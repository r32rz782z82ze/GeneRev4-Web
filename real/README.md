# GeneRev4 Web REAL – helyi TCP-híd

A Nico [GeneCBR101Automation](https://github.com/nekowokaburu/GeneCBR101Automation) projekt eredeti STM32 parancsaihoz készült, Windows laptopon futó Python 3.10+ híd és böngészős vezérlő.

**Nem demó:** valódi GeneRev4 ESP8266/STM32 esetén a híd TCP-kapcsolatot nyit, valós, soronként fogadott számadatokat jelenít meg, és csak külön engedélyezett módban küld hardverparancsokat.

**A nyilvános GitHub Pages weboldal nem vezérel gépet.** A Web REAL kizárólag a laptop saját böngészőjében, http://127.0.0.1:8787/ címen fut; másik telefonról, LAN-eszközről vagy internetről nem érhető el.

## Windows indítás

1. GitHub Desktop: GeneRev4-Web → Fetch origin / Pull origin.
2. Repository → Show in Explorer → real mappa.
3. START_GeneRev4_REAL.cmd indítása.
4. 1 = csak valódi mérés, 2 = helyben külön engedélyezett, felügyelt manuális vezérlés.
5. A laptopon megnyitni: http://127.0.0.1:8787/
6. Megadni a GeneRev4 ESP8266 saját LAN IP-címét. A 5333 csupán a Nico Python-szkriptekben szereplő alapport, a tényleges firmware-port külön ellenőrzendő.

A laptop és a pörkölő azonos helyi hálózaton legyen. Python 3.10+ szükséges, egyéb Python-csomag nem. A HTTP szerver csak 127.0.0.1-re hallgat, CSRF-védelmet használ. Ne állítsd át 0.0.0.0-ra.

## Nico eredeti STM32-forrásában ellenőrzött protokoll

GeneRev4_STM32/GeneRev4_STM32.ino és roaster.cpp alapján:

- START: ASCII Start + CRLF, majd temp180; + CRLF; az STM32 a Start alatt lenullázza a setpointot, ezért a célértéket START után kell küldeni.
- COOL: Cool + CRLF.
- STOP: Stop + CRLF; a firmware visszaállítja a dobot, és 80 °C alatt kapcsolja le a ventilátort.
- Célérték: tempNNN; + CRLF, egész 150–250 °C.
- Telemetria: számérték / sor. A temp-parancs nyomán az STM32 a célértéket is visszaírhatja; a szám nem egyértelmű fizikai hőmérséklet-visszaigazolás.

Az ESP8266 firmware-e **nincs** közzétéve Nico GitHubján. Ezt és a fizikai hardvert külön tesztelni kell.

## Biztonság: kötelező olvasnivaló

- Indításkor csak MONITOR mód engedélyezett; valódi parancsokhoz a Windows CMD-ben külön választás és FELUGYELEM visszaigazolás szükséges.
- A webfelületen külön, 2 perces élesítés kell a START előtt.
- START és célhőmérséklet-küldés csak friss számszerű mérés mellett engedélyezett.
- STOP és COOL hiányzó friss mérés mellett is kérhető, amennyiben a TCP még elérhető.
- Indítás után 3 másodpercig hiányzó friss adat esetén a híd COOL parancs küldésével próbálkozik, és a vezérlést tiltja. A hardver végrehajtása NEM igazolható.
- Kapcsolatbontáskor, futáskérés után a híd szintén COOL küldését kísérli meg. Kapcsolatvesztés esetén a valódi fűtés NEM garantáltan áll le.
- Az alkalmazás nem tartalmaz automatikus profilkövetést, távoli internetes START-ot vagy feltétel nélküli újracsatlakozást. Ennek feltétele egy független, tesztelt hardveres watchdog / fűtéslekapcsolás.
- A parancs elküldése nem firmware- vagy hardware-ACK; az app csak kért, nem fizikailag igazolt állapotokat jelez.

**Független hővédelem, fizikai vészleállító és helyszíni felügyelet nélkül ne használj valódi fűtésvezérlést.** A program nem minősített biztonsági rendszer.

## Tesztek

A repó gyökerében futtatható:

    python -m unittest discover -s real/tests -v

A GitHub Actions ezzel a protokollformátumot és vezérlési tiltásokat szoftverszinten teszteli. Nem csatlakozik fizikai géphez, nem indít fűtést.

## Gyakori hibák

- Nem csatlakozik: ellenőrizd az ESP8266 valódi Wi-Fi IP-jét és portját.
- TCP van, de nincs szenzoradat: a START le van tiltva; a firmware és adatfolyam külön ellenőrzendő.
- Internetes Pages-oldalon nem érhető el: a Python-híd a laptopon fut, nem a GitHubon.
- iPhone-on localhost használatával nem nyitható meg: a localhost az iPhone-ra mutat. A külön natív iPhone-app alkalmasabb helyi Wi-Fi-s hardvervezérlésre, miután azt is hardveresen ellenőrizted.

Licenc: GPL-3.0, Nico eredeti forrására hivatkozva.
