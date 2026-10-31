"""Nico GeneRev4 idő-hőmérséklet profillal kompatibilis helyi tervező.

Nem küld a pörkölőnek semmit: a profil-előnézet csak a Windows UI-ban fut.
"""
from __future__ import annotations

import math
import re
from typing import NamedTuple


class ProfilePoint(NamedTuple):
    second: int
    temperature: float


def parse_profile(content: str) -> list[ProfilePoint]:
    data = content.lstrip("\ufeff")
    lines = [line.strip() for line in data.splitlines()
             if line.strip() and not line.strip().startswith("#")]
    if not lines:
        raise ValueError("A profilfájl üres.")

    points: list[ProfilePoint] = []
    if any(re.match(r"^\[[tT]\d+\s*=", line) for line in lines):
        times: dict[int, float] = {}
        temps: dict[int, float] = {}
        for kind, number, value in re.findall(
            r"\[([tT])(\d+)\s*=\s*([+-]?\d+(?:[.,]\d+)?)\s*\]", data
        ):
            key, parsed = int(number), float(value.replace(",", "."))
            (times if kind == "t" else temps)[key] = parsed
        if not times or set(times) != set(temps):
            raise ValueError("TXT: minden [tN=...] párhoz kell [TN=...]!")
        points = [ProfilePoint(times[n], temps[n]) for n in sorted(times)]
    else:
        for line in lines:
            if re.match(r"^999\s*;", line):
                continue
            cells = line.split(";")
            if len(cells) < 2:
                raise ValueError("Hibás CSV sor: " + line[:100])
            try:
                points.append(ProfilePoint(
                    float(cells[0].strip()),
                    float(cells[1].strip().replace(",", "."))
                ))
            except ValueError as exc:
                raise ValueError("Nem számértékű CSV sor: " + line[:100]) from exc
    if not 1 <= len(points) <= 2000:
        raise ValueError("A profil 1–2000 időpontot tartalmazhat.")
    last = -1
    for p in points:
        if not (math.isfinite(p.second) and
                p.second == int(p.second) and 0 <= p.second <= 21600 and
                p.second > last):
            raise ValueError("A profilidőnek növekvő egész másodpercnek kell lennie (0–21600).")
        if not math.isfinite(p.temperature) or not 150 <= p.temperature <= 250:
            raise ValueError("A célhőmérséklet 150 és 250 °C között legyen.")
        last = p.second
    return [ProfilePoint(int(p.second), p.temperature) for p in points]


def target_at(points: list[ProfilePoint], second: float) -> float | None:
    current = None
    for p in points:
        if second < p.second:
            break
        current = p.temperature
    return current


def export_csv(points: list[ProfilePoint]) -> str:
    return "999;GeneRev4\r\n" + "".join(
        f"{p.second};{p.temperature:.1f}\r\n" for p in points
    )


def export_txt(points: list[ProfilePoint]) -> str:
    return "".join(
        f"[t{i}={p.second}]\n[T{i}={p.temperature:.1f}]\n"
        for i, p in enumerate(points, start=1)
    )


EXAMPLE = [
    ProfilePoint(0, 180), ProfilePoint(60, 190),
    ProfilePoint(120, 205), ProfilePoint(180, 220),
    ProfilePoint(240, 230), ProfilePoint(300, 225),
    ProfilePoint(360, 210)
]


def mmss(second: float) -> str:
    s = max(0, int(second))
    return f"{s // 60:02d}:{s % 60:02d}"
