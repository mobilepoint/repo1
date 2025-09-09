import pandas as pd
import re
import math

def split_codes(value: str) -> list[str]:
    """
    Ex.: 'GH82-26485A/26486A/26925A'
    -> ['GH82-26485A', 'GH82-26486A', 'GH82-26925A']
    """
    base_match = re.match(r'([A-Z0-9]+)-(\d+)([A-Z])(?:/(.*))?', value)
    if not base_match:
        return [value]
    prefix, first_num, suffix, rest = base_match.groups()
    codes = [f"{prefix}-{first_num}{suffix}"]
    if rest:
        for part in rest.split('/'):
            codes.append(f"{prefix}-{part}{suffix}")
    return codes

def round_qty(qty: float) -> int:
    """
    Rotunjește la setul {1, 2, 5, 10, 20, 50}.
    Dacă depășește 50, rotunjește la cel mai apropiat multiplu de 50.
    """
    if qty <= 0:
        return 0
    steps = [1, 2, 5, 10, 20, 50]
    for step in steps:
        if qty <= step:
            return step
    return 50 * math.ceil(qty / 50)

def normalize_and_order(
    supplier_path: str,
    stock_path: str,
    out_path: str
) -> None:
    # -------- 1. Fișierul de la furnizor --------
    df_sup = pd.read_excel(supplier_path, engine="openpyxl")
    df_sup = df_sup.dropna(how="all").fillna("")
    df_sup = df_sup[df_sup["Cod"].notna()]

    rows = []
    for _, row in df_sup.iterrows():
        codes = split_codes(str(row["Cod"]))
        for code in codes:
            new_row = row.copy()
            new_row["Cod"] = code.strip()
            rows.append(new_row)
    df_norm = pd.DataFrame(rows)

    # -------- 2. Mișcările de stoc --------
    df_stock = pd.read_excel(
        stock_path,
        skiprows=9,          # începe de la rândul 10
        usecols="B:H",       # col. B–H
        engine="openpyxl"
    )
    df_stock.columns = [
        "Nume Produs", "Cod", "Stoc initial",
        "Intrari", "Iesiri", "Stoc final"
    ]
    df_stock = df_stock.dropna(subset=["Cod"])
    df_stock["Cod"] = df_stock["Cod"].astype(str).strip()
    df_stock["vandut"] = df_stock["Iesiri"].fillna(0)

    # mapăm cantitatea vândută la cod
    sold_map = df_stock.set_index("Cod")["vandut"]

    # -------- 3. Calcul cantitate comandă --------
    df_norm["comanda"] = (
        df_norm["Cod"].map(sold_map).fillna(0).apply(round_qty)
    )

    # -------- 4. Export --------
    df_norm.to_csv(out_path, index=False)

if __name__ == "__main__":
    normalize_and_order(
        "intrare.xlsx",      # fișierul furnizor
        "miscari.xlsx",      # mișcări de stoc
        "iesire_comanda.csv" # rezultat pentru furnizor
    )
