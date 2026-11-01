# GeneRev4 – projektközpont / Kezdőlap

**Gene Café CBR-101 · Nico eredeti GeneRev4 rendszerére épülő saját alkalmazások**

> **Mit keresel?** Ezen az oldalon minden jelenlegi alkalmazásnak külön neve van. **A forráskód megléte nem egyenlő a valódi pörkölőn igazolt működéssel.** Éles fűtéshez a hardver és a független biztonsági lekapcsolás külön ellenőrizendő.

## 1. Melyik programot nyissam meg?

| Ha ezt szeretnéd… | Ezt válaszd | Jelenlegi állapot |
|---|---|---|
| **Profilokat megnyitni vagy megtervezni telefonon/számítógépen** | **[GeneRev4 Web – publikus profilkezelő](https://r32rz782z82ze.github.io/GeneRev4-Web/)** · [forrás](web/) | Megosztható PWA; **nem vezérli** a gépet |
| **Valódi TCP-kapcsolatot kipróbálni Windows laptopon, böngészőből** | **[GeneRev4 Web REAL](real/)** · [útmutató](real/README.md) | Helyi `127.0.0.1:8787` szerver; hardveresen **nem igazolt** |
| **Korábbi egyszerű Windows GUI-t indítani** | **[GeneRev4 Windows (régi)](windows/)** · [útmutató](windows/README.md) | TCP/kézi parancsok + **profil-előnézet**; **nem** a Studio |
| **Modern, teljesebb Windows-kezelőfelületet használni** | **GeneRev4 Studio** | A legutóbb összeállított `GeneRev4_STUDIO_WINDOWS_NICO_TELJES.zip` csomagban, **még nem ebben a GitHub-repóban** |
| **iPhone-on használni a saját natív appot** | **GeneRev4 Real iPhone** | **Külön privát GitHub-projekt**; aláírás/telepítés kell, a pörkölővel nem tesztelt |
| **Androidra tenni az eredeti TCP-s alkalmazást** | **Nico Xamarin Android-forrása** · [eredeti projekt](https://github.com/nekowokaburu/GeneCBR101Automation) | A korábban fordított **OFFLINE DEMO nem hardvervezérlő** |

**Amit először érdemes elolvasni:** [**TELJES MAGYAR PROJEKTTÉRKÉP – mi van a GitHubon, mi nincs még fent, mit lehet kihozni belőle?**](docs/PROJEKTTERKEP_HU.md)

## 2. A repó jelenlegi részei

```text
GeneRev4-Web/
├── README.md                         ← ez a kezdőlap
├── docs/
│   └── PROJEKTTERKEP_HU.md           ← teljes magyar forrás- és funkciótérkép
├── web/                              ← nyilvános GitHub Pages, profilkezelő
├── real/                             ← helyi Python TCP-híd + böngészős felület
├── windows/                          ← korábbi Python/Tkinter Windows app
└── .github/workflows/
    ├── web-pages.yml                 ← profilweboldal közzététele
    ├── real-check.yml                ← helyi híd szoftvertesztje
    └── windows-exe.yml               ← korábbi Windows-app EXE-fordító
```

Az iPhone-forrás **szándékosan külön, privát repóban** van. Az új Studio ZIP még feltöltendő a javasolt `studio/` mappába; a meglévő `windows/` mappát **nem szabad felülírni**.

## 3. Mire képes eredetileg Nico GeneRev4?

Nico [**eredeti GitHub-projektjében**](https://github.com/nekowokaburu/GeneCBR101Automation) van: Xamarin Android/iOS/Windows UWP, közös TCP és **START / STOP / CONTINUE / COOL**, CSV/TXT automatikus profilkövetés, **STM32-firmware**, PCB/Gerber/Excel BOM, Python/Artisan szkriptek és régebbi Rev3 dokumentáció.

A teljes **ESP8266 TCP-soros firmware nincs közreadva**, a régi iOS-alkalmazást Nico nem tesztelte, a mobilos grafikonok pedig kikommenteltek. A Studio modern RoR/DTR, profilrajzoló és naplózó részei **saját új fejlesztések**, nem Nico kész eredeti funkciói.

## 4. Mire van még szükség?

1. **Források egy helyre rendezése:** a modern Studio csomag hozzáadása külön `studio/` mappában.
2. **Valódi eszköz ellenőrzése:** ESP8266 saját LAN IP-cím, TCP-port és firmware-verzió; elsőként kizárólag passzív adatolvasás.
3. **Biztonság:** firmware-beli buffer/végállás/szenzorhiba, független fűtéslekapcsolás, fizikai áramtalanítás és felügyelet.
4. **Csak utána:** ellenőrzött kézi parancsok, automatikus profilpörkölés, Artisan-interfész, egységes platformfunkciók.

A részletes [funkciómátrix, telepíthetőség és fejlesztési terv itt található](docs/PROJEKTTERKEP_HU.md).

## 5. Biztonság és licencek

- **A jelenlegi alkalmazásainkat nem teszteltük teljes, működő GeneRev4 hardverrel.** A `Start`, `Stop`, `Cool` TCP-üzenet elküldése **nem** hardveres visszaigazolás.
- Kapcsolatvesztéskor a fűtés **nem garantáltan áll le**; a gépet nem szabad felügyelet nélkül működtetni. Független hővédelem és fizikai lekapcsolási lehetőség szükséges.
- Nico eredeti kódja: [GeneCBR101Automation](https://github.com/nekowokaburu/GeneCBR101Automation), GPL-3.0. A saját forrásoknál tartsuk meg a megfelelő jogi és szerzői hivatkozásokat.
