# GeneRev4 REAL – hordozható Windows alkalmazás (ONEDIR)

**Fontos: az első 2026-10-31-i, egyetlen EXE-be csomagolt változat indításakor egyes gépeken Failed to extract _decimal.pyd: decompression resulted in return code -1 hiba jelent meg.**

A javított kiadás **PyInstaller ONEDIR** felépítésű: a GeneRev4_Windows.exe mellett egy _internal mappa tartalmazza a Python-futtatókörnyezetet és a .pyd modulokat. Ez a kiadás nem bontja ki ezeket minden indításkor a Windows ideiglenes mappájába. A build a Windows GitHub runneren automatikusan ellenőrzi a _decimal.pyd jelenlétét és az EXE önellenőrzését.

## Letöltés és indítás (Windows 10/11, 64 bites)

1. GitHub → Actions → **GeneRev4 Windows - EXE build** → legfrissebb sikeres (zöld) futás.
2. **Artifacts** → GeneRev4-Windows-Portable-ONEDIR letöltése.
3. A kapott ZIP-et **teljesen bontsd ki** például C:\GeneRev4_Windows\ mappába; ne futtasd az EXE-t a ZIP előnézetéből.
4. Ellenőrizd, hogy **ugyanabban a mappában** megtalálható a GeneRev4_Windows.exe fájl, a **_internal mappa**, az útmutató és a SHA256.txt.
5. Indítsd a GeneRev4_Windows.exe fájlt. **Python telepítése nem szükséges.**
6. Alapból csak MONITOR mód fut. A valódi hardver kapcsolatát és független biztonságát később kell tesztelni.

A GeneRev4_Windows.exe fájlt **nem szabad külön elmozgatni** a _internal mappától. Ha csak az EXE-t másolod át, a program nem indul.

## Ha továbbra is hibát kapsz

- Ne a korábbi egyfájlos .exe-t indítsd; a javított verzió GitHub-csomagjában _internal mappa is van.
- Bontsd ki a ZIP-et egy rövid helyi útvonalra, például C:\GeneRev4_Windows\, és legyen elegendő szabad hely.
- Ellenőrizd a Windows Biztonság → Vírus- és veszélyforrás-kezelés → Védelmi előzmények részt, hátha a vírusvédelem zárolt vagy karanténba helyezett egy fájlt. **Ne kapcsold ki a vírusvédelmet és ne állíts be általános kivételt.** Ha blokkolást látsz, a fájlt és a riasztás okát külön vizsgálni kell.
- A csomag tartalmazza a fájlok SHA256-listáját, ez segít az átvitel sértetlenségének ellenőrzésében.
- Ha hiányzik a _decimal.pyd, töltsd le újra a teljes javított csomagot, mert hiányos a kibontás vagy a vírusvédelem módosította a fájlokat.

## A program funkciói

- Önálló grafikus Windows-ablak; nem webes böngésző vagy szerver.
- GeneRev4 ESP8266 LAN IP-cím és TCP-port (5333 a Nico szkriptjében szereplő alapport).
- Fogadott valós számértékek és élő grafikon, mérési CSV-export.
- Kézi START, STOP, COOL és 150–250 °C célérték (alapból tiltva, felügyelt élesítés).
- CSV/TXT profilimport, grafikon, időbeli előnézet, CSV/TXT export (az előnézet **nem vezérel fűtést**).
- Helyi eseménynapló.

## Biztonság

A készülékkel **még nem teszteltük**. A Nico-féle ESP8266-firmware teljes változata nem nyilvános, a TCP visszaérkező numerikus érték akár célérték-echo is lehet. A program által elküldött START/STOP/COOL nem hardveres végrehajtási visszaigazolás. Kapcsolatvesztéskor a fűtés **nem garantáltan áll le**.

Független hővédelmet, fizikai vészleállítót és személyes felügyeletet kell biztosítani. Hardvertesztig **csak MONITOR mód** ajánlott.

## Forrás / önálló fordítás

A repó gyökerében, Python 3.12-vel:

    python -m pip install pyinstaller==6.16.0
    python -m PyInstaller --clean --noconfirm --onedir --noupx --windowed --contents-directory _internal --name GeneRev4_Windows --paths real --paths windows windows/GeneRev4_Windows.py

A hordozható alkalmazás a dist/GeneRev4_Windows/ könyvtárban lesz; az egész mappát együtt kell terjeszteni.

Források:
- https://github.com/r32rz782z82ze/GeneRev4-Web
- https://github.com/nekowokaburu/GeneCBR101Automation

A saját Windows GUI új Python/Tkinter kliens a Nico által használt protokollhoz, nem Nico eredeti UWP programjának változatlan fordítása.
