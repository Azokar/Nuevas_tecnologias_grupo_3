# limpieza.py
import os
import pandas as pd

# -------------------------------------------------------
# 1. Cargar datos
# -------------------------------------------------------
def cargar_datos(ruta):
    df = pd.read_csv(ruta)
    print(f"Archivo cargado: {ruta}")
    print(f"   Filas: {len(df)} | Columnas: {len(df.columns)}")
    return df

# -------------------------------------------------------
# 2. Manejar nulos
# -------------------------------------------------------
def manejar_nulos(df, columnas_clave, valores_relleno=None):
    print("\nValores nulos por columna antes de limpiar:")
    print(df.isnull().sum())

    # Las filas sin dato en una columna clave no sirven: se eliminan
    df = df.dropna(subset=columnas_clave)
    print(f"\nFilas con nulos en columnas clave eliminadas. Restantes: {len(df)}")

    # En el resto de columnas el nulo se corrige con un valor por defecto
    if valores_relleno:
        df = df.fillna(valores_relleno)
        print(f"Nulos rellenados en: {list(valores_relleno.keys())}")
    return df

# -------------------------------------------------------
# 3. Estandarizar texto
# -------------------------------------------------------
def estandarizar_texto(df, columnas_texto):
    for col in columnas_texto:
        if col in df.columns:
            # strip() quita espacios al inicio y al final
            # lower() convierte todo a minúsculas
            df[col] = df[col].str.strip().str.lower()
    print(f"Texto estandarizado en: {columnas_texto}")
    return df

# -------------------------------------------------------
# 4. Limpieza específica del proyecto
# -------------------------------------------------------
def limpieza_especifica(df):
    if 'correo' in df.columns:
        df['correo'] = df['correo'].str.strip().str.lower()
    if 'isbn' in df.columns:
        # Elimina los guiones del ISBN, ej: 978-0132350884 → 9780132350884
        df['isbn'] = df['isbn'].str.replace('-', '')
    if 'estado_equipo' in df.columns:
        df['estado_equipo'] = df['estado_equipo'].str.strip().str.lower()
    print("Limpieza específica aplicada (correos, isbns, estados).")
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
        print(f"Se eliminaron {antes - despues} duplicados basados en '{columna_unica}'.")
    else:
        print(f"No se encontraron duplicados en '{columna_unica}'.")
    return df

# -------------------------------------------------------
# 6. Guardar datos procesados
# -------------------------------------------------------
def guardar_datos(df, ruta_destino):
    # Crea la carpeta de destino si todavía no existe
    os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
    # index=False evita que se guarde la columna de números de fila
    df.to_csv(ruta_destino, index=False)
    print(f"Datos limpios guardados en: {ruta_destino}")
