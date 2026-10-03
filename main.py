# Archivo principal
import sys
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')  # Permite emojis en la consola de Windows

from limpieza import cargar_datos, manejar_nulos, estandarizar_texto, limpieza_especifica, eliminar_duplicados, guardar_datos

print("=" * 50)
print("   CARGANDO, LIMPIANDO Y GUARDANDO DATOS...")
print("=" * 50)

print("\n--- Procesando USUARIOS ---")
df_usuarios = cargar_datos("data/raw/usuarios.csv")
df_usuarios = manejar_nulos(df_usuarios, columnas_clave=["nombre_usuario", "correo"])
df_usuarios = estandarizar_texto(df_usuarios, columnas_texto=["nombre_usuario", "programa"])
df_usuarios = limpieza_especifica(df_usuarios)
df_usuarios = eliminar_duplicados(df_usuarios, columna_unica="correo")
guardar_datos(df_usuarios, "data/processed/usuarios_limpio.csv")

# --- Libros ---
print("\n--- Procesando LIBROS ---")
df_libros = cargar_datos("data/raw/libros.csv")
df_libros = manejar_nulos(df_libros, columnas_clave=["nom_libro"])
df_libros = estandarizar_texto(df_libros, columnas_texto=["nom_libro", "autor", "editorial"])
df_libros = limpieza_especifica(df_libros)
guardar_datos(df_libros, "data/processed/libros_limpio.csv")

# --- Equipos ---
print("\n--- Procesando EQUIPOS ---")
df_equipos = cargar_datos("data/raw/equipos_tecnologicos.csv")
df_equipos = manejar_nulos(df_equipos, columnas_clave=["nom_equipo"])
df_equipos = estandarizar_texto(df_equipos, columnas_texto=["nom_equipo", "tipo_equipo", "estado_equipo"])
df_equipos = limpieza_especifica(df_equipos)
guardar_datos(df_equipos, "data/processed/equipos_limpio.csv")

print("\n✅ Proceso completado. Archivos guardados en data/processed/\n")

# MENÚ DE CONSOLA (Usando los datos ya limpios)

def mostrar_menu():
    print("\n" + "=" * 50)
    print("   MENÚ DE ANÁLISIS DE DATOS - NEXOU")
    print("=" * 50)
    print("1. Agrupar: Usuarios por programa")
    print("2. Filtrar: Libros disponibles")
    print("3. Filtrar: Equipos disponibles")
    print("4. Filtrar: Buscar usuarios por semestre")
    print("5. Agrupar: Promedio días de préstamo por editorial")
    print("6. Combinar: Inventario de libros prestados")
    print("0. Salir")
    print("-" * 50)

# -------------------------------------------------------
# BUCLE PRINCIPAL DEL MENÚ
# -------------------------------------------------------
while True:
    mostrar_menu()
    opcion = input("Selecciona una opción: ")

    match opcion:

        case "1":
            # Agrupación (groupby)
            res = df_usuarios.groupby("programa").size().reset_index(name="Cantidad")
            print("\n📚 USUARIOS POR PROGRAMA:\n", res.to_string(index=False))

        case "2":
            # Filtrado
            disp = df_libros[df_libros["cantidad_disponible"] > 0]
            print("\n📖 LIBROS DISPONIBLES:\n", disp[["nom_libro", "cantidad_disponible"]].to_string(index=False))

        case "3":
            # Filtrado
            disp = df_equipos[df_equipos["estado_equipo"] == "disponible"]
            print("\n💻 EQUIPOS DISPONIBLES:\n", disp[["nom_equipo", "cantidad_disponible"]].to_string(index=False))

        case "4":
            # Filtrado por input del usuario
            try:
                sem = int(input("¿Qué semestre deseas consultar? "))
                res = df_usuarios[df_usuarios["semestre"] == sem]
                if not res.empty:
                    print(f"\n👥 USUARIOS (SEM {sem}):\n", res[["nombre_usuario", "programa"]].to_string(index=False))
                else:
                    print("No hay usuarios en ese semestre.")
            except ValueError:
                print("❌ Número inválido.")

        case "5":
            # Agrupación (groupby)
            res = df_libros.groupby("editorial")["dias_prestamo_max"].mean().reset_index(name="Promedio Días")
            res["Promedio Días"] = res["Promedio Días"].round(1)
            print("\n📊 PRÉSTAMO PROMEDIO POR EDITORIAL:\n", res.to_string(index=False))

        case "6":
            # Combinación de columnas
            resumen = df_libros[["nom_libro", "cantidad_total", "cantidad_disponible"]].copy()
            resumen["prestados"] = resumen["cantidad_total"] - resumen["cantidad_disponible"]
            print("\n📦 INVENTARIO (PRESTADOS VS DISPONIBLES):\n", resumen.to_string(index=False))

        case "0":
            print("\n👋 ¡Hasta luego!")
            break

        case _:
            # El guión bajo '_' es el caso por defecto (como el 'else')
            print("❌ Opción no válida.")

