import streamlit as st
import pandas as pd
import unicodedata
import re
from rapidfuzz import fuzz

# İsim temizleme (normalize) fonksiyonu
def normalize_name(name):
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")
    name = re.sub(r"bireysel\s*odeme", "", name)
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", "", name)
    return name.strip()

st.title("Fuzzy (Benzerlik) Tabanlı İsim Karşılaştırma")

file1 = st.file_uploader("1. Dosya (Referans)", type=["xlsx"])
file2 = st.file_uploader("2. Dosya (Kontrol)", type=["xlsx"])

similarity_threshold = st.slider("Benzerlik Eşiği (%)", 70, 100, 90)

if file1 and file2:
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    df1.columns = [c.lower() for c in df1.columns]
    df2.columns = [c.lower() for c in df2.columns]

    name_col1 = [c for c in df1.columns if "isim" in c][0]
    name_col2 = [c for c in df2.columns if "isim" in c][0]

    df1["normalized"] = df1[name_col1].apply(normalize_name)
    df2["normalized"] = df2[name_col2].apply(normalize_name)

    # Sayımları al
    names1 = df1["normalized"].value_counts().to_dict()
    names2_raw = df2["normalized"].tolist()

    result = []

    for name1_norm, count1 in names1.items():
        match_count = 0
        used_indices = set()
        for i, name2_norm in enumerate(names2_raw):
            if i in used_indices:
                continue
            score = fuzz.ratio(name1_norm, name2_norm)
            if score >= similarity_threshold:
                match_count += 1
                used_indices.add(i)
        if match_count < count1:
            orj_name = df1[df1["normalized"] == name1_norm][name_col1].iloc[0]
            result.append({
                "İsim": orj_name,
                "1. Dosya Adet": count1,
                "2. Dosya Benzer Adet": match_count,
                "Eksik Sayı": count1 - match_count
            })

    if result:
        df_result = pd.DataFrame(result)
        st.subheader("Benzer ama Eksik Olan İsimler")
        st.dataframe(df_result)
        csv = df_result.to_csv(index=False).encode("utf-8")
        st.download_button("CSV Olarak İndir", csv, "eksik_benzer_isimler.csv", "text/csv")
    else:
        st.success("Tüm isimler yeterli sayıda eşleşiyor!")