import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import socket
import time
import unittest
from bridge import Bridge, allowed_host, temperature_line


class ProtocolTests(unittest.TestCase):
    def test_lan_addresses_only(self):
        for value in ("192.168.0.30", "10.1.2.3", "172.16.1.1", "172.31.255.254"):
            self.assertEqual(value, allowed_host(value))
        for value in ("127.0.0.1", "8.8.8.8", "localhost", "169.254.1.1",
                      "172.32.1.1", "0.0.0.0", "::1", "192.168.0.1.example.com"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                allowed_host(value)

    def test_telemetry(self):
        for raw, want in ((b"25\r", 25.0), (b"204.5", 204.5), (b"0", None),
                          (b"255", None), (b"NaN", None), (b"abc", None),
                          (b"251", None), (b"", None)):
            with self.subTest(raw=raw):
                self.assertEqual(temperature_line(raw), want)

    def test_monitor_mode_rejects_commands(self):
        a = Bridge()
        with self.assertRaisesRegex(ValueError, "monitor"):
            a.command_request("start", 180)
        with self.assertRaises(ValueError):
            a.arm("FELUGYELEM")

    def test_hardware_commands_are_exact_crlf_and_start_sets_temp_after_start(self):
        app, roaster = socket.socketpair()
        try:
            app.settimeout(0.2)
            roaster.settimeout(0.2)
            b=Bridge(control_enabled=True)
            b.sock=app
            b.temperature=25.0
            b.last_temp_at=time.monotonic()
            b.arm("FELUGYELEM")
            b.command_request("start",180)
            self.assertEqual(roaster.recv(80),b"Start\r\ntemp180;\r\n")
            self.assertTrue(b.running_requested)
            b.command_request("setpoint",210)
            self.assertEqual(roaster.recv(80),b"temp210;\r\n")
            b.command_request("cool")
            self.assertEqual(roaster.recv(80),b"Cool\r\n")
            self.assertFalse(b.running_requested)
            b.command_request("stop")
            self.assertEqual(roaster.recv(80),b"Stop\r\n")
            b.disconnect()
        finally:
            app.close()
            roaster.close()

    def test_stale_sensor_forces_cool_attempt_not_confirmed_shutdown(self):
        app, roaster = socket.socketpair()
        try:
            roaster.settimeout(0.2)
            b=Bridge(control_enabled=True)
            b.sock=app
            b.last_temp_at=time.monotonic()-20
            b.temperature=200
            b.running_requested=True
            b._watchdog_locked()
            self.assertEqual(roaster.recv(80),b"Cool\r\n")
            self.assertFalse(b.running_requested)
            self.assertIn("NEM igazolt",b.notice)
            self.assertFalse(b.status()["fresh"])
            b.disconnect()
        finally:
            app.close()
            roaster.close()

    def test_target_validation(self):
        for target in (0,149,251,180.1,True,"180",None):
            with self.subTest(target=target),self.assertRaises(ValueError):
                Bridge._validate_target(target)
        self.assertEqual(Bridge._validate_target(220),220)


if __name__=="__main__":
    unittest.main()
