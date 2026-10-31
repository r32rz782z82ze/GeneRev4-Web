#!/usr/bin/env python3
"""GeneRev4 REAL: localhost-only browser -> Nico ESP8266 TCP bridge.

No simulated hardware and no TCP commands from the public GitHub Pages page.
NOT a certified safety controller; independent hardware cutoffs required.
"""
from __future__ import annotations

import argparse
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
import secrets
import socket
import threading
import time
from urllib.parse import urlsplit

PORT = 8787
FRESH_SECONDS = 3.0
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}
LOCAL_NETS = tuple(ipaddress.ip_network(n) for n in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"
))


def allowed_host(value: str) -> str:
    """Require an explicit LAN IPv4 address; never accept DNS/public/loopback."""
    try:
        ip = ipaddress.ip_address(value.strip())
    except (ValueError, AttributeError) as exc:
        raise ValueError("Adj meg egy 192.168.x.x / 10.x.x.x / 172.16–31.x.x LAN IP-címet.") from exc
    if ip.version != 4 or not any(ip in net for net in LOCAL_NETS):
        raise ValueError("Csak helyi, privát IPv4-cím használható.")
    return str(ip)


def temperature_line(value: bytes) -> float | None:
    """Read Nico's newline-delimited ASCII numbers. Echoed setpoints are indistinguishable."""
    try:
        line = value.decode("ascii", "strict").strip()
        if not line or len(line) > 15:
            return None
        number = float(line)
        if not 1 <= number <= 250 or not number < float("inf"):
            return None
        return round(number, 1)
    except (UnicodeError, ValueError, OverflowError):
        return None


