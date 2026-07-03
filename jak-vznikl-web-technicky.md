# Jak vznikl web Pražské ulice v číslech: technický postup

## Zadání

Výchozí prompt pro Claude:

> Projekt: v Praze je cca 7800 ulic. chtěl bych udělat hezký web, který udělá statistiky a funfakty na základě jejich názvů. Kolik ulic je pojmenovaných po lidech? kolik po zvířatech? kolik má geografické názvy? atd. napadá tě k tomu něco?

## Architektura

Tři fáze: získání dat → klasifikace → statický web. Žádný backend, žádná databáze, žádný framework. Výstupem pipeline je jeden JSON, nad kterým běží jeden HTML soubor.

## Fáze 1: Wikidata (strukturovaná data zadarmo)

Pražské ulice byly do Wikidat hromadně importovány z RÚIAN, takže je nebylo nutné stahovat z katastru. Jeden SPARQL dotaz vrátil všechny položky typu ulice a náměstí ležící v Praze: **8 066 záznamů**.

Klíčová je vlastnost **P138 („pojmenováno po")**: měla ji vyplněnou 3 830 ulic. Pokud P138 odkazuje na člověka, dotaz rovnou přibral pohlaví (P21), profese (P106), roky narození a úmrtí a občanství. Tím bylo 1 155 ulic klasifikováno jako „po osobě" bez jediného dotazu na LLM.

## Fáze 2: LLM doklasifikace zbytku

Zbylých 6 911 názvů klasifikoval Claude Haiku přes OpenRouter, v dávkách po 25, do 12 pevných kategorií (osoba, česká obec, zahraničí, rostlina, zvíře, řemeslo, pomístní název, vlastnost atd.). Skript ukládá průběh po každé dávce, takže jde kdykoli přerušit a navázat. Náklady: jednotky korun, běh cca 30 minut.

Kontrola správnosti: akademický Pražský uličník uvádí 32 % ulic pojmenovaných po osobách. Pipeline, která tento údaj neznala, došla k 27,7 % (2 235 ulic). Řádová shoda potvrdila, že LLM klasifikaci lze věřit.

## Fáze 3: Doplnění pohlaví

Wikidata znala pohlaví jen u poloviny osob. U zbylých 1 055 zafungovala nejdřív gramatická heuristika: ulice po ženách mají genitiv (Milady Horákové, koncovka -ové), po mužích přivlastňovací tvar (-ova) nebo genitiv mužských jmen. Heuristika vyřešila 748 případů (71 %), LLM dalších 191, u 115 nejednoznačných (Curieových, Bratří Čapků) zůstalo „neznámé".

Výsledek: **1 960 ulic po mužích, 160 po ženách** (poměr 12,3 : 1).

## Fáze 4: Web

Statický single-file HTML s vanilla JS, bez frameworků. Data se načítají z data.js (ne fetch, aby web fungoval i z disku). Vizuál stojí na jediném motivu: pražské smaltované cedule, červené pro názvy, modré pro čísla. Součástí je vyhledávač všech 8 066 ulic s kategorií a vysvětlením původu názvu.

## Fáze 5: Kvíz

Interaktivní hra „skutečná, nebo vymyšlená pražská ulice?". Claude předgeneroval 55 falešných názvů napodobujících reálné pražské vzory (Za Flusárnou, Rorýsí, U Vodníkovy tůně) a uložil je přímo do JavaScriptu. Web při načtení porovná falešné názvy se skutečnými daty a případné náhodné shody z kvízu vyřadí, takže kolize s realitou nehrozí. U skutečných ulic kvíz po odpovědi zobrazí kategorii a původ názvu, hra tedy zároveň slouží jako nenápadná prohlídka datasetu. Vše běží na straně prohlížeče, bez jediného volání API.

## Shrnutí čísel

| Krok | Výsledek |
|---|---|
| SPARQL z Wikidat | 8 066 ulic, 3 830 s P138 |
| Osoby z Wikidat | 1 155 (zdarma) |
| LLM klasifikace | 6 911 názvů, ~30 min, jednotky Kč |
| Pohlaví heuristikou | 748 ze 1 055 (zdarma) |
| Gender gap | 1 960 mužů : 160 žen |
