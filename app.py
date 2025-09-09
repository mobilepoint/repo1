import re
import io
import pandas as pd
from openpyxl import load_workbook
import streamlit as st

# ---- funcții utilitare ----
def remove_images_to_buffer(uploaded_file) -> io.BytesIO:
    """Încărcă fișierul în memorie și elimină imaginile."""
    wb = load_workbook(uploaded_file)
    for sheet in wb.worksheets:
        for img in list(sheet._images):
            sheet._images.remove(img)
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

def expand_codes(code: str):
    """
    Ex: 'GH82-26485A/26486A/26925A'
    -> ['GH82-26485A', 'GH82-26486A', 'GH82-26925A']
    """
    if pd.isna(code):
        return []
    match = re.match(r"^([A-Z0-9]+-)(.+)$", code)
    if match:
        prefix, rest = match.groups()
        parts = rest.split("/")
        return [prefix + part for part in parts]
    return code.split("/")

def normalize_excel(file_bytes: io.BytesIO, code_column: str):
    df = pd.read_excel(file_bytes)

    # elimină rândurile și coloanele complet goale
    df.dropna(how="all", inplace=True)
    df.dropna(axis=1, how="all", inplace=True)

    # extinde codurile cu slash
    df[code_column] = df[code_column].apply(expand_codes)
    df = df.explode(code_column).reset_index(drop=True)
    return df

# ---- interfața Streamlit ----
st.title("Normalizare fișier piese furnizor")

uploaded_file = st.file_uploader("Încarcă fișierul Excel", type=["xlsx"])

if uploaded_file:
    # 1. șterge imaginile și încarcă workbook-ul curățat
    buffer = remove_images_to_buffer(uploaded_file)

    # 2. citește o previzualizare pentru a obține numele coloanelor
    df_preview = pd.read_excel(buffer)
    code_col = st.selectbox("Alege coloana cu coduri", df_preview.columns)

    # 3. normalizează (resetează pointerul în buffer înainte de a citi din nou)
    buffer.seek(0)
    df = normalize_excel(buffer, code_col)

    st.success("Fișierul a fost normalizat!")

    # 4. oferă descărcare CSV
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descarcă CSV",
        data=csv_bytes,
        file_name="normalized.csv",
        mime="text/csv",
    )
else:
    st.info("Încarcă un fișier Excel pentru a continua.")
