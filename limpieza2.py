import pandas as pd



#  Limpieza específica del proyecto

def limpieza_especifica(df):
    if 'correo' in df.columns:
        df['correo'] = df['correo'].astype(str).str.strip().str.lower()
    if 'isbn' in df.columns:
        # Elimina los guiones del ISBN
        df['isbn'] = df['isbn'].astype(str).str.replace('-', '', regex=False)
    if 'estado_equipo' in df.columns:
        df['estado_equipo'] = df['estado_equipo'].astype(str).str.strip().str.lower()
    print("✅ Limpieza específica aplicada (correos, isbns, estados).")
    return df


#  Eliminar duplicados

def eliminar_duplicados(df, columna_unica):
    antes = len(df)
    # drop_duplicates elimina filas que tengan el mismo valor en 'columna_unica'
    df = df.drop_duplicates(subset=[columna_unica])
    despues = len(df)

    if antes != despues:
        print(f"✅ Se eliminaron {antes - despues} duplicados basados en '{columna_unica}'.")
    else:
        print(f"✅ No se encontraron duplicados en '{columna_unica}'.")
    return df


#  Guardar datos procesados

def guardar_datos(df, ruta_destino):
    # index=False evita que se guarde la columna de números de fila
    df.to_csv(ruta_destino, index=False)
    print(f"💾 Datos limpios guardados en: {ruta_destino}")