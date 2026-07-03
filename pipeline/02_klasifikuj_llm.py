#!/usr/bin/env python3
"""
02 – Doklasifikuje ulice pomocí LLM (OpenRouter).

Ulice, které mají na Wikidatech P138 s člověkem, dostanou kategorii "osoba"
automaticky. Zbytek se klasifikuje po dávkách přes LLM do pevné taxonomie.

Průběh se ukládá po každé dávce do data/klasifikace.json,
skript jde kdykoli přerušit a pustit znovu (naváže, kde skončil).

Použití:
    export OPENROUTER_API_KEY=sk-or-...
    python 02_klasifikuj_llm.py
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

MODEL = "anthropic/claude-haiku-4.5"  # levný a na tohle bohatě stačí
BATCH = 25
API_URL = "https://openrouter.ai/api/v1/chat/completions"

DATA_DIR = Path(__file__).parent / "data"
IN_FILE = DATA_DIR / "ulice_wikidata.json"
OUT_FILE = DATA_DIR / "klasifikace.json"

KATEGORIE = [
    "osoba",            # konkrétní člověk (Jungmannova, Seifertova)
    "svaty_cirkev",     # světci, církevní pojmy (Anenská, Dušní, U Anděla)
    "obec_cz",          # česká obec či město (Kolínská, Benešovská)
    "geografie_cz",     # české hory, řeky, kraje (Šumavská, Vltavská)
    "zahranici",        # cizí města, země, regiony (Pařížská, Norská)
    "rostlina",         # (Šeříková, Lipová, Pomněnková)
    "zvire",            # (Sokolí, Jelení, Poštolčí)
    "remeslo_profese",  # řemesla a profese (Provaznická, Platnéřská)
    "udalost_datum",    # události a data (5. května, Pražského povstání)
    "mistni_nazev",     # pomístní názvy (Na Babě, Na Bojišti, Pohořelec)
    "vlastnost",        # vzhled, poloha, charakter (Krátká, Šikmá, Polední)
    "ostatni",
]

PROMPT = """Jsi expert na pražskou toponymii. Dostaneš seznam názvů pražských ulic.
Ke každé urči kategorii původu názvu. Povolené kategorie (použij přesně tyto kódy):

{kategorie}

Odpověz POUZE validním JSON polem objektů, bez markdownu a bez komentáře:
[{{"nazev": "...", "kategorie": "...", "vysvetleni": "max 8 slov, po kom/čem"}}]

Pokud si nejsi jistý, zvol nejpravděpodobnější kategorii. U kategorie "osoba"
uveď do vysvětlení celé jméno osoby, pokud ho znáš.

Ulice:
{ulice}"""


def call_llm(nazvy: list[str], api_key: str) -> list[dict]:
    prompt = PROMPT.format(
        kategorie="\n".join(f"- {k}" for k in KATEGORIE),
        ulice="\n".join(nazvy),
    )
    r = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        },
        timeout=180,
    )
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    return json.loads(text)


def main() -> None:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("Chybí OPENROUTER_API_KEY v prostředí.")
    if not IN_FILE.exists():
        sys.exit("Chybí data/ulice_wikidata.json – spusť nejdřív 01_stahni_wikidata.py")

    ulice = json.loads(IN_FILE.read_text(encoding="utf-8"))
    hotovo: dict[str, dict] = {}
    if OUT_FILE.exists():
        hotovo = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        print(f"Navazuji: {len(hotovo)} ulic už je klasifikováno.")

    # 1) Wikidata řekla, že jde o člověka → kategorie zdarma
    for u in ulice:
        if u["nazev"] in hotovo:
            continue
        if u["po_je_clovek"]:
            hotovo[u["nazev"]] = {
                "kategorie": "osoba",
                "vysvetleni": u["po_nazev"] or "",
                "zdroj": "wikidata",
            }

    # 2) zbytek přes LLM
    zbyva = [u["nazev"] for u in ulice if u["nazev"] not in hotovo]
    print(f"K LLM klasifikaci zbývá {len(zbyva)} ulic (dávky po {BATCH}).")

    for i in range(0, len(zbyva), BATCH):
        davka = zbyva[i : i + BATCH]
        try:
            vysledky = call_llm(davka, api_key)
        except Exception as e:
            print(f"  dávka {i // BATCH + 1}: chyba ({e}), čekám 20 s a pokračuji…")
            time.sleep(20)
            continue
        for v in vysledky:
            kat = v.get("kategorie")
            if kat not in KATEGORIE:
                kat = "ostatni"
            hotovo[v.get("nazev", "")] = {
                "kategorie": kat,
                "vysvetleni": v.get("vysvetleni", ""),
                "zdroj": "llm",
            }
        OUT_FILE.write_text(
            json.dumps(hotovo, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"  {min(i + BATCH, len(zbyva))}/{len(zbyva)} hotovo")
        time.sleep(1)

    print(f"\nHotovo → {OUT_FILE}")
    print("Další krok: python 03_sestav_data.py")


if __name__ == "__main__":
    main()