class Bridge:
    def __init__(self, control_enabled: bool = False):
        self.control_enabled = control_enabled
        self.lock = threading.RLock()
        self.sock: socket.socket | None = None
        self.host = ""
        self.port = 5333
        self.temperature: float | None = None
        self.last_temp_at = 0.0
        self.history = deque(maxlen=150)
        self.notice = "Nincs TCP-kapcsolat. Nem ismert a pörkölő állapota."
        self.command = "nincs"
        self.requested_state = "ismeretlen"
        self.running_requested = False
        self.start_time = 0.0
        self.setpoint = 180
        self.armed_until = 0.0
        self.stale_cool_attempted = False

    def connect(self, host: str, port: int):
        ip = allowed_host(host)
        if not (1 <= port <= 65535):
            raise ValueError("A TCP-port 1–65535 között legyen.")
        with self.lock:
            if self.sock:
                raise ValueError("Már van kapcsolat. Előbb bontsd.")
            connection = socket.create_connection((ip, port), timeout=3)
            connection.settimeout(0.5)
            self.sock = connection
            self.host, self.port = ip, port
            self.temperature, self.last_temp_at = None, 0.0
            self.history.clear()
            self.notice = "TCP csatlakoztatva. Várakozás friss szenzoradatra."
            self.requested_state = "ismeretlen"
            self.running_requested = False
            self.armed_until = 0.0
            self.stale_cool_attempted = False
        threading.Thread(target=self._reader, args=(connection,), daemon=True).start()

    def _reader(self, connection: socket.socket):
        buffer = b""
        try:
            while True:
                with self.lock:
                    if self.sock is not connection:
                        return
                    self._watchdog_locked()
                try:
                    data = connection.recv(1024)
                except socket.timeout:
                    continue
                if not data:
                    raise ConnectionError("A TCP-kapcsolat megszakadt.")
                buffer += data
                if len(buffer) > 4096:
                    buffer = buffer[-1024:]
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    number = temperature_line(line.rstrip(b"\r"))
                    if number is None:
                        continue
                    with self.lock:
                        if self.sock is not connection:
                            return
                        now = time.monotonic()
                        self.temperature = number
                        self.last_temp_at = now
                        self.history.append((round(now, 2), number))
        except (OSError, ConnectionError) as exc:
            with self.lock:
                if self.sock is connection:
                    self._clear_connection_locked(
                        "KAPCSOLATVESZTÉS! A pörkölő állapota ISMERETLEN. "
                        "A gépet fizikailag ellenőrizni kell. " + str(exc)
                    )

    def _fresh_locked(self) -> bool:
        return bool(self.sock and self.temperature is not None
                    and time.monotonic() - self.last_temp_at <= FRESH_SECONDS)

    def _send_locked(self, cmd: str):
        if not self.sock:
            raise ValueError("Nincs TCP-kapcsolat.")
        try:
            self.sock.sendall((cmd + "\r\n").encode("ascii"))
        except OSError as exc:
            self._clear_connection_locked(
                "Sikertelen TCP-küldés. A pörkölő állapota ISMERETLEN; ellenőrizd fizikailag."
            )
            raise ValueError("A TCP-parancs nem küldhető: " + str(exc)) from exc
        self.command = cmd
        self.notice = "Parancs elküldve: " + cmd + ". A hardveres végrehajtás NINCS visszaigazolva."

    def _watchdog_locked(self):
        if not (self.running_requested and self.sock):
            return
        if self._fresh_locked() or self.stale_cool_attempted:
            return
        self.stale_cool_attempted = True
        self.running_requested = False
        self.armed_until = 0
        self.requested_state = "COOL megkísérelve / állapot ismeretlen"
        try:
            self._send_locked("Cool")
            self.notice = ("MEGSZAKADT A FRISS MÉRÉS. COOL parancs megkísérelve, "
                           "de annak végrehajtása NEM igazolt. Fizikai ellenőrzés szükséges!")
        except ValueError:
            pass

    def _clear_connection_locked(self, notice: str):
        old, self.sock = self.sock, None
        self.temperature, self.last_temp_at = None, 0.0
        self.armed_until = 0.0
        self.running_requested = False
        self.requested_state = "ISMERETLEN"
        self.notice = notice
        if old:
            try:
                old.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            old.close()

    def disconnect(self):
        with self.lock:
            if self.running_requested and self.sock:
                try:
                    self._send_locked("Cool")
                except ValueError:
                    pass
            self._clear_connection_locked(
                "TCP leválasztva. A fizikai gép állapota ISMERETLEN, ellenőrizd."
            )

    def arm(self, confirmation: str):
        with self.lock:
            if not self.control_enabled:
                raise ValueError("Csak monitor mód aktív. Indítsd újra a helyi hidat felügyelt vezérléssel.")
            if confirmation != "FELUGYELEM":
                raise ValueError("Írd be pontosan: FELUGYELEM")
            if not self._fresh_locked():
                raise ValueError("Nincs friss mért hőmérséklet. Az indítás tiltva.")
            self.armed_until = time.monotonic() + 120
            self.notice = "Kézi indítás engedélyezve 2 percig. A gép fizikailag ellenőrzendő."

    def command_request(self, action: str, temperature: int | None = None):
        with self.lock:
            if not self.control_enabled:
                raise ValueError("A valódi parancsok monitor módban tiltva vannak.")
            self._watchdog_locked()
            if action == "start":
                if not self._fresh_locked():
                    raise ValueError("Friss szenzoradat nélkül START nem engedélyezett.")
                if time.monotonic() >= self.armed_until:
                    raise ValueError("A START előtt újra élesíteni kell a vezérlést.")
                target = self._validate_target(temperature)
                # Nico's STM32 sets the setpoint to 0 on Start; send target AFTER Start.
                self._send_locked("Start")
                self._send_locked("temp" + str(target) + ";")
                self.setpoint = target
                self.running_requested = True
                self.start_time = time.monotonic()
                self.requested_state = "START kérve, nem visszaigazolt"
                self.armed_until = 0
                self.stale_cool_attempted = False
            elif action == "setpoint":
                if not self.running_requested or not self._fresh_locked():
                    raise ValueError("Új célérték csak aktív, friss méréssel rendelkező indítás után küldhető.")
                target = self._validate_target(temperature)
                self._send_locked("temp" + str(target) + ";")
                self.setpoint = target
            elif action in ("cool", "stop"):
                # Permit shutdown requests even when readings are stale.
                self._send_locked("Cool" if action == "cool" else "Stop")
                self.running_requested = False
                self.requested_state = action.upper() + " kérve; nem visszaigazolt"
                self.armed_until = 0
            else:
                raise ValueError("Ismeretlen parancs.")

    @staticmethod
    def _validate_target(value: int | None) -> int:
        if type(value) is not int or not 150 <= value <= 250:
            raise ValueError("A célhőmérséklet egész szám legyen 150–250 °C között.")
        return value

    def status(self) -> dict:
        with self.lock:
            self._watchdog_locked()
            fresh = self._fresh_locked()
            now = time.monotonic()
            return {
                "connected": bool(self.sock),
                "host": self.host if self.sock else None,
                "port": self.port,
                "fresh": fresh,
                "age": round(now - self.last_temp_at, 1) if self.last_temp_at else None,
                "temperature": self.temperature if fresh else None,
                "controlEnabled": self.control_enabled,
                "armed": fresh and now < self.armed_until,
                "runningRequested": self.running_requested,
                "requestedState": self.requested_state,
                "setpoint": self.setpoint,
                "elapsed": round(now - self.start_time, 1) if self.running_requested else None,
                "lastCommand": self.command,
                "notice": self.notice,
                "history": list(self.history),
            }


