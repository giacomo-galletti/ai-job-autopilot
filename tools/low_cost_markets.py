#!/usr/bin/env python3
"""Recognise postings from low-cost labour markets, which are skipped at search time.

A posting located only in these markets is hiring at local rates (rate arbitrage), so /scrape
drops it before fit scoring. A posting that also lists an acceptable location, such as your home
region or worldwide remote, is kept.

Exceptions: a place whose name contains a low-cost region (for example a country inside a broad
region such as "Africa") can be exempted by listing it, one name per line, in
`profile/allowed_markets.txt` (lines starting with # are comments). Exempt postings reach
evaluation instead of being dropped; any salary floor is applied there.

Usage: bun run <portal cli> search ... --format json | python3 tools/low_cost_markets.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

# ISO 3166-1 alpha-2 code -> name: the markets employers hire in to pay local rates.
COUNTRIES = {
    "in": "India", "pk": "Pakistan", "bd": "Bangladesh", "lk": "Sri Lanka", "np": "Nepal",
    "ph": "Philippines", "vn": "Vietnam", "id": "Indonesia", "my": "Malaysia", "th": "Thailand",
    "kh": "Cambodia", "mm": "Myanmar",
    "uz": "Uzbekistan", "kz": "Kazakhstan", "kg": "Kyrgyzstan", "tj": "Tajikistan",
    "eg": "Egypt", "ma": "Morocco", "tn": "Tunisia", "dz": "Algeria", "ng": "Nigeria", "ke": "Kenya",
    "gh": "Ghana", "et": "Ethiopia", "ug": "Uganda", "rw": "Rwanda",
    "mx": "Mexico", "co": "Colombia", "ar": "Argentina", "br": "Brazil", "cl": "Chile", "pe": "Peru",
    "cr": "Costa Rica", "ec": "Ecuador", "bo": "Bolivia", "uy": "Uruguay", "py": "Paraguay",
    "ve": "Venezuela", "gt": "Guatemala", "hn": "Honduras", "sv": "El Salvador", "ni": "Nicaragua",
    "do": "Dominican Republic", "pa": "Panama",
}

# Names that appear in location text, lower-case and without accents -> market.
_ALIASES = {name.lower(): name for name in COUNTRIES.values()}
_ALIASES.update({"brasil": "Brazil", "viet nam": "Vietnam", "latam": "Latin America",
                 "latin america": "Latin America", "south america": "Latin America",
                 "central america": "Latin America", "south asia": "South Asia",
                 "southeast asia": "Southeast Asia", "africa": "Africa"})
# Cities and states that listings print without their country. LinkedIn writes some Indian metros
# as "Greater Coimbatore Area". Only names no European or US place shares.
_PLACES = {
    "India": ("bengaluru", "bangalore", "hyderabad", "pune", "chennai", "mumbai", "noida", "gurugram",
              "gurgaon", "delhi", "kolkata", "ahmedabad", "coimbatore", "kochi", "cochin",
              "thiruvananthapuram", "trivandrum", "jaipur", "chandigarh", "mohali", "indore", "nagpur",
              "lucknow", "bhubaneswar", "vadodara", "visakhapatnam", "mysuru", "mysore", "mangaluru",
              "karnataka", "maharashtra", "telangana", "tamil nadu", "kerala", "uttar pradesh",
              "haryana", "west bengal", "gujarat", "andhra pradesh", "rajasthan"),
    "Pakistan": ("karachi", "lahore", "islamabad", "rawalpindi", "faisalabad"),
    "Bangladesh": ("dhaka",),
    "Sri Lanka": ("colombo",),
    "Philippines": ("manila", "makati", "taguig", "cebu", "quezon city", "pasig"),
    "Vietnam": ("ho chi minh", "hanoi", "da nang"),
    "Indonesia": ("jakarta",),
    "Uzbekistan": ("tashkent",),
    "Egypt": ("cairo", "giza"),
    "Kenya": ("nairobi",),
    "Morocco": ("casablanca", "rabat"),
    "Colombia": ("bogota", "medellin"),
    "Argentina": ("buenos aires",),
    "Brazil": ("sao paulo", "rio de janeiro", "florianopolis", "belo horizonte", "curitiba"),
    "Uruguay": ("montevideo",),
}
for _market, _names in _PLACES.items():
    _ALIASES.update({name: _market for name in _names})
ALLOWED_FILE = Path(__file__).resolve().parent.parent / "profile" / "allowed_markets.txt"
_PATTERN = None


def allow_places(names) -> None:
    """Exempt places whose names contain a low-cost region (e.g. a city inside a broad region).

    The pattern tries longer names first, so an exempt name matches whole and resolves to no market.
    """
    global _PATTERN
    for key in [k for k, v in _ALIASES.items() if v is None]:
        del _ALIASES[key]
    _ALIASES.update({_plain(str(n)).strip(): None for n in names if str(n).strip()})
    _PATTERN = re.compile(r"\b(" + "|".join(sorted(map(re.escape, _ALIASES), key=len, reverse=True)) + r")\b")


def _load_allowed() -> list[str]:
    try:
        lines = ALLOWED_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    return [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]

# Indian IT-services firms pay offshore-anchored rates even for roles in Europe.
_INDIAN_IT_SERVICES = re.compile(
    r"\b(tata consultancy services|infosys|wipro|hcltech|hcl technologies|tech mahindra|ltimindtree"
    r"|mphasis|hexaware|persistent systems|coforge|zensar)\b")


def _plain(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).lower()


allow_places(_load_allowed())


def _text_market(segment: str) -> str | None:
    match = _PATTERN.search(_plain(segment).replace("new mexico", ""))
    return _ALIASES[match.group(1)] if match else None


def _all_low_cost(markets: list[str | None]) -> str | None:
    return markets[0] if markets and all(markets) else None


def low_cost_market(job: dict) -> str | None:
    """The low-cost market a posting is confined to, or None when it is open to somewhere else."""
    company = _plain(job.get("company") or "")
    if _INDIAN_IT_SERVICES.search(company):
        return "Indian IT services"
    if re.search(r"\bindia\s*$", company):
        return "India"
    # Structured fields win over the display text: freehire's country codes, Himalayas' restrictions.
    if job.get("countries"):
        return _all_low_cost([COUNTRIES.get(str(code).lower()) for code in job["countries"]])
    if job.get("locationRestrictions"):
        return _all_low_cost([_text_market(str(name)) for name in job["locationRestrictions"]])
    segments = [part for part in re.split(r"[;|]", job.get("location") or "") if part.strip()]
    return _all_low_cost([_text_market(part) for part in segments])


def filter_payload(payload: dict) -> dict:
    """A portal's search payload without low-cost postings, listing each one it dropped."""
    kept, dropped = [], []
    for job in payload.get("results", []):
        market = low_cost_market(job)
        if market:
            dropped.append({"id": job.get("id"), "title": job.get("title"), "company": job.get("company"),
                            "location": job.get("location"), "market": market})
        else:
            kept.append(job)
    return {**payload, "results": kept, "dropped_low_cost": dropped}


def main() -> None:
    payload = json.load(sys.stdin)
    filtered = filter_payload(payload)
    json.dump(filtered, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    print(f"dropped {len(filtered['dropped_low_cost'])} low-cost postings", file=sys.stderr)


if __name__ == "__main__":
    main()
