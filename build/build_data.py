#!/usr/bin/env python3
"""Merge S&P prices + consensus estimates -> comp-sheet dataset (data.js).

Inputs (regenerate these from the S&P Global connector to refresh — see REFRESH.md):
  build/prices.json        {id: [close, ccy], "_date": "YYYY-MM-DD"}
  build/fx.json            {ccy: USD-per-unit, "_date": ...}
  build/estimates_raw.json one JSON object per line (consensus EPS/revenue per fiscal year)
The S&P identifier -> display-ticker -> sub-sector map (SECTORS) is stable and lives below.
"""
import json, os

HERE = os.path.dirname(__file__)
def load(name):
    with open(os.path.join(HERE, name)) as f:
        return json.load(f)

_prices = load("prices.json")
TO_USD = {k: v for k, v in load("fx.json").items() if not k.startswith("_")}
PRICE = {k: tuple(v) for k, v in _prices.items() if not k.startswith("_")}
PRICE_DATE = _prices.get("_date", "")
AS_OF = PRICE_DATE

# sector -> [(s&p id, display ticker)] preserving the user's ordering
SECTORS = {
 "Exchanges":[("CME","CME US"),("ICE","ICE US"),("NDAQ","NDAQ US"),("CBOE","CBOE US"),
   ("LSE:LSEG","LSEG LN"),("XTRA:DB1","DB1 GY"),("ENXTPA:ENX","ENX FP"),("TW","TW US"),
   ("MKTX","MKTX US"),("MIAX","MIAX US"),("MRX","MRX US")],
 "Info Services":[("SPGI","SPGI US"),("MCO","MCO US"),("MSCI","MSCI US"),("FDS","FDS US"),
   ("EFX","EFX US"),("TRU","TRU US"),("LSE:EXPN","EXPN LN"),("FICO","FICO US"),("VRSK","VRSK US")],
 "Payments / Fintech":[("V","V US"),("MA","MA US"),("PYPL","PYPL US"),("XYZ","XYZ US"),
   ("ENXTAM:ADYEN","ADYEN NA"),("TOST","TOST US"),("SHOP","SHOP US"),("SOFI","SOFI US"),
   ("FISV","FISV US"),("FIS","FIS US"),("GPN","GPN US"),("JKHY","JKHY US"),("CPAY","CPAY US"),
   ("WEX","WEX US"),("AFRM","AFRM US"),("KLAR","KLAR US"),("BILL","BILL US"),("CHYM","CHYM US"),
   ("MQ","MQ US"),("FOUR","FOUR US"),("LSE:WISE","WISE LN"),("RELY","RELY LN"),("WU","WU US")],
 "M&A Boutiques":[("LAZ","LAZ US"),("EVR","EVR US"),("MC","MC US"),("HLI","HLI US"),
   ("PWP","PWP US"),("PJT","PJT US"),("PIPR","PIPR US")],
 "Alternatives":[("SWX:PGHN","PGHN SW"),("OM:EQT","EQT SS"),("ENXTAM:CVC","CVC NA"),
   ("LSE:ICG","ICG LN"),("ARES","ARES US"),("APO","APO US"),("BX","BX US"),("KKR","KKR US"),
   ("OWL","OWL US"),("CG","CG US"),("BAM","BAM US"),("TPG","TPG US"),("STEP","STEP US"),("HLNE","HLNE US")],
 "Traditionals":[("BLK","BLK US"),("TROW","TROW US"),("XTRA:DWS","DWS GY"),("ENXTPA:AMUN","AMUN FP"),
   ("AB","AB US"),("BEN","BEN US"),("IVZ","IVZ US"),("AMP","AMP US")],
 "Wealth / Brokers":[("SCHW","SCHW US"),("LPLA","LPLA US"),("HOOD","HOOD US"),("IBKR","IBKR US"),
   ("COIN","COIN US"),("RJF","RJF US"),("SF","SF US"),("WLTH","WLTH US"),("ETOR","ETOR US"),
   ("SWX:SQN","SQ SW"),("XTRA:FTK","FTK GY"),("BIT:BGN","BGN IM"),("BIT:FBK","FBK IM"),
   ("CRCL","CRCL US"),("FIGR","FIGR US")],
}

HERE = os.path.dirname(__file__)
est = {}
with open(os.path.join(HERE, "estimates_raw.json")) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        est.setdefault(o["id"], o)  # first occurrence wins

def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

def conv_price(price, pccy, eccy):
    if pccy == eccy:
        return price
    return price * TO_USD[pccy] / TO_USD[eccy]

