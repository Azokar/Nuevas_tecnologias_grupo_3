import pandas as pd 

def limpieza_especifica(df):
    if 'correo' in df.columns:
        df['correo'] = df['correo'].astype(str).str.strip().str.lower()
    return df