class Handler(BaseHTTPRequestHandler):
    server_version = "GeneRev4Local/1.0"

    def _headers(self, code: int, mime: str):
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; script-src 'self'; style-src 'self'; "
                         "connect-src 'self'; img-src 'self'; base-uri 'none'; "
                         "frame-ancestors 'none'; form-action 'none'")
        self.end_headers()

    def _json(self, status: int, payload: dict):
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8")
        self.wfile.write(content)

    def _safe_host(self) -> bool:
        return self.headers.get("Host", "") in (
            "127.0.0.1:" + str(PORT), "localhost:" + str(PORT)
        )

    def do_GET(self):
        if not self._safe_host():
            self._json(403, {"error": "Érvénytelen Host fejléc."})
            return
        path = urlsplit(self.path).path
        if path == "/api/status":
            self._json(200, self.server.bridge.status())
        elif path == "/api/session":
            self._json(200, {"token": self.server.token})
        elif path in ASSETS:
            filename, content_type = ASSETS[path]
            data = (Path(__file__).parent / "static" / filename).read_bytes()
            self._headers(200, content_type)
            self.wfile.write(data)
        else:
            self._json(404, {"error": "Nincs ilyen útvonal."})

    def do_POST(self):
        origin = self.headers.get("Origin", "")
        if (not self._safe_host() or
            origin not in ("http://127.0.0.1:" + str(PORT), "http://localhost:" + str(PORT)) or
            not secrets.compare_digest(self.headers.get("X-GeneRev4-Token", ""), self.server.token) or
            self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json"):
            self._json(403, {"error": "Jogosulatlan vagy idegen eredetű kérés."})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 4096:
                raise ValueError("Érvénytelen kérésméret.")
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError("Hibás kérés.")
            op = urlsplit(self.path).path
            b = self.server.bridge
            if op == "/api/connect":
                port = body.get("port", 5333)
                if type(port) is not int:
                    raise ValueError("Érvénytelen port.")
                b.connect(str(body.get("host", "")), port)
            elif op == "/api/disconnect":
                b.disconnect()
            elif op == "/api/arm":
                b.arm(body.get("confirmation", ""))
            elif op == "/api/command":
                b.command_request(body.get("action", ""), body.get("temperature"))
            else:
                raise ValueError("Ismeretlen művelet.")
            self._json(200, b.status())
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})

    def log_message(self, fmt, *args):
        # Local-only, avoid displaying raw tokens, requests or private addresses.
        if not str(args[1] if len(args) > 1 else "").startswith("2"):
            super().log_message(fmt, *args)


def main():
    parser = argparse.ArgumentParser(description="GeneRev4 REAL helyi híd, Python 3.")
    parser.add_argument("--enable-control", action="store_true",
                        help="Kézi START / STOP / COOL parancsok helyi engedélyezése")
    args = parser.parse_args()
    bridge = Bridge(control_enabled=args.enable_control)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    server.bridge = bridge
    server.token = secrets.token_urlsafe(32)
    print("GeneRev4 REAL: http://127.0.0.1:%d/" % PORT, flush=True)
    print("MÓD: %s" % ("FELÜGYELT PARANCSOK" if args.enable_control else "CSAK MONITOR"), flush=True)
    print("Csak ezen a laptopon érhető el. A GitHub Pages nem vezérli a pörkölőt.", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nLeállítás. A hardver állapotát ellenőrizd!", flush=True)
    finally:
        bridge.disconnect()
        server.server_close()


if __name__ == "__main__":
    main()
