# GeneRev4 REAL – önálló Windows alkalmazás

Ez **valódi Windows .exe alkalmazás**, saját ablakkal (Tkinter). A Nico-féle GeneRev4 TCP-parancsait a korábban szoftvertesztelt real/bridge.py vezérlőn keresztül használja. **Nem kell telepíteni a Pythont a futtatásához**: az EXE PyInstallerrel készül.

## Program letöltése

GitHub → Actions → **GeneRev4 Windows - EXE build** → legutóbbi sikeres futás → **Artifacts** → **GeneRev4-Windows-EXE**. A letöltött ZIP-ben megtalálod az önálló GeneRev4_Windows.exe fájlt és a magyar útmutatót.

Indítás: a ZIP kibontása után Windows 10/11-en duplán kattints a **GeneRev4_Windows.exe** fájlra. A PyInstaller onefile indítása első alkalommal lassabb lehet. Nincs telepítő, nincs rendszerszintű beavatkozás, de a Windows SmartScreen ismeretlen kiadót jelezhet, mert nincs kódaláíró tanúsítvány. Csak akkor futtasd, ha megbízol a saját GitHub-repódból származó fájlban.

## Mit tartalmaz?

- Saját grafikus Windows-felület, NEM böngésző vagy webkiszolgáló.
- ESP8266 helyi IP-cím és TCP-port megadása (5333 csak kezdeti alapérték).
- Élő, ténylegesen fogadott numerikus hőmérsékletértékek és grafikon, mérési CSV-export.
- Manuális START, STOP, COOL és 150–250 °C közötti célhőmérséklet küldése (alapból tiltva).
- MONITOR mód alapértelmezett; a valódi parancsokhoz külön kétlépcsős helyi engedélyezés szükséges. START előtt friss számszerű adat és kétperces külön élesítés is kell.
- CSV/TXT profilok betöltése, grafikon és időbeli előnézet, CSV/TXT export. **A profil-előnézet NEM vezérli a pörkölőt.**
- Helyi eseménynapló a kérésekről, kapcsolatvesztés-figyelés.

## Biztonság

**A program nem minősített biztonsági vezérlő; éles pörköléshez még nincs fizikailag tesztelve.**

- Nico ESP8266-firmware-e nem nyilvános, ezért a TCP-port, a telemetria és a firmware kompatibilitása nem igazolt.
- Egy egyszerű fogadott szám lehet célérték-visszhang és nem valós mért hőmérséklet. A szoftver ezt nem tudja biztonsággal megkülönböztetni.
- A START/STOP/COOL parancs elküldése nem bizonyítja a fizikai gép állapotát.
- Friss telemetria hiányakor a híd COOL parancsot próbál küldeni, de kapcsolatvesztéskor **nem tudja garantálni a fűtés lekapcsolását**.
- A STOP nem tekinthető fizikai vészleállításnak. Független hőhatároló, fizikai vészleállítás és folyamatos személyes felügyelet szükséges.
- Amíg a hardver nincs ellenőrizve, csak MONITOR módot használj.

## Fordítás saját Windows számítógépen

Python 3.12 és PyInstaller 6.16 szükséges. A projekt gyökeréből:

    python -m pip install pyinstaller==6.16.0
    python -m PyInstaller --clean --noconfirm --onefile --windowed --name GeneRev4_Windows --paths real --paths windows windows/GeneRev4_Windows.py

Az EXE a dist/GeneRev4_Windows.exe helyre kerül. A GitHub Actions ugyanilyen módon fordítja automatikusan.

## Licenc és forrás

Eredeti Nico projekt: https://github.com/nekowokaburu/GeneCBR101Automation
Saját projekt: https://github.com/r32rz782z82ze/GeneRev4-Web
A kód a projekt GPL-3.0 szerinti terjesztésének megfelelően készült.

A Windows GUI nem azonos Nico eredeti UWP alkalmazásával: új, Python/Tkinter kliens, amely Nico eredeti TCP vezérlési protokollját és a közös GeneRev4 hidat használja.
