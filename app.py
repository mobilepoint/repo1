import math
import pandas as pd
import streamlit as st

THRESHOLDS = [1, 3, 5, 10, 20, 50]


def round_to_pack(qty: float) -> int:
    """Rotunjește cantitatea la 1,3,5,10,20,50 (sau multiplu de 50 dacă e >50)."""
    for t in THRESHOLDS:
        if qty <= t:
            return t
    return math.ceil(qty / THRESHOLDS[-1]) * THRESHOLDS[-1]


st.title("Generator comenzi APEX")

apex_file = st.file_uploader("Încarcă fișierul APEX (.csv)", type="csv")
smartbill_file = st.file_uploader(
    "Încarcă raportul SmartBill (.xls / .xlsx)", type=["xls", "xlsx"]
)

if apex_file and smartbill_file:
    # 1. APEX
    apex_df = pd.read_csv(apex_file)  # cod, nume, disponibil, pret, comanda

    # 2. SmartBill
    sb_df = pd.read_excel(smartbill_file, header=9)  # primele 9 rânduri ignorate
    sb_df.columns = (
        sb_df.columns.str.strip().str.lower().str.replace(" ", "_")
    )  # normalizare nume coloane
    sb_df = sb_df[["cod", "iesiri", "stoc_final"]]

    # 3. Combinare
    data = apex_df.merge(sb_df, on="cod", how="left")
    data[["iesiri", "stoc_final"]] = data[["iesiri", "stoc_final"]].fillna(0)

    # 4. Calcul „comanda”
    def calc_comanda(row):
        if row["stoc_final"] > row["iesiri"]:
            return 0
        return round_to_pack(row["iesiri"])

    data["comanda"] = data.apply(calc_comanda, axis=1).astype(int)

    # 5. Afișare + export
    st.dataframe(data)
    csv_bytes = data.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descarcă CSV pentru APEX", csv_bytes, "apex_comenzi.csv", "text/csv"
    )
else:
    st.info("Încarcă ambele fișiere pentru a genera comanda.")
