import io
import re
import pandas as pd
import streamlit as st


# ---- Utilitare --------------------------------------------------------------
def split_codes(code: str):
    """Împarte șiruri de coduri de forma GH82-26485A/26486A/26925A."""
    parts = [p.strip() for p in str(code).split("/") if p.strip()]
    if len(parts) <= 1:
        return parts
    m = re.match(r"^(.+?-)", parts[0])  # prefixul înainte de primul „-”
    prefix = m.group(1) if m else ""
    codes = [parts[0]]
    for p in parts[1:]:
        codes.append(p if "-" in p else prefix + p)
    return codes


def normalize_apex(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how="all").dropna(axis=1, how="all")  # elimină rânduri/coloane goale
    df.columns = [str(c).strip().lower() for c in df.columns]
    aliases = {
        "cod": {"cod", "product code"},
        "nume": {"nume", "descriere"},
        "disponibil": {"disponibil", "stock"},
        "pret": {"pret", "price"},
    }
    normalized_cols = {}
    for key, names in aliases.items():
        for name in names:
            if name in df.columns:
                normalized_cols[name] = key
                break
    missing = [k for k in aliases if k not in normalized_cols.values()]
    if missing:
        raise ValueError(f"Lipsesc coloanele necesare din APEX: {', '.join(missing)}")
    df = df.rename(columns=normalized_cols)[list(aliases.keys())]
    df["pret"] = pd.to_numeric(df["pret"], errors="coerce").fillna(0) * 5.1

    rows = []
    for _, row in df.iterrows():
        for code in split_codes(row["cod"]):
            new_row = row.copy()
            new_row["cod"] = code
            new_row["comanda"] = 0
            rows.append(new_row)
    out = pd.DataFrame(rows)
    return out[["cod", "nume", "disponibil", "pret", "comanda"]]


def parse_smartbill(file) -> pd.DataFrame:
    sb = pd.read_excel(file, header=None)
    sb = sb.iloc[9:]                    # ignoră primele 9 rânduri
    sb.columns = sb.iloc[0]             # rândul 10 devine antet
    sb = sb[1:]
    sb.columns = [str(c).strip().lower() for c in sb.columns]
    sb = sb.rename(columns={"produs": "cod"})
    sb = sb[["cod", "iesiri", "stoc final"]]
    sb["iesiri"] = pd.to_numeric(sb["iesiri"], errors="coerce").fillna(0)
    sb["stoc final"] = pd.to_numeric(sb["stoc final"], errors="coerce").fillna(0)
    sb["comanda"] = sb.apply(
        lambda r: 0 if r["stoc final"] > r["iesiri"] else r["iesiri"], axis=1
    )
    return sb[["cod", "comanda"]]
# ----------------------------------------------------------------------------


def main():
    st.title("Normalizare APEX și calcul comenzi")

    apex_file = st.file_uploader("Încarcă fișierul APEX", type=["xls", "xlsx"])
    smartbill_file = st.file_uploader("Încarcă fișierul Smartbill", type=["xls", "xlsx"])

    if apex_file and smartbill_file:
        try:
            apex_df = normalize_apex(pd.read_excel(apex_file))
        except ValueError as e:
            st.error(str(e))
            return

        # 1.1: exportă APEX normalizat în CSV și folosește-l mai departe
        csv_bytes = apex_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Descarcă APEX normalizat (CSV)",
            data=csv_bytes,
            file_name="apex_normalizat.csv",
            mime="text/csv",
        )
        apex_df = pd.read_csv(io.BytesIO(csv_bytes))

        smartbill_df = parse_smartbill(smartbill_file)

        result = (
            apex_df.drop(columns=["comanda"])
            .merge(smartbill_df, on="cod", how="left")
        )
        result["comanda"] = result["comanda"].fillna(0).astype(int)

        st.subheader("Rezultat normalizat")
        st.dataframe(result)

        buf = io.BytesIO()
        result.to_excel(buf, index=False)
        buf.seek(0)
        st.download_button(
            "Descarcă Excel pentru comandă",
            data=buf,
            file_name="comanda.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


if __name__ == "__main__":
    main()
