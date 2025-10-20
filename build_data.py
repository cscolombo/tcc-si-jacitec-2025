import pandas as pd, json, os, re, datetime, sys, unicodedata

DATA_DIR = "data"
out = { "datas": {}, "gerado_em": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") }

def clean(x):
    if pd.isna(x): return None
    s = str(x).strip()
    return s if s and s.lower()!="nan" else None

def slug(s: str) -> str:
    s = unicodedata.normalize('NFD', s or '').encode('ascii', 'ignore').decode('ascii')
    s = s.replace('\\n',' ').lower()
    s = re.sub(r'[^a-z0-9]+',' ', s).strip()
    return s

def normalize_headers(df):
    # Se a primeira linha parece ser cabecalho "logico", use-a
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

# tentativa flexivel de recuperar campos por sinonimos
def pick(row, key_map, *candidates):
    for cand in candidates:
        if cand in key_map:
            return clean(row.get(key_map[cand]))
    return None

def parse_file(path, date_label):
    df = read_csv_safely(path)
    df.columns = [str(c).strip() for c in df.columns]
    df = normalize_headers(df)

    # mapa de chaves por slug
    keys = { slug(k): k for k in df.columns }

    # aliases
    HORA = pick.__defaults__
    items = []
    for _, r in df.iterrows():
        hora = pick(r, keys, 'hora')
        aluno = pick(r, keys, 'aluno', 'nome do aluno', 'estudante')
        titulo = pick(r, keys, 'titulo do trabalho', 'titulo', 't tulo do trabalho')
        orientador = pick(r, keys, 'orientador', 'orientadora', 'orientador a', 'nome orientador', 'nome do orientador')
        r1 = pick(r, keys, 'revisor 1', 'revisor1', 'nome revisor 1', 'banca 1', 'avaliador 1', 'professor 1')
        r2 = pick(r, keys, 'revisor 2', 'revisor2', 'nome revisor 2', 'banca 2', 'avaliador 2', 'professor 2')

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
        m = re.match(r"^(\d{1,2}):(\d{2})$", e["hora"] or "")
        return int(m.group(1))*60 + int(m.group(2)) if m else 99999

    return sorted(items, key=sort_key)

# Gera rotulo de data sempre como DD/MM/AAAA, independente do nome do arquivo
def label_from_filename(fname: str) -> str:
    m = re.search(r'(\d{1,2})_(\d{1,2})_(\d{4})', fname)
    if m:
        d, mth, y = m.groups()
        return f"{int(d):02d}/{int(mth):02d}/{y}"
    # fallback: tenta DD-MM-YYYY, DD.MM.YYYY, etc
    m = re.search(r'(\d{1,2})[^\d](\d{1,2})[^\d](\d{4})', fname)
    if m:
        d, mth, y = m.groups()
        return f"{int(d):02d}/{int(mth):02d}/{y}"
    return fname

for fname in sorted(os.listdir(DATA_DIR)):
    if fname.lower().endswith(".csv"):
        label = label_from_filename(fname)
        path = os.path.join(DATA_DIR, fname)
        try:
            out["datas"][label] = parse_file(path, label)
            print(f"OK: {fname} -> {label} ({len(out['datas'][label])} itens)")
        except Exception as e:
            print(f"ERRO ao processar {fname}: {e}", file=sys.stderr)

with open("data.js", "w", encoding="utf-8") as f:
    f.write("window.TCC_DATA = " + json.dumps(out, ensure_ascii=False, indent=2) + ";\n")
print("data.js gerado sem notas/média e com rótulos DD/MM/AAAA.")
