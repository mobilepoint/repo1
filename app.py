import io
import re
import pandas as pd
from openpyxl import load_workbook
import streamlit as st

def remove_images_to_buffer(uploaded_file) -> io.BytesIO:
    wb = load_workbook(uploaded_file)
    for sheet in wb.worksheets:
        for img in list(sheet._images):
            sheet._images.remove(img)
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

def expand_codes(code: str):
    if pd.isna(code):
        return []
    match = re.match(r"^([A-Z0-9]+-)(.+)$", str(code))
    if match:
        prefix, rest = match.groups()
        return [prefix + part for part in rest.split("/")]
    return str(code).split("/")

def normalize_excel(file_bytes: io.BytesIO, code_column: str):
    df = pd.read_excel(file_bytes)
    df.dropna(how="all", inplace=True)
    df.dropna(axis=1, how="all", inplace=True)
    df[code_column] = df[code_column].apply(expand_codes)
    df = df.explode(code_column).reset_index(drop=True)
    return df

st.title("Normalizare fișier piese furnizor")

uploaded_file = st.file_uploader("Încarcă fișierul Excel", type=["xlsx"])

if uploaded_file:
    buffer = remove_images_to_buffer(uploaded_file)
    df_preview = pd.read_excel(buffer)
    code_col = st.selectbox("Alege coloana cu coduri", df_preview.columns)

    buffer.seek(0)
    df = normalize_excel(buffer, code_col)

    desired = ["cod", "nume", "cantitate disponibila", "pret", "comanda"]
    for i in range(len(df.columns), len(desired)):
        df[desired[i]] = pd.NA
    df = df.iloc[:, :len(desired)]
    df.columns = desired
    df["pret"] = pd.to_numeric(df["pret"], errors="coerce").fillna(0) * 5.1

    st.success("Fișierul a fost normalizat!")

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descarcă CSV",
        data=csv_bytes,
        file_name="normalized.csv",
        mime="text/csv",
    )
else:
    st.info("Încarcă un fișier Excel pentru a continua.")
