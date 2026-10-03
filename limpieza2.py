import pandas as pd

#  Limpieza específica del proyecto

def limpieza_especifica(df):
    if 'correo' in df.columns:
        df['correo'] = df['correo'].astype(str).str.strip().str.lower()
    if 'isbn' in df.columns:
        # Elimina los guiones 
        df['isbn'] = df['isbn'].astype(str).str.replace('-', '', regex=False)
    return df