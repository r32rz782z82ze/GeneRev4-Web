# GeneRev4 — teljes projekt-térkép (magyar)

> **Ez a dokumentum a jelenleg a GitHubon ellenőrizhető állapotot mutatja.** A kód megléte, a sikeres fordítás, a telefonon történő elindulás és a valódi pörkölővel bizonyított működés **négy különböző dolog**.
>
> Az eredeti Nico projektet nem módosítjuk; a saját fejlesztések külön projektek. **Éles hardveres pörkölés nem minősített, és a független túlmelegedés-/áramtalanítás-védelem nincs igazolva.**

## 1. A három GitHub-projekt

| Hol? | Pontos szerep | Hozzáférés |
|---|---|---|
| [nekowokaburu/GeneCBR101Automation](https://github.com/nekowokaburu/GeneCBR101Automation) | **Nico eredeti GeneRev4 kódja**: közös Xamarin alkalmazás, Android/iOS/UWP indítók, STM32, PCB, Python/Artisan, régi dokumentáció | Nyilvános, eredeti szerző |
| [r32rz782z82ze/GeneRev4-Web](https://github.com/r32rz782z82ze/GeneRev4-Web) | **Saját, nyilvános projekt**: webes profilkezelő, helyi Web REAL híd, a korábbi egyszerű Windows GUI, automatikus fordítók | Nyilvános |
| `r32rz782z82ze/GeneRev4-iPhone` | **Saját, külön natív SwiftUI iPhone-projekt**: TCP, kézi vezérlés, profilkövetés, IPA-fordítás, saját tesztek | **Privát**, a forrás csak jogosult felhasználóknak |

### Ami még NINCS fent a fő saját repóban

- **GeneRev4 Studio** – a korszerűbb, sötét témájú Windows GUI külön, `GeneRev4_STUDIO_WINDOWS_NICO_TELJES.zip` csomagban van. **A `GeneRev4-Web/windows` nem ez a Studio.**
- **Android saját fordítócsomagok és offline demók** – korábbi helyi ZIP/APK-fájlok; a `GeneRev4-Web` repóban nincs külön Android projekt.
- Egy működő, tesztelt **ESP8266 TCP-soros híd firmware** – Nico saját szavaival: nincs közzétéve az eredeti repóban.
- Hardveren ellenőrzött, biztonságosan üzembe helyezett teljes rendszer.

## 2. Az eredeti Nico GitHub tartalma: mire való minden fő mappa?

| Mappa | Mi van benne? | Mit nyerünk belőle? |
|---|---|---|
| [GeneRev4App](https://github.com/nekowokaburu/GeneCBR101Automation/tree/master/GeneRev4App) | Közös Xamarin.Forms felület és TCP-logika | START/STOP/CONTINUE/COOL, 150–250 °C célérték, CSV/TXT profilok, időmérés, TCP-üzenetek |
| [GeneRev4App.Android](https://github.com/nekowokaburu/GeneCBR101Automation/tree/master/GeneRev4App.Android) | Android-indító, manifest, ikonok, Xamarin Android projekt | Android APK forrása, önmagában nincs benne a pörkölési logika |
| [GeneRev4App.iOS](https://github.com/nekowokaburu/GeneCBR101Automation/tree/master/GeneRev4App.iOS) | Régi Xamarin iOS-indító és erőforrások | Eredeti iOS-port alapja; Nico nem tesztelte iPhone-on |
| [GeneRev4App.UWP](https://github.com/nekowokaburu/GeneCBR101Automation/tree/master/GeneRev4App.UWP) | Windows UWP indító/manifest/csempék | Régi Windows-app; nem modern, kész EXE-telepítő |
| [GeneRev4_STM32](https://github.com/nekowokaburu/GeneCBR101Automation/tree/master/GeneRev4_STM32) | `GeneRev4_STM32.ino`, `roaster.cpp/.h`, `helper.cpp/.h`, projektfájlok | Fizikai SSR-fűtés, dob, ventilátor, végállás, MAX31855, 80 °C-ig COOL, Artisan mód |
| [GeneRev4_PCB](https://github.com/nekowokaburu/GeneCBR101Automation/tree/master/GeneRev4_PCB) | Gerber, Excel BOM, nyomtatott áramköri lap képei, SSR-vezérlési javítás | Elektronikai revízió / panel gyártása, szerelési referencia |
| [GeneRev4Py](https://github.com/nekowokaburu/GeneCBR101Automation/tree/master/GeneRev4Py) | Python TCP kliens/teszt/szkriptek és `artisan-settings.aset` | Artisan műszer-/gombkapcsolatok, START/STOP/COOL, adatfogadás |
| [doc](https://github.com/nekowokaburu/GeneCBR101Automation/tree/master/doc) | Régi Rev3 ZIP kézikönyv és tartozékok | Történeti referencia; **nem Rev4-firmware** |
| Gyökér | README, LICENSE, solution, gitignore | Dokumentáció, GPL-3.0 és régi Xamarin/Visual Studio fejlesztői projekt |

**Nico által valóban közölt STM32-parancsok:** `Start`, `Stop`, `Cool`, `tempNNN;`, `ArtisanOn`, `ArtisanOff`. **CONTINUE** = új `Start` alkalmazásszinten, nem önálló firmware-parancs. A sorvég a TCP-n küldött szövegnél CRLF.

**Nico eredeti alkalmazásában nincs kész élő RoR, részletes pörkölési napló, modern grafikon vagy profilrajzoló**: a mobilos OxyPlot-grafikonkód kikommentelt. A GeneRev4 Studio ilyen elemei saját továbbfejlesztések.

**Hardveres korlátok:** egy hőelem; a ventilátor és a dob PWM-értéke a firmware-ben rögzített; nincs ismert szabad ventilátor-/dobsebesség TCP-parancs; nincs igazolt, független kapcsolatvesztési fűtéslekapcsolás.

## 3. A saját GeneRev4-Web repó pontos mappatérképe

| Elérési út | Szerep | Mit tud MOST? | Mit NEM szabad állítani? |
|---|---|---|---|
| [`web/`](../web/) | Publikus, mobilbarát profilkezelő (PWA) | CSV/TXT import-export, grafikon, időbeli előnézet, példapontok | **Nem** csatlakozik az ESP8266 TCP-portjára; **nem** vezérel fűtést |
| [`real/`](../real/) | Windows laptopon futó **helyi webes TCP-híd** `bridge.py`-val | LAN TCP-csatlakozás, valódi számértékek fogadása, kézi START/STOP/COOL/célérték csak engedéllyel | Nem internetes távoli vezérlő; nem automatikus profilpörkölő; nincs fizikai ACK |
| [`windows/`](../windows/) | Korábbi Python/Tkinter Windows GUI | Helyi TCP, kézi parancsok, élő görbe, CSV/TXT-előnézet és export | **Nem az új GeneRev4 Studio**; profil-előnézete nem vezérel valódi pörkölést |
| [`.github/workflows/web-pages.yml`](../.github/workflows/web-pages.yml) | GitHub Pages publikálás | Csak a `web/` statikus fájljait teszi közzé | Nem tud helyi TCP-porthoz férni |
| [`.github/workflows/real-check.yml`](../.github/workflows/real-check.yml) | Helyi híd szoftvertesztje | Protokoll-/szintaktikai ellenőrzés | Nem fizikai gépteszt |
| [`.github/workflows/windows-exe.yml`](../.github/workflows/windows-exe.yml) | Korábbi Windows GUI ONEDIR EXE build | Hordozható többfájlos Windows-csomag GitHub Artifactként | Nem Studio EXE, nem aláírt telepítő |
| [`docs/`](./) | Ez a dokumentáció | Projekt-térkép, képességek, következő lépések | Nincs benne firmware |

A publikus weboldal: **https://r32rz782z82ze.github.io/GeneRev4-Web/**. A helyi Web REAL kezelőfelület: **http://127.0.0.1:8787/** *csak akkor*, ha a Windows laptopon a helyi Python-híd elindult.

## 4. Másik készülékre átvitel

| Platform | Hogyan? | Ami feltétel |
|---|---|---|
| Eredeti Nico Android TCP-s APK | Külön APK telepítése másik Androidra | OS-kompatibilitás/engedélyek, azonos LAN, tényleges ESP8266 IP+port, firmware-kompatibilitás |
| Android OFFLINE DEMO | APK másolása / telepítése | Csak felületpróba; **nincs valódi hardvervezérlés** |
| Saját natív iPhone SwiftUI | Apple ID-vel aláírt, telepíthető IPA vagy Xcode | Másik iPhone-ra új aláírás/provisioning lehet szükséges; iOS helyi hálózati hozzáférés; foreground futás |
| Korábbi Windows GUI | Teljes ONEDIR mappa vagy Python-forrás átadása | Windows 10/11, 64 bit; EXE mellett kötelező `_internal`; Python-forráshoz Python 3.10+ |
| Új GeneRev4 Studio | **Jelenleg külön ZIP**, `studio/01_START_GeneRev4_STUDIO.cmd` | Python 3.10+; önálló EXE-hez külön ONEDIR fordítás, még nincs GitHubon |
| Nyilvános Web/PWA | Csak az URL megnyitása | Böngésző; nem vezérel pörkölőt |

**Mindegyik valós vezérlőapp csak akkor lehet használható**, ha a pörkölő ESP8266-on valóban fut a hozzá illeszkedő TCP-soros firmware; a teljes kábelezés és vezérlő működik; a PC/telefon eléri a gépet ugyanazon LAN-on; és a fizikai biztonság ellenőrzött. A `5333` Nico példáiban alapport, **nem bizonyítja a tényleges portot**.

## 5. Képességek egy helyen: mi van meg és mi fejleszthető?

Jelölés: **Nico** = eredeti kódban; **Saját** = valamelyik jelenlegi saját alkalmazásban; **Fejleszthető** = a szükséges alapadat/protokoll alapján megírható, de még nincs kész vagy nincs igazolva.

| Funkció | Nico eredetileg | Saját projektben | További teendő |
|---|---|---|---|
| IP/port, Wi-Fi TCP | Igen | Android TCP, Swift iPhone, `real`, `windows`, Studio | Tényleges firmware/port ellenőrzése |
| START/STOP/COOL | Igen | Valódi parancsküldés megírva | Hardveres visszaigazolás és biztonsági teszt |
| CONTINUE | Kliens `Start` ismétléssel | Swift iPhone és Studio | Állapotfolytonosság ellenőrzése |
| Hőmérséklet + célérték | Igen, egy szenzor | Megírva | A célérték-visszhang kiszűrésének igazolása |
| CSV/TXT automatikus profil | Nico közös alkalmazásban | Swift iPhone és Studio vezérlési logika; publikus Web csak előnézet | Valódi hardvertesztek előtt automatika nem használható |
| Profi élő grafikon és RoR | Nem kész | Studio (külön ZIP), egyszerű grafikon más appokban | Hosszú pörkölési stabilitás teszt |
| Eseményjelölés, DTR | Nem | Studio (külön ZIP) | Valós adatokkal teszt |
| Napló, CSV/JSON, összehasonlítás | Nem kész | Studio (külön ZIP) | Formátum, mentés és UI ellenőrzése |
| Artisan-kapcsolat | `GeneRev4Py` + `.aset` | Az új Studio nem teljes Artisan-kliens | Python-szkriptek és profilkonfig javítása |
| ArtisanOn/Off / SSR-időarány | STM32-ben | UI-ból nincs kitéve | Protokoll és fűtésbiztonság teszt |
| Ventilátor- és dobsebesség külön állítása | Nincs TCP-parancs | Nincs | STM32-firmware-bővítés, motorok vizsgálata |
| BT+ET két valódi csatorna | Nincs, egy hőelem | Nincs | Új érzékelő + elektronika + firmware |
| Hardveres állapot-ACK, önálló watchdog | Nem igazolt | Nincs | **Firmware/hardver biztonsági fejlesztés** |

## 6. Mit érdemes sorrendben megcsinálni?

1. **Egy közös névhasználat:** `GeneRev4-Web` (publikus profil-PWA), `GeneRev4-Web-REAL` (helyi böngészős TCP), `GeneRev4-Windows-Legacy` (korábbi Tkinter GUI), `GeneRev4 Studio` (új fő Windows GUI), `GeneRev4 Real iPhone` (privát SwiftUI), `GeneRev4 Android TCP` (eredeti kompatibilitás), `GeneRev4 OFFLINE DEMO` (teszt).
2. **A külön Studio ZIP-et feltölteni a saját repo `studio/` mappájába** a ZIP-ben mellékelt `.github/workflows/gene-studio-windows.yml` fájllal. Másik Windows-projektet ne írjunk felül.
3. **Tesztelt verziók jelölése**: GitHub Actions szoftverteszt ≠ kompatibilitási/hardverbiztonsági teszt. Kiadáskor jelölni a verziót és a hardverállapotot.
4. **ESP8266 és STM32 tényleges verziójának azonosítása**, helyi IP/port és passzív hőmérsékletmérés tesztje fűtésindítás nélkül.
5. **Veszélyes firmware-hibák ellenőrzése/javítása**: bejövő üzenet pufferhatár, dobvégállás-időtúllépés, hőelemhibák, fűtésleállítás kapcsolatvesztésnél, független hőhatároló. Ezt a Windows felület nem oldja meg.
6. **Csak ezután** kézi vezérlési tesztek és a profilautomatika külön validálása. Egyszerre egyetlen vezérlő kliens adjon fűtésparancsot.
7. Fejlesztések: egységes kezelőfelület, profil szerkesztő/tárolás, RoR/DTR, mérési CSV/JSON, Artisan integráció, Windows aláírt telepítő, Android korszerűsítés.

## 7. Hol keresd a pontos fájlokat és fejlesztési irányokat?

- [Nico firmware (`GeneRev4_STM32.ino`)](https://github.com/nekowokaburu/GeneCBR101Automation/blob/master/GeneRev4_STM32/GeneRev4_STM32.ino)
- [Nico hardverállapotgép (`roaster.cpp`)](https://github.com/nekowokaburu/GeneCBR101Automation/blob/master/GeneRev4_STM32/roaster.cpp)
- [Nico mobilvezérlő (`OperationsPage.xaml.cs`)](https://github.com/nekowokaburu/GeneCBR101Automation/blob/master/GeneRev4App/Views/OperationsPage.xaml.cs)
- [Artisan-szkriptek és beállítás](https://github.com/nekowokaburu/GeneCBR101Automation/tree/master/GeneRev4Py)
- [Helyi TCP-híd használata](../real/README.md)
- [Korábbi Windows GUI használata](../windows/README.md)
- [Publikus Web/PWA használata](../web/README.md)

**Hatókör:** ez a leltár a három megnevezett GitHub-repó aktuális fájllistájára és a korábban megosztott, különálló GeneRev4 Studio ZIP tartalmára támaszkodik. Nem bizonyítja, hogy a valódi pörkölőben éppen melyik firmware-verzió fut.
