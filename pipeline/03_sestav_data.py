#!/usr/bin/env python3
"""
03 – Sloučí Wikidata + LLM klasifikaci, spočítá statistiky
a vygeneruje web/data.js (JS soubor, aby web fungoval i z file://).
"""

import json
import re
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
WEB_FILE = Path(__file__).parent.parent / "web" / "data.js"


def profese_skupina(profese: list[str]) -> str:
    """Zhrubí seznam profesí z Wikidat do jedné skupiny."""
    text = " ".join(profese).lower()
    pravidla = [
        ("spisovatel|básník|dramatik|prozaik|novinář|publicist", "spisovatelé a novináři"),
        ("skladatel|hudebn|zpěva|dirigent|klavírist|houslist", "hudebníci"),
        ("malíř|sochař|architekt|grafik|fotograf|výtvarn", "výtvarníci a architekti"),
        ("herec|herečka|režisér|divad", "herci a filmaři"),
        ("věde?[ck]|fyzi[kč]|chemi[kč]|matemati[kč]|biolo|lékař|astronom|histori[kč]|filozof|filolog|přírodověd", "vědci a lékaři"),
        ("politi[kč]|prezident|diplomat|státní[kc]", "politici"),
        ("voják|generál|důstojník|legionář|odbojář|letec|plukovník", "vojáci a odbojáři"),
        ("kněz|teolog|biskup|kazatel|duchovní", "duchovní"),
        ("sportovec|atlet|fotbalista|gymnasta", "sportovci"),
        ("pedagog|učitel", "pedagogové"),
    ]
    for vzor, skupina in pravidla:
        if re.search(vzor, text):
            return skupina
    return "ostatní"


def main() -> None:
    ulice = json.loads((DATA_DIR / "ulice_wikidata.json").read_text(encoding="utf-8"))
    klasifikace = json.loads((DATA_DIR / "klasifikace.json").read_text(encoding="utf-8"))
    pohlavi_dopl = {}
    if (DATA_DIR / "pohlavi_doplnene.json").exists():
        pohlavi_dopl = json.loads(
            (DATA_DIR / "pohlavi_doplnene.json").read_text(encoding="utf-8")
        )
        print(f"Načteno doplněné pohlaví pro {len(pohlavi_dopl)} ulic (skript 04).")

    kategorie = Counter()
    pohlavi = Counter()
    profese = Counter()
    stoleti = Counter()
    zeme = Counter()
    zaznamy = []

    for u in ulice:
        k = klasifikace.get(u["nazev"], {"kategorie": "ostatni", "vysvetleni": ""})
        kategorie[k["kategorie"]] += 1
        zaznamy.append(
            {"n": u["nazev"], "k": k["kategorie"], "v": k.get("vysvetleni", "")}
        )
        if k["kategorie"] == "osoba":
            p = u.get("pohlavi") or pohlavi_dopl.get(u["nazev"])
            if p:
                pohlavi[p] += 1
            else:
                pohlavi["neznámé"] += 1
            if u.get("profese"):
                profese[profese_skupina(u["profese"])] += 1
            if u.get("narozeni") and u["narozeni"].lstrip("-").isdigit():
                stoleti[f"{(int(u['narozeni']) - 1) // 100 + 1}. století"] += 1
            if u.get("obcanstvi"):
                zeme[u["obcanstvi"]] += 1

    # jazykové funfakty přímo z názvů
    nazvy = [u["nazev"] for u in ulice if u["nazev"]]
    delky = sorted(nazvy, key=len)
    pripony = Counter()
    for n in nazvy:
        slovo = n.split()[-1].lower()
        for prip in ("ova", "ská", "cká", "ní", "ná", "ého", "ých"):
            if slovo.endswith(prip):
                pripony["-" + prip] += 1
                break
    prvni_pismena = Counter(n[0].upper() for n in nazvy)
    na_ulice = sum(1 for n in nazvy if n.lower().startswith(("na ", "nad ", "pod ", "u ", "k ", "v ", "za ", "mezi ")))

    data = {
        "demo": False,
        "celkem": len(ulice),
        "kategorie": dict(kategorie.most_common()),
        "pohlavi": dict(pohlavi),
        "profese": dict(profese.most_common(12)),
        "stoleti": dict(sorted(stoleti.items())),
        "zeme": dict(zeme.most_common(10)),
        "jazyk": {
            "nejdelsi": delky[-5:][::-1],
            "nejkratsi": delky[:5],
            "pripony": dict(pripony.most_common()),
            "predlozkove": na_ulice,
            "pismena": dict(prvni_pismena.most_common()),
        },
        "ulice": zaznamy,
    }

    WEB_FILE.write_text(
        "window.ULICE_DATA = " + json.dumps(data, ensure_ascii=False) + ";",
        encoding="utf-8",
    )
    print(f"Hotovo → {WEB_FILE}")
    print(f"Celkem {len(ulice)} ulic. Kategorie:")
    for k, v in kategorie.most_common():
        print(f"  {k:18s} {v:5d}  ({v / len(ulice) * 100:.1f} %)")
    if pohlavi:
        print(f"\nGender gap: {pohlavi.get('muž', 0)} mužů vs. {pohlavi.get('žena', 0)} žen")
    print("\nOtevři web/index.html v prohlížeči.")


if __name__ == "__main__":
    main()