rows = []
missing = []
for sector, members in SECTORS.items():
    for sid, disp in members:
        e = est.get(sid)
        p = PRICE.get(sid)
        if not e or not p:
            missing.append((sid, disp, bool(e), bool(p)))
            continue
        price, pccy = p
        eccy = e["eps_ccy"]
        fy = e["fy"]
        # prefer normalized EPS; fall back to GAAP EPS where normalized is absent
        for k, d in fy.items():
            if fnum(d.get("eps")) is None and fnum(d.get("eps_gaap")) is not None:
                d["eps"] = d["eps_gaap"]; d["n"] = d.get("n_gaap"); d["_src"] = "GAAP"
            else:
                d["_src"] = "Normalized"
        years = sorted(int(k[2:]) for k in fy.keys())
        # three forward fiscal years with a usable EPS mean
        usable = [y for y in years if fnum(fy[f"FY{y}"].get("eps")) is not None]
        y3yr = usable[:3]
        while len(y3yr) < 3:
            y3yr.append(None)
        rec = {"id": sid, "ticker": disp, "name": e["name"], "sector": sector,
               "price": round(price, 2), "price_ccy": pccy, "eps_ccy": eccy,
               "fx": None if pccy == eccy else round(TO_USD[pccy] / TO_USD[eccy], 4),
               "eps_src": ("GAAP" if any(fy[f"FY{y}"]["_src"] == "GAAP"
                                         for y in y3yr if y is not None) else "Normalized"),
               "offcycle": years and years[0] >= 2027}
        price_e = conv_price(price, pccy, eccy)
        rec["price_eps_ccy"] = round(price_e, 2)
        eps_vals, rev_vals, fy_labels, pe_vals, ne_vals = [], [], [], [], []
        for y in y3yr:
            if y is None:
                eps_vals.append(None); rev_vals.append(None); fy_labels.append(None)
                pe_vals.append(None); ne_vals.append(None); continue
            d = fy[f"FY{y}"]
            eps = fnum(d.get("eps")); rev = fnum(d.get("rev")); ne = fnum(d.get("n"))
            eps_vals.append(eps)
            rev_vals.append(round(rev/1e6, 1) if rev is not None else None)  # $mm in eps_ccy
            fy_labels.append(y)
            ne_vals.append(int(ne) if ne is not None else None)
            pe_vals.append(round(price_e/eps, 1) if (eps and eps > 0) else None)
        rec["fy_labels"] = fy_labels
        rec["eps"] = [round(v, 2) if v is not None else None for v in eps_vals]
        rec["rev"] = rev_vals
        rec["n_est"] = ne_vals
        rec["pe"] = pe_vals
        # 2-yr CAGRs (FY1 -> FY3)
        def cagr(a, b, yrs=2):
            if a is None or b is None or a <= 0 or b <= 0:
                return None
            return round(((b/a)**(1/yrs) - 1) * 100, 1)
        rec["eps_cagr"] = cagr(eps_vals[0], eps_vals[2])
        rec["rev_cagr"] = cagr(rev_vals[0], rev_vals[2]) if (rev_vals[0] and rev_vals[2]) else None
        rows.append(rec)

out = {"as_of": AS_OF, "price_date": PRICE_DATE,
       "fx_note": "FX as of %s: GBPUSD %.4f, EURUSD %.4f, SEKUSD %.4f." % (
           PRICE_DATE, TO_USD["GBP"], TO_USD["EUR"], TO_USD["SEK"]),
       "sectors": list(SECTORS.keys()), "rows": rows}

with open(os.path.join(HERE, "..", "data.js"), "w") as f:
    f.write("// Auto-generated by build/build_data.py — S&P Global connector data as of %s\n" % AS_OF)
    f.write("window.COMP_DATA = ")
    json.dump(out, f, indent=1)
    f.write(";\n")

print("rows:", len(rows), "| missing:", missing)
print("offcycle:", [r["ticker"] for r in rows if r["offcycle"]])
# quick sanity print
for t in ("CME","LSE:EXPN","ENXTAM:ADYEN","OM:EQT","BAM","AFRM"):
    r = next((x for x in rows if x["id"] == t), None)
    if r:
        print(r["ticker"], "px_eps_ccy", r["price_eps_ccy"], r["eps_ccy"],
              "eps", r["eps"], "pe", r["pe"], "epsCAGR", r["eps_cagr"], "revCAGR", r["rev_cagr"])
