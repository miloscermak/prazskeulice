# PŘEDÁVACÍ PROTOKOL — Pražské ulice v číslech

Pozn.: Projekt se původně jmenoval „Pražský uličník v číslech", přejmenováno
3. 7. 2026 kvůli kolizi s existujícím projektem Pražský uličník (Lašťovka,
prazskyulicnik.cz).

Datum předání: 3. 7. 2026 (aktualizováno po dokončení fáze pohlaví + kvíz)
Stav: v1.5 — data kompletní, pohlaví doplněno, kvíz hotový, web běží
lokálně na laptopu. Body 1 a 4 roadmapy jsou HOTOVÉ a spuštěné.
Další krok = bod 2: nasadit na GitHub Pages.

## Co projekt dělá

Statistiky a funfakty o názvech pražských ulic. Pipeline stáhla 8 066 ulic
a náměstí z Wikidat (SPARQL, vlastnost P138 „pojmenováno po"), zbytek
doklasifikoval LLM přes OpenRouter do 12 kategorií. Výsledek zobrazuje
statický web ve vizuálním stylu pražských smaltovaných cedulí.

## Struktura projektu

Umístění: `~/prazske-ulice/` (laptop Miloss-Laptop; na iMacu je starší
kopie v `~/prazske-ulice-projekt/prazske-ulice/` — pracovní je LAPTOP)

```
pipeline/
  01_stahni_wikidata.py   # SPARQL → data/ulice_wikidata.json
  02_klasifikuj_llm.py    # OpenRouter klasifikace → data/klasifikace.json
  03_sestav_data.py       # statistiky → web/data.js (vč. doplněného pohlaví)
  04_pohlavi.py           # doplnění pohlaví: heuristika + LLM → data/pohlavi_doplnene.json
  data/                   # mezivýsledky (NEmazat, klasifikace stála peníze)
  .venv/                  # virtuální prostředí (aktivace: source .venv/bin/activate)
web/
  index.html              # celý web, single file (CSS i JS inline)
  data.js                 # window.ULICE_DATA = {...}, generuje skript 03
README.md
```

## Datové formáty

**data/ulice_wikidata.json** — pole objektů:
`{qid, nazev, po_qid, po_nazev, po_je_clovek, pohlavi ("muž"/"žena"/null),
profese [], narozeni "RRRR", umrti "RRRR", obcanstvi}`

**data/pohlavi_doplnene.json** — dict `{nazev_ulice: "muž" | "žena"}`,
939 záznamů (748 heuristika, 191 LLM). Skript 03 ho automaticky přičítá.

**data/klasifikace.json** — dict `{nazev_ulice: {kategorie, vysvetleni, zdroj}}`,
zdroj je "wikidata" nebo "llm". Kategorie (12): osoba, svaty_cirkev, obec_cz,
geografie_cz, zahranici, rostlina, zvire, remeslo_profese, udalost_datum,
mistni_nazev, vlastnost, ostatni.

**web/data.js** — jeden objekt: `{demo, celkem, kategorie, pohlavi, profese,
stoleti, zeme, jazyk {nejdelsi, nejkratsi, pripony, predlozkove, pismena},
ulice [{n, k, v}]}` (n=název, k=kategorie, v=krátké vysvětlení).

## Aktuální výsledky (pro kontext i sanity check)

- osoba 2 235 (27,7 %), mistni_nazev 1 722, obec_cz 1 659, vlastnost 751,
  geografie_cz 424, remeslo_profese 372, rostlina 347, zahranici 220,
  udalost_datum 104, svaty_cirkev 91, zvire 87, ostatni 54
- Gender gap (FINÁLNÍ, po skriptu 04): 1 960 mužů vs. 160 žen
  (poměr 12,3 : 1; ženy 7,5 %). Zbývá 115 „neznámé" — množné a
  nejednoznačné případy (Curieových, Bratří Čapků), záměrně nehádáme.
- Zajímavost do textů: mezi eponymy bez Wikidat (méně slavní) je poměr
  16 : 1 — gender gap se s klesající slávou prohlubuje.
- Benchmark: Pražský uličník (Lašťovka 2022) uvádí 32 % osob, 16 % obcí,
  12 % pomístních — kategorie se nepřekrývají 1:1, řádově sedíme.

## Známé problémy a dluhy (seřazeno podle priority)

1. ~~Pohlaví neúplné~~ VYŘEŠENO 3. 7.: skript 04 doplnil 939 ulic,
   pokrytí pohlaví 95 % (2 120 z 2 235 osob).
2. Kategorie LLM vs. Uličník nejsou stejné členění — v textech na webu
   nepsat „podle Uličníku", jen „řádově odpovídá".
3. `bar-val` na mobilu — fix v CSS je nasazený (media query ≤520 px),
   ale reálný telefon zatím nikdo nezkoušel. Ověřit po nasazení.
4. Duplicitní/zaniklé ulice z Wikidat nejsou filtrované (8 066 vs.
   očekávaných ~7 800). Případně filtrovat přes P576 (datum zániku).

## Nasazení (návrh)

GitHub Pages: repo miloscermak/prazske-ulice, stačí pushnout složku `web/`
(nebo celý projekt a Pages nastavit na /web). Žádný build, žádný backend.
Před nasazením: doplnit OG metatagy (og:title, og:description, og:image —
ideálně vygenerovaná cedule s gender gapem), favicon (mini cedule),
`<html lang="cs">` už je.

## Bezpečnost

OPENROUTER_API_KEY je jen v env, nikde v kódu — před pushnutím na GitHub
zkontrolovat, že v repu není `.env` ani klíč v historii. `data/` složku
lze do repa dát (jsou to veřejná data), `.venv/` do `.gitignore`.

## Roadmapa v2 — DOHODNUTÉ POŘADÍ (2. 7. 2026)

1. **Pohlaví** — HOTOVO A SPUŠTĚNO (3. 7.). Heuristika vyřešila 748,
   LLM 191, výsledek v data/pohlavi_doplnene.json a promítnutý
   ve web/data.js. Znovu spouštět jen při změně klasifikace.
2. **Nasazení na GitHub Pages** — DALŠÍ ÚKOL, ZAČÍT TÍMTO.
   Repo miloscermak/prazske-ulice, Pages na složku /web. Přidat OG
   metatagy (návrh og:description: „8 066 pražských ulic. 1 960
   pojmenovaných po mužích, 160 po ženách."), og:image s cedulí,
   favicon (mini cedule). Před commitem: .gitignore s .venv/ a .env,
   zkontrolovat že nikde není API klíč.
3. **Mapa Prahy** — ulice obarvené podle kategorie; ukáže tematické
   čtvrti (skladatelé, města, rostliny) jako barevné ostrovy. Geometrie
   z OSM Overpass (highway s name v Praze), join s klasifikace.json
   podle názvu, GeoJSON zjednodušit (turf simplify) nebo vektorové
   dlaždice; render Leaflet/MapLibre. Pozor na velikost dat (desítky MB
   před zjednodušením).
4. **Kvíz** — HOTOVO A NASAZENO v index.html (sekce #sec-kviz).
   55 vymyšlených názvů přímo v JS (FEJKY_RAW), za běhu se filtrují
   proti skutečným ulicím v data.js, kolize nehrozí. Fejky lze doplnit.
5. **Crossover Ve vahách** — ulice seřazené podle dnešní slávy eponyma;
   join přes po_qid (1 155 osob má QID) s fame skóre. Unikátní featura,
   materiál pro newsletter/podcast.

Odloženo (nízká priorita): detail ulice, timeline století narození
(data už jsou v data.js pod klíčem `stoleti`), mapa světa.

Strategie publikace: nasadit brzo, přidávat po vrstvách — každá featura
= samostatný obsahový výstup (newsletter, glosa).

## Stav prostředí (laptop)

Patch z 2. 7. je aplikovaný, skripty 04 a 03 proběhly, web/data.js je
finální. Virtuální prostředí: `pipeline/.venv` (Python 3.13). Po otevření
nového terminálu: `cd ~/prazske-ulice/pipeline && source .venv/bin/activate`.
OPENROUTER_API_KEY není uložen — pro případné další LLM běhy znovu
exportovat. Pipeline netřeba znovu pouštět, pokud se nemění data.

## Kontext stylu

Vizuální jazyk: smaltované cedule (červená = pražská uliční tabule,
modrá = orientační čísla). Fonty Oswald (cedule) + IBM Plex Sans/Mono.
Nepřidávat další barvy ani dekorace — síla je v jednom motivu.
Texty na webu: česky, střízlivě, s lehkou ironií, žádný marketing.
