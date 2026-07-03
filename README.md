# Pražský uličník v číslech

Statistiky a funfakty o názvech cca 7 800 pražských ulic a náměstí.
Pipeline: Wikidata (SPARQL) → LLM doklasifikace (OpenRouter) → statický web.

## Spuštění

```bash
cd pipeline
pip install -r requirements.txt

python 01_stahni_wikidata.py        # stáhne ulice + P138 z Wikidat (~1 min)

export OPENROUTER_API_KEY=sk-or-...
python 02_klasifikuj_llm.py         # doklasifikuje zbytek (dávky po 25, jde přerušit)

python 03_sestav_data.py            # spočítá statistiky → web/data.js
open ../web/index.html
```

Web je čistě statický (jeden HTML + jeden data.js), funguje z disku
i z GitHub Pages. Dokud nepustíš pipeline, běží na ukázkových datech
(vidíš badge „ukázková data").

## Jak to funguje

1. **01** – SPARQL dotaz stáhne všechny položky typu ulice/náměstí ležící
   v Praze (P131* → Q1085). U ulic s vyplněnou vlastností **P138
   („pojmenováno po")** rovnou přibere: je to člověk? pohlaví, profese,
   roky života, občanství.
2. **02** – Ulice s P138 = člověk dostanou kategorii `osoba` zadarmo.
   Zbytek klasifikuje LLM do 12 pevných kategorií (osoba, světci a církev,
   česká obec, česká geografie, zahraničí, rostlina, zvíře, řemeslo,
   událost/datum, pomístní název, vlastnost, ostatní). Průběh se ukládá
   po každé dávce, skript umí navázat.
3. **03** – Sloučení, statistiky (kategorie, gender gap, profese, století
   narození, občanství) + jazykové funfakty počítané přímo z názvů
   (nejdelší/nejkratší, koncovky, předložkové názvy, první písmena).

## Sanity check

Pražský uličník (Lašťovka a kol., 2022) uvádí: 32 % osoby, 23 % místo/
poloha/charakter, 16 % obce, 12 % pomístní názvy. Pokud výsledky pipeline
vyjdou řádově jinak, něco je špatně — nejspíš pokrytí Wikidat nebo prompt.

## Známé limity

- Wikidata nemusí mít úplně všech ~7 800 ulic; skript 01 vypíše počet,
  porovnej s očekáváním. Chybějící lze doplnit z RÚIAN (ČÚZK) nebo OSM.
- LLM klasifikace je odhad, ne úřední pravda. U sporných případů je
  autorita prazskyulicnik.cz.
- Jedna ulice může mít víc motivací názvu (Vinohradská…), bereme jednu.

## Nápady na v2

- Kvíz „skutečná, nebo vymyšlená pražská ulice?"
- Mapa světa: kam všude ukazují názvy podle cizích měst a zemí
- Crossover s projektem Ve vahách: ulice seřazené podle dnešní slávy
  osob, po kterých se jmenují
- Historická vrstva: přejmenování (Stalinova → Vinohradská…)
