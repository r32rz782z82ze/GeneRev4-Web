#!/usr/bin/env python3
"""GeneRev4 Windows Desktop – Nico-compatible local TCP control.

Based on the already reviewed real/bridge.py, without public web exposure.
The program is NOT a tested hardware safety controller.
"""
from __future__ import annotations

import csv
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from pathlib import Path

from bridge import Bridge
from gene_profile import EXAMPLE, export_csv, export_txt, mmss, parse_profile, target_at

BG = "#4b291c"
PANEL = "#352017"
PANEL2 = "#412719"
TEXT = "#fff3e7"
MUTED = "#d7b49c"
ACCENT = "#efb47f"
BAD = "#ff8d83"
GOOD = "#b8e7b3"
INK = "#3c2013"

def safe_self_test():
    """Exercise bundled imports and data model without requiring a GUI or roaster."""
    import socket
    pts = parse_profile("999;header\n0;180\n60;200\n")
    assert target_at(pts, 70) == 200
    assert len(parse_profile(export_txt(pts))) == 2
    assert len(parse_profile(export_csv(pts))) == 2
    left, right = socket.socketpair()
    try:
        left.settimeout(0.25)
        right.settimeout(0.25)
        controller = Bridge(control_enabled=False)
        controller.sock = left
        controller.temperature = 25
        controller.last_temp_at = time.monotonic()
        assert controller.status()["fresh"]
        try:
            controller.command_request("start", 180)
            raise AssertionError("Monitor-only mode must refuse START")
        except ValueError:
            pass
        controller.disconnect()
    finally:
        left.close()
        right.close()


