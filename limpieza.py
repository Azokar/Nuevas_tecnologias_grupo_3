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

