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

# -------------------------------------------------------
# 4. Limpieza específica del proyecto
# -------------------------------------------------------
def limpieza_especifica(df):
    if 'correo' in df.columns:
        df['correo'] = df['correo'].astype(str).str.strip().str.lower()
    if 'isbn' in df.columns:
        # Elimina los guiones del ISBN, ej: 978-0132350884 → 9780132350884
        df['isbn'] = df['isbn'].astype(str).str.replace('-', '', regex=False)
    if 'estado_equipo' in df.columns:
        df['estado_equipo'] = df['estado_equipo'].astype(str).str.strip().str.lower()
    print("✅ Limpieza específica aplicada (correos, isbns, estados).")
    return df

# -------------------------------------------------------
# 5. Eliminar duplicados
# -------------------------------------------------------
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

# -------------------------------------------------------
# 6. Guardar datos procesados
# -------------------------------------------------------
def guardar_datos(df, ruta_destino):
    # index=False evita que se guarde la columna de números de fila
    df.to_csv(ruta_destino, index=False)
    print(f"💾 Datos limpios guardados en: {ruta_destino}")
