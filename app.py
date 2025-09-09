import io
import os
import pandas as pd
import streamlit as st

ALLOWED_ROUNDINGS = [1, 3, 5, 10, 20, 50]


def round_to_allowed(value: float) -> int:
    """Rotunjește la cea mai apropiată valoare din lista permisă."""
    for threshold in ALLOWED_ROUNDINGS:
        if value <= threshold:
            return threshold
    return ALLOWED_ROUNDINGS[-1]


def compute_order(row: pd.Series) -> int:
    iesiri = row.get("iesiri", 0)
    stoc_final = row.get("stoc final", 0)

    if pd.isna(iesiri) or pd.isna(stoc_final):
        return 0
    if iesiri > stoc_final and iesiri > 0:
        return round_to_allowed(iesiri)
    return 0


st.title("Generator comandă APEX")
st.write("Încarcă fișierele APEX (CSV) și SmartBill (Excel).")

apex_file = st.file_uploader("Fișier APEX (.csv)", type=["csv"])
smartbill_file = st.file_uploader("Fișier SmartBill (.xlsx, .xls)", type=["xlsx", "xls"])

if apex_file and smartbill_file:
    apex_df = pd.read_csv(apex_file)
    apex_df.columns = apex_df.columns.str.strip().str.lower()

    smart_df = pd.read_excel(smartbill_file)
    smart_df.columns = smart_df.columns.str.strip().str.lower()
    st.write(smart_df.columns.tolist())

    merged = apex_df.merge(
        smart_df.loc[:, ["cod", "iesiri", "stoc final"]],
        on="cod",
        how="left",
    )
    merged["comanda"] = merged.apply(compute_order, axis=1)

    st.subheader("Rezultat")
    st.dataframe(merged)

    csv_buffer = io.StringIO()
    merged.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Descarcă fișierul pentru furnizor (CSV)",
        data=csv_buffer.getvalue(),
        file_name="apex_comanda.csv",
        mime="text/csv",
    )
