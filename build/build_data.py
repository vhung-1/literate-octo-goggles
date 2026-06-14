#!/usr/bin/env python3
"""Merge S&P prices + consensus estimates -> comp-sheet dataset (data.js).
All figures sourced from the S&P Global connector as of the price date below.
"""
import json, os

PRICE_DATE = "2026-06-12"
AS_OF = "2026-06-12"

# --- FX: units of USD per 1 unit of currency (approx, ~2026-06-12) ---
TO_USD = {"USD": 1.0, "GBP": 1.3368, "EUR": 1.1537, "CHF": 1.24,
          "SEK": 1.1537 / 10.92, "CAD": 0.715}

# --- close price (value, currency) keyed by S&P identifier ---
PRICE = {
 "CME":(269.53,"USD"),"ICE":(140.53,"USD"),"NDAQ":(88.98,"USD"),"CBOE":(294.91,"USD"),
 "LSE:LSEG":(90.10,"GBP"),"XTRA:DB1":(249.50,"EUR"),"ENXTPA:ENX":(148.20,"EUR"),
 "TW":(101.19,"USD"),"MKTX":(120.89,"USD"),"MIAX":(43.29,"USD"),"MRX":(61.96,"USD"),
 "SPGI":(418.91,"USD"),"MCO":(447.85,"USD"),"MSCI":(599.12,"USD"),"FDS":(241.16,"USD"),
 "EFX":(163.71,"USD"),"TRU":(66.13,"USD"),"LSE:EXPN":(25.69,"GBP"),"FICO":(1179.19,"USD"),
 "VRSK":(183.80,"USD"),"V":(322.39,"USD"),"MA":(489.98,"USD"),"PYPL":(41.53,"USD"),
 "XYZ":(69.52,"USD"),"ENXTAM:ADYEN":(828.40,"EUR"),"TOST":(24.82,"USD"),"SHOP":(108.24,"USD"),
 "SOFI":(16.58,"USD"),"FISV":(53.78,"USD"),"FIS":(39.20,"USD"),"GPN":(67.71,"USD"),
 "JKHY":(128.23,"USD"),"CPAY":(356.11,"USD"),"WEX":(135.50,"USD"),"AFRM":(66.17,"USD"),
 "KLAR":(16.23,"USD"),"BILL":(33.18,"USD"),"CHYM":(16.70,"USD"),"MQ":(3.83,"USD"),
 "FOUR":(41.18,"USD"),"LSE:WISE":(8.04,"GBP"),"RELY":(19.08,"USD"),"WU":(7.55,"USD"),
 "LAZ":(43.72,"USD"),"EVR":(357.38,"USD"),"MC":(67.70,"USD"),"HLI":(137.89,"USD"),
 "PWP":(15.66,"USD"),"PJT":(152.37,"USD"),"PIPR":(79.05,"USD"),"SWX:PGHN":(697.80,"CHF"),
 "OM:EQT":(287.50,"SEK"),"ENXTAM:CVC":(12.95,"EUR"),"LSE:ICG":(17.79,"GBP"),"ARES":(134.90,"USD"),
 "APO":(133.88,"USD"),"BX":(122.79,"USD"),"KKR":(96.24,"USD"),"OWL":(9.68,"USD"),
 "CG":(45.75,"USD"),"BAM":(47.13,"USD"),"TPG":(43.01,"USD"),"STEP":(44.39,"USD"),
 "HLNE":(80.10,"USD"),"BLK":(1032.00,"USD"),"TROW":(109.64,"USD"),"XTRA:DWS":(60.80,"EUR"),
 "ENXTPA:AMUN":(82.55,"EUR"),"AB":(36.44,"USD"),"BEN":(32.13,"USD"),"IVZ":(28.92,"USD"),
 "AMP":(459.13,"USD"),"SCHW":(91.10,"USD"),"LPLA":(295.66,"USD"),"HOOD":(93.19,"USD"),
 "IBKR":(90.81,"USD"),"COIN":(159.78,"USD"),"RJF":(154.40,"USD"),"SF":(72.66,"USD"),
 "WLTH":(8.96,"USD"),"ETOR":(38.52,"USD"),"SWX:SQN":(39.42,"CHF"),"XTRA:FTK":(36.12,"EUR"),
 "BIT:BGN":(60.90,"EUR"),"BIT:FBK":(21.93,"EUR"),"CRCL":(77.84,"USD"),"FIGR":(27.93,"USD"),
}

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
       "fx_note": "FX ~%s: GBPUSD 1.3368, EURUSD 1.1537, EURSEK 10.92." % PRICE_DATE,
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
