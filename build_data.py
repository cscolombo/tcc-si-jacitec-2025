import pandas as pd, json, os, re, datetime, sys

DATA_DIR = "data"
out = { "datas": {}, "gerado_em": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") }

def clean(x):
    if pd.isna(x): return None
    s = str(x).strip()
    return s if s and s.lower()!="nan" else None

def normalize_headers(df):
    first_row = df.iloc[0]
    header_like = sum(isinstance(x, str) and x.strip() != "" for x in first_row)
    if header_like >= max(3, int(len(df.columns)*0.4)):
        mapping = { old: first_row[i] if str(first_row[i]).strip() else old for i, old in enumerate(df.columns) }
        df = df.rename(columns=mapping)
        df = df.iloc[1:].reset_index(drop=True)
    return df

def read_csv_safely(path):
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        return pd.read_csv(path, engine="python", sep=None)

def parse_file(path, date_label):
    df = read_csv_safely(path)
    df.columns = [str(c).strip() for c in df.columns]
    df = normalize_headers(df)

    items = []
    for _, row in df.iterrows():
        hora = clean(row.get("Hora"))
        aluno = clean(row.get("Aluno"))
        titulo = clean(row.get("Título do trabalho")) or clean(row.get("Titulo do trabalho"))
        orientador = clean(row.get("Nome\\nOrientador")) or clean(row.get("Nome Orientador")) or clean(row.get("Orientador"))
        r1 = clean(row.get("Nome\\nRevisor 1")) or clean(row.get("Nome Revisor 1")) or clean(row.get("Revisor 1"))
        r2 = clean(row.get("Nome\\nRevisor 2")) or clean(row.get("Nome Revisor 2")) or clean(row.get("Revisor 2"))
        if hora and (aluno or titulo):
            items.append({
                "data": date_label,
                "hora": hora,
                "aluno": aluno,
                "titulo": titulo,
                "orientador": orientador,
                "revisor1": r1,
                "revisor2": r2
            })

    def sort_key(e):
        m = re.match(r"^(\\d{1,2}):(\\d{2})$", e["hora"] or "")
        return int(m.group(1))*60 + int(m.group(2)) if m else 99999

    return sorted(items, key=sort_key)

for fname in sorted(os.listdir(DATA_DIR)):
    if fname.lower().endswith(".csv"):
        m = re.search(r"(\\d{1,2})_(\\d{1,2})_(\\d{4})", fname)
        label = f"{m.group(1)}/{m.group(2)}/{m.group(3)}" if m else fname
        path = os.path.join(DATA_DIR, fname)
        try:
            out["datas"][label] = parse_file(path, label)
            print(f"OK: {fname} -> {label} ({len(out['datas'][label])} itens)")
        except Exception as e:
            print(f"ERRO ao processar {fname}: {e}", file=sys.stderr)

with open("data.js", "w", encoding="utf-8") as f:
    f.write("window.TCC_DATA = " + json.dumps(out, ensure_ascii=False, indent=2) + ";\n")
print("data.js gerado sem campos de notas/média.")
