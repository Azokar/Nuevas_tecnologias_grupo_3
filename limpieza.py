# limpieza.py
import pandas as pd

# -------------------------------------------------------
# 1. Cargar datos
# -------------------------------------------------------
def cargar_datos(ruta):
    df = pd.read_csv(ruta)
    print(f"✅ Archivo cargado: {ruta}")
    print(f"   Filas: {len(df)} | Columnas: {len(df.columns)}")
    return df

# -------------------------------------------------------
# 2. Manejar nulos
# -------------------------------------------------------
def manejar_nulos(df, columnas_clave):
    print("\n📊 Valores nulos por columna antes de limpiar:")
    print(df.isnull().sum())

    df = df.dropna(subset=columnas_clave)
    print(f"\n🗑️  Filas con nulos en columnas clave eliminadas. Restantes: {len(df)}")
    return df

# -------------------------------------------------------
# 3. Estandarizar texto
# -------------------------------------------------------
def estandarizar_texto(df, columnas_texto):
    for col in columnas_texto:
        if col in df.columns:
            # strip() quita espacios al inicio y al final
            # lower() convierte todo a minúsculas
            df[col] = df[col].astype(str).str.strip().str.lower()
    print(f"✅ Texto estandarizado en: {columnas_texto}")
    return df