class GeneRev4Desktop:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.bridge = Bridge(control_enabled=False)
        self.results = queue.Queue()
        self.busy = False
        self.closed = False
        self.control_selected = tk.BooleanVar(value=False)
        self.host_value = tk.StringVar(value="")
        self.port_value = tk.StringVar(value="5333")
        self.setpoint_value = tk.IntVar(value=180)
        self.profile_points = []
        self.profile_name = "Nincs profil"
        self.profile_second = 0.0
        self.profile_playing = False
        self.profile_tick = time.monotonic()
        self.profile_duration = 0.0
        self.last_chart_signature = None

        self.root.title("GeneRev4 REAL – Windows")
        self.root.geometry("1080x850")
        self.root.minsize(790, 630)
        self.root.configure(bg=BG)
        self._configure_ttk()
        self._create_ui()
        self._log("GeneRev4 REAL Windows elindult – alapértelmezett mód: CSAK MONITOR.")
        self._log("Nincsenek szimulált szenzoradatok és nincs automatikus START.")
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(300, self._poll)

    def _configure_ttk(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL2, foreground=TEXT,
                        padding=(22, 10), font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#8a5635")])
        style.configure("Gene.TEntry", fieldbackground="#25170f",
                        foreground=TEXT, insertcolor=TEXT, padding=8)
        style.configure("Gene.TCombobox", fieldbackground="#25170f",
                        foreground=TEXT)
        style.configure("Gene.Horizontal.TScale", background=PANEL)
        style.configure("Gene.Treeview", background=PANEL2, foreground=TEXT,
                        fieldbackground=PANEL2, rowheight=28, borderwidth=0)
        style.configure("Gene.Treeview.Heading", background="#6b422d",
                        foreground=TEXT, font=("Segoe UI", 9, "bold"))
        style.map("Gene.Treeview", background=[("selected", "#966340")])

    def _label(self, parent, text, *, size=11, color=TEXT, bold=False, **kwargs):
        return tk.Label(parent, text=text, fg=color, bg=parent.cget("bg"),
                        font=("Segoe UI", size, "bold" if bold else "normal"),
                        **kwargs)

    def _button(self, parent, text, command, *, accent=False, width=None):
        return tk.Button(parent, text=text, command=command, relief="flat",
                         activebackground="#ffd4a6" if accent else "#92603f",
                         bg=ACCENT if accent else "#79503a",
                         fg=INK if accent else TEXT,
                         activeforeground=INK if accent else TEXT,
                         disabledforeground="#9c8171", padx=13, pady=8, width=width,
                         font=("Segoe UI", 10, "bold"),
                         cursor="hand2", borderwidth=0)

    def _panel(self, parent):
        frame = tk.Frame(parent, bg=PANEL, padx=16, pady=13, highlightbackground="#70432b",
                         highlightthickness=1)
        frame.pack(fill="x", padx=16, pady=(0, 12))
        return frame

    def _create_ui(self):
        header = tk.Frame(self.root, bg="#3a2017", padx=18, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="◈ GeneRev4 REAL", bg=header["bg"], fg=TEXT,
                 font=("Segoe UI", 19, "bold")).pack(side="left")
        tk.Label(header, text="  WINDOWS  ·  NICO STM32 / ESP8266",
                 bg=header["bg"], fg=MUTED, font=("Segoe UI", 10)).pack(side="left")
        tk.Label(header, text="HELYI ALKALMAZÁS", bg="#704329", fg="#ffe0b3",
                 padx=13, pady=7, font=("Segoe UI", 9, "bold")).pack(side="right")

        alert = tk.Frame(self.root, bg="#633227", padx=17, pady=8)
        alert.pack(fill="x")
        tk.Label(alert, bg=alert["bg"], fg="#ffe1d3",
                 text="⚠ FŰTŐBERENDEZÉS: a TCP-parancs nem hardveres visszaigazolás. "
                      "Független hővédelem és fizikai vészleállító kötelező.",
                 font=("Segoe UI", 10, "bold"), anchor="w",
                 wraplength=1000, justify="left").pack(fill="x")

        tabs = ttk.Notebook(self.root)
        tabs.pack(fill="both", expand=True, padx=7, pady=7)
        self.live_tab = tk.Frame(tabs, bg=BG)
        self.profile_tab = tk.Frame(tabs, bg=BG)
        self.log_tab = tk.Frame(tabs, bg=BG)
        tabs.add(self.live_tab, text="   ÉLŐ PÖRKÖLŐ   ")
        tabs.add(self.profile_tab, text="   PROFILOK – ELŐNÉZET   ")
        tabs.add(self.log_tab, text="   NAPLÓ ÉS BIZTONSÁG   ")
        self._live_ui()
        self._profile_ui()
        self._log_ui()

    def _scrollable(self, parent):
        canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inside = tk.Frame(canvas, bg=BG)
        winid = canvas.create_window((0, 0), window=inside, anchor="nw")
        inside.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(winid, width=e.width))
        # Bind the wheel only while the mouse is over this page.
        def on_scroll(e):
            canvas.yview_scroll(int(-e.delta / 120), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_scroll))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        return inside

    def _live_ui(self):
        body = self._scrollable(self.live_tab)
        connect = self._panel(body)
        self._label(connect, "TCP-CSATLAKOZÁS", size=10, color=MUTED, bold=True).pack(anchor="w")
        row = tk.Frame(connect, bg=PANEL)
        row.pack(fill="x", pady=(9, 4))
        self._label(row, "GeneRev4 ESP8266 IP:", color=MUTED).pack(side="left")
        ttk.Entry(row, textvariable=self.host_value, width=20,
                  style="Gene.TEntry").pack(side="left", padx=9)
        self._label(row, "Port:", color=MUTED).pack(side="left")
        ttk.Entry(row, textvariable=self.port_value, width=8,
                  style="Gene.TEntry").pack(side="left", padx=9)
        self.connect_btn = self._button(row, "Csatlakozás", self._connect, accent=True)
        self.connect_btn.pack(side="left", padx=(5, 7))
        self.disconnect_btn = self._button(row, "Bontás", self._disconnect)
        self.disconnect_btn.pack(side="left")
        self.connection_label = self._label(connect, "NINCS KAPCSOLAT",
                                            color=BAD, bold=True)
        self.connection_label.pack(anchor="w", pady=(9, 0))
        self._label(connect, "A laptopnak és a vezérlőnek ugyanazon a Wi-Fi-hálózaton kell lennie. "
                    "Az IP nem a laptop vagy telefon címe.", size=9,
                    color=MUTED, wraplength=910, justify="left").pack(anchor="w", pady=(4, 0))

        cards = tk.Frame(body, bg=BG)
        cards.pack(fill="x", padx=16, pady=(0, 12))
        for idx in (0, 1, 2):
            cards.columnconfigure(idx, weight=1)
        self.metrics = {}
        for index, (key, title, default) in enumerate([
            ("temperature", "MÉRT HŐMÉRSÉKLET", "— °C"),
            ("elapsed", "HELYI IDŐ", "—"),
            ("target", "KÉRT CÉLÉRTÉK", "180 °C")
        ]):
            cell = tk.Frame(cards, bg=PANEL, padx=17, pady=11,
                            highlightbackground="#70432b", highlightthickness=1)
            cell.grid(row=0, column=index, sticky="nsew",
                      padx=(0, 7) if index < 2 else 0)
            self._label(cell, title, color=MUTED, size=9, bold=True).pack(anchor="w")
            value = self._label(cell, default, size=27, bold=True)
            value.pack(anchor="w", pady=5)
            self.metrics[key] = value

        chart_panel = self._panel(body)
        self._label(chart_panel, "VALÓDIAN FOGADOTT HŐMÉRSÉKLETI SZÁMÉRTÉKEK",
                    color=MUTED, size=10, bold=True).pack(anchor="w")
        self.real_chart = tk.Canvas(chart_panel, bg="#26170f", height=160,
                                    highlightthickness=0)
        self.real_chart.pack(fill="x", pady=9)
        self.fresh_label = self._label(chart_panel,
                "Nincs mérés. A visszaérkező szám önmagában nem garantál hőelem-eredetet.",
                color=MUTED, size=9)
        self.fresh_label.pack(anchor="w")
        self.export_measure_btn = self._button(chart_panel,
                "Mért adatok CSV mentése", self._export_measurements)
        self.export_measure_btn.pack(anchor="w", pady=(10, 0))

        state_panel = self._panel(body)
        self._label(state_panel, "KÉRT ÁLLAPOT (NEM HARDVERES VISSZAIGAZOLÁS)",
                    color=MUTED, size=10, bold=True).pack(anchor="w")
        self.requested_label = self._label(state_panel, "ISMERETLEN", bold=True, size=17)
        self.requested_label.pack(anchor="w", pady=5)
        self.notice_label = self._label(state_panel,
            "Nincs TCP-kapcsolat. A pörkölő fizikai állapota nem ismert.",
            color="#ffd49e", wraplength=900, justify="left")
        self.notice_label.pack(anchor="w")

        control = self._panel(body)
        self._label(control, "FELÜGYELT MANUÁLIS PARANCSOK",
                    color=MUTED, size=10, bold=True).pack(anchor="w")
        check = tk.Checkbutton(
            control, text="Valódi parancsküldés engedélyezése (alapból tiltva)",
            variable=self.control_selected, command=self._toggle_control,
            bg=PANEL, fg=TEXT, selectcolor="#61402b", activebackground=PANEL,
            activeforeground=TEXT, font=("Segoe UI", 10, "bold")
        )
        check.pack(anchor="w", pady=(7, 4))
        self.arm_button = self._button(control, "START élesítése 2 percre", self._arm)
        self.arm_button.pack(anchor="w", pady=4)
        buttons = tk.Frame(control, bg=PANEL)
        buttons.pack(fill="x", pady=(8, 7))
        self.start_button = self._button(buttons, "🔥 START", self._start, accent=True)
        self.start_button.pack(side="left", padx=(0, 8))
        self.cool_button = self._button(buttons, "❄ COOL", self._cool)
        self.cool_button.pack(side="left", padx=(0, 8))
        self.stop_button = self._button(buttons, "■ STOP", self._stop)
        self.stop_button.pack(side="left")
        setrow = tk.Frame(control, bg=PANEL)
        setrow.pack(fill="x", pady=(8, 4))
        self._label(setrow, "Kért célhőmérséklet:", bold=True).pack(side="left")
        self.setpoint_display = self._label(setrow, "180 °C", size=17, bold=True)
        self.setpoint_display.pack(side="right")
        tk.Scale(control, from_=150, to=250, orient="horizontal",
                 variable=self.setpoint_value, command=self._setpoint_preview,
                 resolution=1, showvalue=False, bg=PANEL,
                 troughcolor="#70452f", fg=TEXT,
                 activebackground=ACCENT, highlightthickness=0).pack(fill="x")
        self.setpoint_button = self._button(control, "Új célérték küldése", self._setpoint)
        self.setpoint_button.pack(anchor="w", pady=5)
        self._label(control,
            "A START és az új célérték csak friss mérési adatnál engedélyezett. "
            "A STOP nem vészleállító. Kapcsolatvesztésnél a fűtés nem garantáltan áll le.",
            color="#ffd18d", wraplength=900, justify="left", size=10).pack(anchor="w", pady=7)

    def _profile_ui(self):
        bar = self._panel(self.profile_tab)
        self._label(bar, "NICO CSV/TXT PROFIL – CSAK ELŐNÉZET",
                    color=MUTED, size=10, bold=True).pack(anchor="w")
        self._label(bar, "A profil lejátszása SOHA nem küld START, hőfok vagy COOL parancsot.",
                    color="#ffcf8d", bold=True).pack(anchor="w", pady=(4, 10))
        actions = tk.Frame(bar, bg=PANEL)
        actions.pack(fill="x")
        for label, fn in [
            ("Fájl betöltése", self._load_profile),
            ("Mintaprofil", self._example_profile),
            ("CSV export", lambda: self._save_profile("csv")),
            ("TXT export", lambda: self._save_profile("txt"))
        ]:
            self._button(actions, label, fn).pack(side="left", padx=(0, 8))
        self.profile_name_label = self._label(bar, self.profile_name, color=MUTED)
        self.profile_name_label.pack(anchor="w", pady=(12, 0))
        progress = tk.Frame(bar, bg=PANEL)
        progress.pack(fill="x", pady=(10, 4))
        self.profile_time_label = self._label(progress, "00:00 / 00:00",
                                               bold=True, size=14)
        self.profile_time_label.pack(side="left")
        self.profile_target_label = self._label(progress, "Tervezett cél: — °C",
                                                 color=ACCENT, bold=True, size=12)
        self.profile_target_label.pack(side="right")
        self.profile_scale = tk.Scale(
            bar, from_=0, to=1, orient="horizontal", resolution=1,
            showvalue=False, command=self._seek_profile, bg=PANEL,
            troughcolor="#70452f", highlightthickness=0
        )
        self.profile_scale.pack(fill="x")
        controls = tk.Frame(bar, bg=PANEL)
        controls.pack(fill="x")
        self._button(controls, "▶ Előnézet indítása", self._play_profile,
                     accent=True).pack(side="left", padx=(0, 8))
        self._button(controls, "Ⅱ Szünet", self._pause_profile).pack(side="left", padx=(0, 8))
        self._button(controls, "↺ Elejére", self._reset_profile).pack(side="left")
        self.profile_chart = tk.Canvas(bar, height=185, bg="#26170f",
                                       highlightthickness=0)
        self.profile_chart.pack(fill="x", pady=(15, 5))

        bottom = self._panel(self.profile_tab)
        self._label(bottom, "BETÖLTÖTT PROFILPONTOK", color=MUTED,
                    size=10, bold=True).pack(anchor="w")
        columns = ("time", "second", "target")
        self.tree = ttk.Treeview(bottom, columns=columns, show="headings",
                                 style="Gene.Treeview", height=9)
        for key, heading, width in [
            ("time", "Idő", 160), ("second", "Másodperc", 160),
            ("target", "Tervezett cél (°C)", 230)
        ]:
            self.tree.heading(key, text=heading)
            self.tree.column(key, width=width, stretch=True)
        scroll = ttk.Scrollbar(bottom, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, pady=(10, 0))
        self._draw_graph(self.profile_chart, [], preview=True)

    def _log_ui(self):
        panel = self._panel(self.log_tab)
        self._label(panel, "HELYI ESEMÉNYNAPLÓ", color=MUTED, size=10,
                    bold=True).pack(anchor="w")
        self._label(panel, "Csak az alkalmazás eseményeit mutatja; a TCP-parancs nem "
                    "jelenti a hardveres végrehajtás visszaigazolását.",
                    color=MUTED, wraplength=940, justify="left").pack(anchor="w", pady=8)
        self.log_view = tk.Text(panel, bg="#24160f", fg="#fce9d9",
                        font=("Consolas", 10), wrap="word", relief="flat",
                        height=24, padx=10, pady=10)
        self.log_view.pack(fill="both", expand=True)
        self.log_view.configure(state="disabled")
        self._label(panel, "Nico eredeti projektje: github.com/nekowokaburu/GeneCBR101Automation\n"
                    "A teljes ESP8266 firmware nincs közzétéve. Független hővédelem szükséges.",
                    color=MUTED, wraplength=940, justify="left").pack(anchor="w", pady=7)

    def _log(self, event):
        line = time.strftime("%H:%M:%S") + "  " + str(event) + "\n"
        if not hasattr(self, "log_view"):
            return
        self.log_view.configure(state="normal")
        self.log_view.insert("end", line)
        self.log_view.see("end")
        self.log_view.configure(state="disabled")

    def _task(self, description, task):
        if self.busy or self.closed:
            return
        self.busy = True
        self._log(description + " ...")
        def work():
            try:
                task()
                self.results.put((description, None))
            except Exception as exc:
                self.results.put((description, str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def _connect(self):
        host = self.host_value.get().strip()
        try:
            port = int(self.port_value.get().strip())
        except ValueError:
            messagebox.showerror("GeneRev4", "A TCP-port egész szám legyen.")
            return
        self._task("TCP csatlakozás a megadott ESP8266-hoz",
                   lambda: self.bridge.connect(host, port))

    def _disconnect(self):
        self._task("TCP kapcsolat bontása, szükség esetén COOL-kísérlet",
                   self.bridge.disconnect)

    def _toggle_control(self):
        if self.control_selected.get():
            if not messagebox.askyesno("Fűtésvezérlés figyelmeztetés",
                    "VALÓDI HARDVERPARANCSOKAT engedélyeznél.\n\n"
                    "A program nincs fizikai pörkölőn tesztelve. "
                    "A kapcsolat elvesztésekor a fűtés NEM garantáltan áll le.\n\n"
                    "Van független hővédelem, fizikai vészleállítás és folyamatos felügyelet?"):
                self.control_selected.set(False)
                return
            confirm = simpledialog.askstring("Külön megerősítés",
                "Írd be pontosan FELUGYELEM:", parent=self.root)
            if confirm != "FELUGYELEM":
                self.control_selected.set(False)
                return
            with self.bridge.lock:
                self.bridge.control_enabled = True
            self._log("Felügyelt manuális parancsküldés helyileg engedélyezve.")
        else:
            if self.bridge.status()["runningRequested"]:
                messagebox.showwarning("Fűtés állapota ismeretlen",
                    "A parancsküldés tiltása NEM állítja le a pörkölőt. "
                    "Előbb fizikailag ellenőrizd a gépet, és szükség esetén COOL.")
                self.control_selected.set(True)
                return
            with self.bridge.lock:
                self.bridge.control_enabled = False
                self.bridge.armed_until = 0
            self._log("Visszaváltás MONITOR módra.")

    def _arm(self):
        try:
            self.bridge.arm("FELUGYELEM")
            self._log("START külön élesítése, két percre.")
        except ValueError as exc:
            messagebox.showerror("Élesítés sikertelen", str(exc))

    def _start(self):
        if not messagebox.askyesno("VALÓDI START parancs",
            "Valódi fűtésindítási kérést küldenél.\n"
            "Ezt nem lehet biztonságosan ellenőrizni az appból.\n"
            "Biztosan folytatod?"):
            return
        target = self.setpoint_value.get()
        self._task("START + temp" + str(target) + "; elküldése",
                   lambda: self.bridge.command_request("start", target))

    def _cool(self):
        if messagebox.askyesno("COOL kérés",
            "Valódi COOL TCP-parancsot küldesz. "
            "A hardveres végrehajtás nem igazolt. Folytatod?"):
            self._task("COOL kérés", lambda: self.bridge.command_request("cool"))

    def _stop(self):
        if messagebox.askyesno("STOP kérés – NEM vészleállító",
            "A STOP a dobot visszaállíthatja. Nem fizikai vészleállító.\n"
            "Valóban elküldöd a STOP parancsot?"):
            self._task("STOP kérés", lambda: self.bridge.command_request("stop"))

    def _setpoint_preview(self, _value):
        if hasattr(self, "setpoint_display"):
            self.setpoint_display.configure(text=str(self.setpoint_value.get())+" °C")

    def _setpoint(self):
        target = self.setpoint_value.get()
        if messagebox.askyesno("Célhőmérséklet változtatása",
                f"Elküldöd a valódi pörkölőnek a {target} °C célértéket?"):
            self._task("Célhőmérséklet küldése: "+str(target)+" °C",
                       lambda: self.bridge.command_request("setpoint", target))

    def _export_measurements(self):
        data = self.bridge.status().get("history", [])
        if not data:
            messagebox.showinfo("GeneRev4", "Még nincs valódi fogadott adat.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile="GeneRev4_meresek.csv",
            filetypes=[("CSV", "*.csv")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow(["eltelt_masodperc", "fogadott_ertek_C"])
            origin = data[0][0]
            for second, number in data:
                writer.writerow([round(second-origin,2), number])
        self._log("Fogadott hőmérsékleti számok exportálva.")

    def _load_profile(self):
        path = filedialog.askopenfilename(filetypes=[
            ("GeneRev4 profilok", "*.csv *.txt"), ("Minden fájl", "*.*")
        ])
        if not path:
            return
        try:
            if os.path.getsize(path) > 1024 * 1024:
                raise ValueError("A profilfájl legfeljebb 1 MB lehet.")
            content = Path(path).read_text(encoding="utf-8-sig")
            points = parse_profile(content)
            self._set_profile(points, Path(path).name)
        except (OSError, UnicodeError, ValueError) as exc:
            messagebox.showerror("Profilbeolvasás", str(exc))

    def _example_profile(self):
        self._set_profile(list(EXAMPLE), "MINTAPROFIL – CSAK ELŐNÉZET")

    def _set_profile(self, points, name):
        self.profile_points = points
        self.profile_name = name
        self.profile_second = 0
        self.profile_playing = False
        self.profile_duration = points[-1].second
        self.profile_scale.configure(to=max(1, self.profile_duration))
        for row in self.tree.get_children():
            self.tree.delete(row)
        for point in points:
            self.tree.insert("", "end", values=(mmss(point.second),
                              point.second, f"{point.temperature:.1f}"))
        self.profile_name_label.configure(text=f"{name} · {len(points)} profilpont")
        self._update_profile()
        self._log("Profil betöltve: "+name+" (hardveres parancsküldés NINCS).")

    def _seek_profile(self, value):
        if not hasattr(self, "profile_target_label"):
            return
        self.profile_second=float(value)
        self.profile_tick = time.monotonic()
        self._update_profile(seek=False)

    def _update_profile(self, seek=True):
        if seek:
            self.profile_scale.set(self.profile_second)
        self.profile_time_label.configure(
            text=mmss(self.profile_second)+" / "+mmss(self.profile_duration))
        target=target_at(self.profile_points, self.profile_second)
        self.profile_target_label.configure(
            text="Tervezett cél: "+(f"{target:.1f} °C" if target is not None else "— °C"))
        self._draw_graph(self.profile_chart, self.profile_points,
                         preview=True, marker=self.profile_second)

    def _play_profile(self):
        if not self.profile_points:
            messagebox.showinfo("GeneRev4", "Először tölts be profilt.")
            return
        if self.profile_second >= self.profile_duration:
            self.profile_second=0
        self.profile_playing=True
        self.profile_tick=time.monotonic()

    def _pause_profile(self):
        self.profile_playing=False

    def _reset_profile(self):
        self.profile_playing=False
        self.profile_second=0
        self._update_profile()

    def _save_profile(self, extension):
        if not self.profile_points:
            messagebox.showinfo("GeneRev4", "Nincs betöltött profil.")
            return
        path = filedialog.asksaveasfilename(defaultextension="."+extension,
             initialfile="GeneRev4_profil."+extension,
             filetypes=[(extension.upper(), "*."+extension)])
        if path:
            data=export_csv(self.profile_points) if extension=="csv" else export_txt(self.profile_points)
            Path(path).write_text(data, encoding="utf-8-sig")
            self._log("Profil exportálva: "+str(path))

    def _draw_graph(self, canvas, points, *, preview=False, marker=None):
        width = max(250, canvas.winfo_width())
        height = max(120, canvas.winfo_height())
        canvas.delete("all")
        left, right, top, bottom = 50, width-16, 14, height-27
        def xy_time(t):
            span = max(60, points[-1].second if preview and points else
                       (points[-1][0]-points[0][0] if points else 60))
            base = 0 if preview or not points else points[0][0]
            return left + max(0, min(1,(t-base)/span))*(right-left)
        def xy_temp(temp):
            return bottom - max(0, min(1,(temp-0)/260))*(bottom-top)
        for t in (50,100,150,200,250):
            y=xy_temp(t)
            canvas.create_line(left,y,right,y,fill="#624332",dash=(4,4))
            canvas.create_text(left-5,y,text=f"{t}°",fill=MUTED,anchor="e",
                               font=("Segoe UI",8))
        if not points:
            canvas.create_text(width/2,height/2,text="Nincs valódi fogadott adat" if not preview
                               else "Tölts be egy profilt", fill=MUTED,
                               font=("Segoe UI",12))
            return
        coordinates = []
        for point in points:
            t, temp = (point.second, point.temperature) if preview else (point[0],point[1])
            coordinates.extend([xy_time(t),xy_temp(temp)])
        if len(coordinates)>=4:
            canvas.create_line(*coordinates,fill=ACCENT,width=3,smooth=False)
        else:
            canvas.create_oval(coordinates[0]-3, coordinates[1]-3,
                               coordinates[0]+3, coordinates[1]+3,fill=ACCENT)
        if marker is not None:
            x=xy_time(marker)
            canvas.create_line(x,top,x,bottom,fill="#ffe0a1",dash=(5,4),width=2)

    def _poll(self):
        if self.closed:
            return
        while True:
            try:
                description, error = self.results.get_nowait()
            except queue.Empty:
                break
            self.busy = False
            if error:
                self._log("HIBA: "+description+" – "+error)
                messagebox.showerror("GeneRev4", error)
            else:
                self._log(description+" – parancs esetén nincs hardveres visszaigazolás.")

        try:
            s=self.bridge.status()
            connected=bool(s["connected"])
            fresh=bool(s["fresh"])
            active=bool(s["controlEnabled"])
            self.connection_label.configure(
                text="TCP KAPCSOLAT · FRISS SZÁMÉRTÉK" if fresh else
                     ("TCP KAPCSOLAT · NINCS FRISS MÉRÉS" if connected else "NINCS KAPCSOLAT"),
                fg=GOOD if fresh else BAD)
            self.metrics["temperature"].configure(
                text=f'{s["temperature"]:.1f} °C' if fresh else "— °C")
            self.metrics["elapsed"].configure(text=mmss(s["elapsed"]) if s["elapsed"] is not None else "—")
            self.metrics["target"].configure(text=str(s["setpoint"])+" °C")
            self.requested_label.configure(text=s["requestedState"])
            self.notice_label.configure(text=s["notice"])
            self.fresh_label.configure(
                text=("Utolsó fogadott szám: "+str(s["age"])+" másodperce"
                      if fresh else "Nincs friss fogadott szám. A hőelem eredete nem igazolt."))
            self.connect_btn.configure(state="disabled" if connected or self.busy else "normal")
            self.disconnect_btn.configure(state="normal" if connected and not self.busy else "disabled")
            self.arm_button.configure(state="normal" if active and fresh and not self.busy else "disabled")
            self.start_button.configure(state="normal" if active and fresh and s["armed"]
                                   and not s["runningRequested"] and not self.busy else "disabled")
            self.cool_button.configure(state="normal" if active and connected and not self.busy else "disabled")
            self.stop_button.configure(state="normal" if active and connected and not self.busy else "disabled")
            self.setpoint_button.configure(state="normal" if active and fresh and s["runningRequested"]
                                           and not self.busy else "disabled")
            self.export_measure_btn.configure(
                state="normal" if s["history"] else "disabled")
            signature=(len(s["history"]),
                s["history"][-1] if s["history"] else None,
                self.real_chart.winfo_width())
            if signature != self.last_chart_signature:
                self.last_chart_signature=signature
                self._draw_graph(self.real_chart, s["history"])
        except Exception as exc:
            self._log("Helyi felületfrissítési hiba: "+str(exc))

        if self.profile_playing and self.profile_points:
            now=time.monotonic()
            self.profile_second+=(now-self.profile_tick)
            self.profile_tick=now
            if self.profile_second>=self.profile_duration:
                self.profile_second=self.profile_duration
                self.profile_playing=False
                self._log("Profil ELŐNÉZETE befejeződött; COOL parancs NEM ment ki.")
            self._update_profile()
        self.root.after(500,self._poll)

    def _close(self):
        if self.closed:
            return
        s=self.bridge.status()
        if s["runningRequested"]:
            if not messagebox.askyesno("Fizikai pörkölő ellenőrzése szükséges",
                   "Az alkalmazásból START kérés ment ki. "
                   "Az ablak bezárása NEM garantálja a fűtés leállítását. "
                   "A program COOL-t próbál küldeni.\n\n"
                   "A fizikai pörkölőt ellenőrzöd és továbbra is felügyeled?"):
                return
        self.closed=True
        try:
            self.bridge.disconnect()
        except Exception as exc:
            messagebox.showwarning("TCP lezárás", str(exc))
        self.root.destroy()


def main():
    if "--self-test" in sys.argv:
        safe_self_test()
        return
    root=tk.Tk()
    GeneRev4Desktop(root)
    root.mainloop()


if __name__=="__main__":
    main()
