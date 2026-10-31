# GeneRev4 Web – Nico-alapú profilkezelő

A GeneRev4-iPhone projekt különálló, mobilbarát statikus webalkalmazása, a GitHub Pages-hez. Az eredeti Gene Café CBR-101 projekt forrása: https://github.com/nekowokaburu/GeneCBR101Automation

## Mit tud?

- Idő–célhőmérséklet CSV és TXT import, az eredeti Nico formátumokat követve (999; fejléc, tN/TN).
- Helyi profil-előnézet, szüneteltetés, időcsúszka, lépcsős grafikon.
- CSV/TXT export, profiltábla, példapontok, mobilbarát PWA.
- A kézi tervezési célhőmérsékletet a böngésző helyben megőrzi.

## Mit NEM tud?

- Nem küld Start/Stop/Cool/temp parancsokat a pörkölőnek. GitHub Pages statikus tárhely; a böngésző nem nyithat közvetlen, nyers TCP-kapcsolatot a Nico ESP8266 portjára.
- Nincs valódi hőmérsékletmérés, szenzoradat vagy hamis csatlakozási állapot.
- Az előnézet nem jelent hardveres működést, pörkölést vagy automatikus leállást.

Éles irányításhoz megfelelő jogosultságokkal rendelkező és biztonsági szempontból tesztelt helyi híd + független hardveres védelem szükséges. Nico eredeti ESP8266 firmware-e nincs publikálva.

## Helyi használat

A projektgyökérből:

    cd web
    python -m http.server 8765

Majd http://localhost:8765/ . Az oldalt fájlból megnyitni nem ajánlott az ES modulok miatt.

## Teszt

    node --test web/tests/profile.test.mjs

## GitHub Pages közzététel

A .github/workflows/web-pages.yml fájl a web/ mappát publikálja. GitHub → Settings → Pages → Build and deployment → Source: GitHub Actions. A munkafolyamat main-re történő webes módosításoknál és manuálisan is futtatható.

Fontos: GitHub Free mellett a Pages szolgáltatás általában csak nyilvános repóban használható; privát repóhoz GitHub Pro vagy megfelelő magasabb csomag szükséges. A Pages weboldal akkor is nyilvános, ha a forrás-repó privát. A privát iOS-forrást nem publikáljuk szándékosan. Ne változtasd a repót public-ra annak következményeinek megértése nélkül.

Független weboldal később külön, nyilvános repóba is áthelyezhető, ami csak a web/ mappa forrásait tartalmazza.

## Licenc

Az eredeti GeneRev4 szerzői munkájából származó kompatibilitási részek a repó GPL-3.0 licencének megfelelően használhatók. A webes kód ugyanebben a repóban, GPL-3.0 alatt szerepel.
