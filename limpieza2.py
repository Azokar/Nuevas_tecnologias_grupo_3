import pandas as pd


#  Limpieza específica del proyecto

def limpieza_especifica(df):
    if 'correo' in df.columns:
        df['correo'] = df['correo'].astype(str).str.strip().str.lower()
    if 'isbn' in df.columns:
        # Elimina los guiones del isbn
        df['isbn'] = df['isbn'].astype(str).str.replace('-', '', regex=False)
    if 'estado_equipo' in df.columns:
        df['estado_equipo'] = df['estado_equipo'].astype(str).str.strip().str.lower()
    print("✅ Limpieza específica aplicada (correos, isbns, estados).")
    return df