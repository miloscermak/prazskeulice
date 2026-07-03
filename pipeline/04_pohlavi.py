#!/usr/bin/env python3
"""
04 – Doplní pohlaví eponyma u ulic kategorie "osoba", kde ho Wikidata nezná.

Dvě fáze:
1. Heuristika na tvaru názvu (česká gramatika je tu spolehlivý svědek):
   - genitiv ženských jmen a příjmení (Milady Horákové, Němcové, Krásnohorské)
   - přivlastňovací a genitivní tvary mužských jmen (-ova, -ého, Jana Masaryka…)
2. Zbytek po dávkách přes LLM (OpenRouter), s využitím vysvětlení z klasifikace.

Výstup: data/pohlavi_doplnene.json  {nazev_ulice: "muž" | "žena"}
Poté znovu spusť 03_sestav_data.py.
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import requests

MODEL = "anthropic/claude-haiku-4.5"
BATCH = 40
API_URL = "https://openrouter.ai/api/v1/chat/completions"

DATA_DIR = Path(__file__).parent / "data"
OUT_FILE = DATA_DIR / "pohlavi_doplnene.json"

# genitivy častých ženských křestních jmen (první slovo dvouslovného názvu)
ZENSKA_JMENA = re.compile(
    r"^(milady|boženy|elišky|anežky|marie|anny|ludmily|olgy|hany|věry|zdeňky|"
    r"jarmily|libuše|růženy|terezy|kateřiny|barbory|johanky|zuzany|emy|"
    r"karoliny|karolíny|julie|heleny|magdaleny|magdalény|františky|josefiny|"
    r"vlasty|dany|evy|ireny|marty|alžběty|žofie|drahomíry|doubravky|gabriely|"
    r"otýlie|antonie|hermíny|amálie|berty|kláry|lidmily|charlotty|adély)\b",
    re.IGNORECASE,
)
# genitivy častých mužských křestních jmen
MUZSKA_JMENA = re.compile(
    r"^(jana|karla|petra|pavla|josefa|jiřího|františka|václava|antonína|"
    r"jaroslava|miroslava|vladimíra|ladislava|stanislava|bohumila|emila|"
    r"eduarda|rudolfa|otakara|přemysla|vratislava|zdeňka|tomáše|matěje|"
    r"jakuba|martina|ondřeje|michala|milana|romana|viktora|huga|maxe|"
    r"bedřicha|vojtěcha|jindřicha|richarda|roberta|alberta|artura|leoše|"
    r"aloise|ferdinanda|gustava|huberta|ignáce|kamila|norberta|oldřicha|"
    r"prokopa|radima|svatopluka|šimona|teodora|valentina|viléma|zikmunda)\b",
    re.IGNORECASE,
)

PROMPT = """U každé pražské ulice pojmenované po člověku urči pohlaví této osoby.
Dostaneš název ulice a případně jméno osoby. Odpověz POUZE validním JSON polem,
bez markdownu: [{{"nazev": "...", "pohlavi": "muž" | "žena" | "nejasné"}}]

Ulice:
{ulice}"""


def heuristika(nazev: str) -> str | None:
    n = nazev.strip()
    slova = n.split()
    posledni = slova[-1].lower()
    # ženské tvary: Horákové, Němcové; Krásnohorské (adjektivní příjmení)
    if posledni.endswith("ové"):
        return "žena"
    if ZENSKA_JMENA.match(n):
        return "žena"
    if MUZSKA_JMENA.match(n):
        return "muž"
    # mužské tvary: Jungmannova, Wolkerova, Pošepného, Mácův…
    if posledni.endswith(("ova", "ovo", "ův")) and len(slova) == 1:
        return "muž"
    if posledni.endswith("ého"):
        return "muž"
    return None


def call_llm(polozky: list[str], api_key: str) -> list[dict]:
    prompt = PROMPT.format(ulice="\n".join(polozky))
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
    ulice = json.loads((DATA_DIR / "ulice_wikidata.json").read_text(encoding="utf-8"))
    klasifikace = json.loads((DATA_DIR / "klasifikace.json").read_text(encoding="utf-8"))

    hotovo: dict[str, str] = {}
    if OUT_FILE.exists():
        hotovo = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        print(f"Navazuji: {len(hotovo)} už doplněno.")

    cile = [
        u for u in ulice
        if klasifikace.get(u["nazev"], {}).get("kategorie") == "osoba"
        and not u.get("pohlavi")
        and u["nazev"] not in hotovo
    ]
    print(f"Osob s neznámým pohlavím: {len(cile)}")

    # fáze 1: heuristika
    zbyva = []
    for u in cile:
        p = heuristika(u["nazev"])
        if p:
            hotovo[u["nazev"]] = p
        else:
            zbyva.append(u)
    OUT_FILE.write_text(json.dumps(hotovo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Heuristika vyřešila {len(cile) - len(zbyva)}, k LLM jde {len(zbyva)}.")

    # fáze 2: LLM
    if zbyva:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            sys.exit("Chybí OPENROUTER_API_KEY (heuristická část je uložena).")
        for i in range(0, len(zbyva), BATCH):
            davka = zbyva[i : i + BATCH]
            polozky = [
                f"{u['nazev']}"
                + (f" (osoba: {klasifikace[u['nazev']].get('vysvetleni')})"
                   if klasifikace[u["nazev"]].get("vysvetleni") else "")
                for u in davka
            ]
            try:
                vysledky = call_llm(polozky, api_key)
            except Exception as e:
                print(f"  dávka {i // BATCH + 1}: chyba ({e}), čekám 20 s…")
                time.sleep(20)
                continue
            for v in vysledky:
                nazev = v.get("nazev", "").split(" (osoba:")[0].strip()
                if v.get("pohlavi") in ("muž", "žena"):
                    hotovo[nazev] = v["pohlavi"]
            OUT_FILE.write_text(
                json.dumps(hotovo, ensure_ascii=False, indent=1), encoding="utf-8"
            )
            print(f"  {min(i + BATCH, len(zbyva))}/{len(zbyva)} hotovo")
            time.sleep(1)

    m = sum(1 for p in hotovo.values() if p == "muž")
    z = sum(1 for p in hotovo.values() if p == "žena")
    print(f"\nDoplněno celkem: {m} mužů, {z} žen → {OUT_FILE}")
    print("Teď znovu spusť: python 03_sestav_data.py")


if __name__ == "__main__":
    main()
