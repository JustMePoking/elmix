"""Elmix – lokal Flask-sajt: elproduktion per person (race), import/export per person och totalt.
Data: Our World in Data – Energy dataset (hämtas första gången och cachas i ./data).
Kör:  pip install -r requirements.txt && python app.py  →  http://127.0.0.1:5000
"""
from pathlib import Path
import time

import pandas as pd
import requests
from flask import Flask, jsonify

try:
    import pycountry
except ImportError:
    pycountry = None

URL = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
CACHE = Path(__file__).parent / "data" / "owid-energy-data.csv"
MAX_AGE = 30 * 24 * 3600
START, TRADE_START = 1985, 2000
PRICE_URL = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/nrg_pc_204/?format=SDMX-CSV&compressed=false"
PRICE_CACHE = Path(__file__).parent / "data" / "eurostat-nrg_pc_204.csv"

# h=vatten, w=vind, s=sol, b=bio & geo, n=kärnkraft, f=fossilt (= total minus övriga)
GROUPS = {
    "h": ["hydro_electricity"],
    "w": ["wind_electricity"],
    "s": ["solar_electricity"],
    "b": ["biofuel_electricity", "other_renewable_exc_biofuel_electricity"],
    "n": ["nuclear_electricity"],
}

app = Flask(__name__)


def fetch():
    CACHE.parent.mkdir(exist_ok=True)
    if not CACHE.exists() or time.time() - CACHE.stat().st_mtime > MAX_AGE:
        try:
            print("Hämtar data från Our World in Data …")
            r = requests.get(URL, timeout=90)
            r.raise_for_status()
            CACHE.write_bytes(r.content)
        except requests.RequestException as e:
            if not CACHE.exists():
                raise SystemExit(f"Kunde inte hämta data och ingen cache finns: {e}")
            print(f"Kunde inte uppdatera ({e}), använder cache.")


def r3(x):
    return None if pd.isna(x) else round(float(x), 3)


def mix(d):
    """MWh per person och år, fördelat på källgrupper."""
    pop, tot = d["population"], d["electricity_generation"]
    out, used = {}, pd.Series(0.0, index=d.index)
    for k, cols in GROUPS.items():
        v = pd.Series(0.0, index=d.index)
        for c in cols:
            if c in d:
                v = v + d[c].fillna(0)
        out[k] = v
        used = used + v
    out["f"] = (tot - used).clip(lower=0)
    return {k: [r3(x) for x in v * 1e6 / pop] for k, v in out.items()}  # TWh*1e6/inv = MWh/inv


def flag(iso3):
    if not pycountry:
        return ""
    c = pycountry.countries.get(alpha_3=iso3)
    return c.alpha_2.lower() if c else ""


def fetch_prices(flags, years):
    """Hushållens elpris inkl. skatter och avgifter, eurocent/kWh (Eurostat nrg_pc_204,
    band 2 500-4 999 kWh/år). Årsmedel av halvårsvärdena. Går något fel returneras {} och
    sajten fungerar som vanligt utan priser."""
    try:
        if not PRICE_CACHE.exists() or time.time() - PRICE_CACHE.stat().st_mtime > MAX_AGE:
            try:
                print("Hämtar elpriser från Eurostat …")
                r = requests.get(PRICE_URL, timeout=180, headers={"User-Agent": "elmix/1.0"})
                r.raise_for_status()
                PRICE_CACHE.write_bytes(r.content)
            except requests.RequestException as e:
                print(f"Kunde inte hämta elpriser ({e}).")
        if not PRICE_CACHE.exists():
            return {}
        p = pd.read_csv(PRICE_CACHE, usecols=["nrg_cons", "tax", "currency", "geo", "TIME_PERIOD", "OBS_VALUE"])
        p = p[(p["nrg_cons"] == "KWH2500-4999") & (p["tax"] == "I_TAX") & (p["currency"] == "EUR")]
        p = p.assign(year=p["TIME_PERIOD"].astype(str).str[:4].astype(int))
        annual = (p.groupby(["geo", "year"])["OBS_VALUE"].mean() * 100).to_dict()  # EUR -> eurocent
        out = {}
        for iso, f in flags.items():
            if not f:
                continue
            geo = {"GR": "EL", "GB": "UK"}.get(f.upper(), f.upper())
            ser = [r3(annual.get((geo, y), float("nan"))) for y in years]
            if any(v is not None for v in ser):
                out[iso] = ser
        print(f"Elpriser för {len(out)} länder.")
        return out
    except Exception as e:  # priser är en bonus, ska aldrig stoppa bygget
        print(f"Hoppar över elpriser: {e}")
        return {}


def build():
    fetch()
    df = pd.read_csv(CACHE)
    last = int(df["year"].max())
    years = list(range(START, last + 1))
    names, flags, gen, trade = {}, {}, {}, {}
    for name, g in df.groupby("country"):
        iso = g["iso_code"].iloc[0]
        if pd.isna(iso) or str(iso).startswith("OWID"):
            continue
        d = g.drop_duplicates("year").set_index("year").reindex(years)
        pop = d["population"]
        if pop.isna().any() or pop.iloc[-1] < 1e6 and iso != "ISL":
            continue
        ok_gen = d["electricity_generation"].notna().all()
        dt = d.loc[TRADE_START:]
        ok_trade = "net_elec_imports" in d and dt["net_elec_imports"].notna().all()
        if not (ok_gen or ok_trade):
            continue
        names[iso], flags[iso] = name, flag(iso)
        if ok_gen:
            gen[iso] = mix(d)
        if ok_trade:
            trade[iso] = {
                "t": [r3(x) for x in dt["net_elec_imports"]],                      # TWh, + = import
                "p": [r3(x) for x in dt["net_elec_imports"] * 1e6 / dt["population"]],  # MWh/inv
            }
    w = df[df["country"] == "World"].drop_duplicates("year").set_index("year").reindex(years)
    return {"start": START, "tradeStart": TRADE_START, "last": last,
            "names": names, "flags": flags, "gen": gen, "trade": trade, "world": mix(w),
            "price": fetch_prices(flags, years)}


PAYLOAD = build()


@app.route("/")
def index():
    # Hitta index.html även om den ligger bredvid app.py i stället för i templates/
    here = Path(__file__).parent
    for p in (here / "templates" / "index.html", here / "index.html"):
        if p.exists():
            return p.read_text(encoding="utf-8")
    return ("Hittar inte index.html. Lägg den i mappen 'templates' bredvid app.py. "
            f"Letade i: {here}"), 500


@app.route("/api/data")
def data():
    return jsonify(PAYLOAD)


if __name__ == "__main__":
    app.run(debug=True)
