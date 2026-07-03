#!/usr/bin/env python3
"""
01 – Stáhne pražské ulice a náměstí z Wikidat přes SPARQL.

Ke každé ulici zjistí, zda má vlastnost P138 (pojmenováno po),
a pokud je eponym člověk, přidá pohlaví, profese, národnost a roky života.

Výstup: data/ulice_wikidata.json
"""

import json
import time
from pathlib import Path

import requests

ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    "User-Agent": "PrazskeUliceStats/1.0 (osobni datovy projekt)",
    "Accept": "application/sparql-results+json",
}

OUT_DIR = Path(__file__).parent / "data"
OUT_FILE = OUT_DIR / "ulice_wikidata.json"

# Q79007 = ulice, Q174782 = náměstí, Q1200957 = nábřeží (nepovinné)
QUERY = """
SELECT ?ulice ?uliceLabel ?po ?poLabel ?poTyp ?pohlavi ?profeseLabel
       ?narozeni ?umrti ?obcanstviLabel
WHERE {
  VALUES ?typ { wd:Q79007 wd:Q174782 }
  ?ulice wdt:P31 ?typ ;
         wdt:P131* wd:Q1085 .
  OPTIONAL {
    ?ulice wdt:P138 ?po .
    OPTIONAL { ?po wdt:P31 ?poTyp . }
    OPTIONAL { ?po wdt:P21 ?pohlavi . }
    OPTIONAL { ?po wdt:P106 ?profese . }
    OPTIONAL { ?po wdt:P569 ?narozeni . }
    OPTIONAL { ?po wdt:P570 ?umrti . }
    OPTIONAL { ?po wdt:P27 ?obcanstvi . }
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "cs,en". }
}
"""


def sparql(query: str, retries: int = 3) -> dict:
    for attempt in range(retries):
        r = requests.get(
            ENDPOINT, params={"query": query}, headers=HEADERS, timeout=120
        )
        if r.status_code == 429 or r.status_code >= 500:
            wait = 10 * (attempt + 1)
            print(f"  server vrátil {r.status_code}, čekám {wait} s…")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("SPARQL endpoint opakovaně selhal.")


def val(binding: dict, key: str) -> str | None:
    return binding.get(key, {}).get("value")


def qid(uri: str | None) -> str | None:
    return uri.rsplit("/", 1)[-1] if uri else None


def main() -> None:
    print("Stahuji pražské ulice z Wikidat (může trvat i minutu)…")
    data = sparql(QUERY)
    rows = data["results"]["bindings"]
    print(f"  {len(rows)} řádků (jedna ulice může mít víc řádků kvůli profesím).")

    ulice: dict[str, dict] = {}
    for b in rows:
        u_qid = qid(val(b, "ulice"))
        u = ulice.setdefault(
            u_qid,
            {
                "qid": u_qid,
                "nazev": val(b, "uliceLabel"),
                "po_qid": None,
                "po_nazev": None,
                "po_je_clovek": False,
                "pohlavi": None,
                "profese": [],
                "narozeni": None,
                "umrti": None,
                "obcanstvi": None,
            },
        )
        if val(b, "po"):
            u["po_qid"] = qid(val(b, "po"))
            u["po_nazev"] = val(b, "poLabel")
            if qid(val(b, "poTyp")) == "Q5":
                u["po_je_clovek"] = True
            p = qid(val(b, "pohlavi"))
            if p == "Q6581097":
                u["pohlavi"] = "muž"
            elif p == "Q6581072":
                u["pohlavi"] = "žena"
            prof = val(b, "profeseLabel")
            if prof and prof not in u["profese"]:
                u["profese"].append(prof)
            u["narozeni"] = u["narozeni"] or (val(b, "narozeni") or "")[:4] or None
            u["umrti"] = u["umrti"] or (val(b, "umrti") or "")[:4] or None
            u["obcanstvi"] = u["obcanstvi"] or val(b, "obcanstviLabel")

    OUT_DIR.mkdir(exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(list(ulice.values()), ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    s_p138 = sum(1 for u in ulice.values() if u["po_qid"])
    s_lide = sum(1 for u in ulice.values() if u["po_je_clovek"])
    print(f"\nHotovo: {len(ulice)} unikátních ulic → {OUT_FILE}")
    print(f"  s vyplněným P138 (pojmenováno po): {s_p138}")
    print(f"  z toho po lidech: {s_lide}")
    print("\nDalší krok: python 02_klasifikuj_llm.py")


if __name__ == "__main__":
    main()
