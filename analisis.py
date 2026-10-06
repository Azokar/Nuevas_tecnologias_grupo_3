# Archivo principal
from colorama import init, Fore, Style
from limpieza import cargar_datos, manejar_nulos, estandarizar_texto, limpieza_especifica, eliminar_duplicados, guardar_datos

init()               # Activa los colores en la consola de Windows
print(Fore.MAGENTA)  # Desde aquí todo el texto de la consola sale en magenta

# -------------------------------------------------------
# MENÚ DE ANÁLISIS (usa los datos ya limpios)
# -------------------------------------------------------
def menu_analisis():
    while True:
        print("\n" + "=" * 50)
        print("   MENÚ DE ANÁLISIS DE DATOS - NEXOU")
        print("=" * 50)
        print("1. Frecuencia: Libro con más préstamos")
        print("2. Agrupar: Promedio de días de préstamo por editorial")
        print("3. Filtrar y contar: Préstamos retrasados")
        print("0. Volver al menú principal")
        print("-" * 50)
        opcion = input("Selecciona una opción: ")

        match opcion:

            case "1":
                # value_counts cuenta cuántas veces aparece cada libro
                frecuencia = df_completo["nom_libro"].value_counts()
                print(f"\nLIBRO CON MÁS PRÉSTAMOS: '{frecuencia.idxmax()}' con {frecuencia.max()} préstamos.")
                print("\nLos 5 libros más prestados:\n", frecuencia.head(5).to_string())

            case "2":
                # Agrupación (groupby)
                promedio = df_completo.groupby("editorial")["dias_prestamo"].mean().round(1)
                print("\nPROMEDIO DE DÍAS DE PRÉSTAMO POR EDITORIAL:\n", promedio.to_string())

            case "3":
                # Filtrado y conteo
                retrasados = df_completo[df_completo["estado_prestamo"] == "retrasado"]
                print(f"\nPRÉSTAMOS RETRASADOS: {len(retrasados)}")
                print(retrasados[["nombre_usuario", "nom_libro", "dias_prestamo"]].to_string(index=False))

            case "0":
                break

            case _:
                # El guión bajo '_' es el caso por defecto (como el 'else')
                print("Opción no válida.")

# -------------------------------------------------------
# MENÚ PRINCIPAL
# -------------------------------------------------------
cargado = False
limpio = False

while True:
    print("\n" + "=" * 50)
    print("   MENÚ PRINCIPAL - NEXOU")
    print("=" * 50)
    print("1. Cargar archivos")
    print("2. Limpieza")
    print("3. Análisis")
    print("4. Salir")
    print("-" * 50)
    opcion = input("Selecciona una opción: ")

    match opcion:

        case "1":
            df_usuarios = cargar_datos("data/raw/usuarios.csv")
            df_libros = cargar_datos("data/raw/libros.csv")
            df_equipos = cargar_datos("data/raw/equipos_tecnologicos.csv")
            df_prestamos = cargar_datos("data/raw/prestamos.csv")
            cargado = True
            limpio = False

        case "2" if cargado:
            print("\n--- Limpiando USUARIOS ---")
            df_usuarios = manejar_nulos(df_usuarios, ["id_usuario", "nombre_usuario", "correo"], {"programa": "sin programa"})
            df_usuarios = estandarizar_texto(df_usuarios, ["nombre_usuario", "programa"])
            df_usuarios = limpieza_especifica(df_usuarios)
            df_usuarios = eliminar_duplicados(df_usuarios, "correo")
            guardar_datos(df_usuarios, "data/processed/usuarios_limpio.csv")

            print("\n--- Limpiando LIBROS ---")
            df_libros = manejar_nulos(df_libros, ["id_libro", "nom_libro"], {"autor": "desconocido", "editorial": "sin editorial", "cantidad_disponible": 0})
            df_libros = estandarizar_texto(df_libros, ["nom_libro", "autor", "editorial"])
            df_libros = limpieza_especifica(df_libros)
            df_libros["cantidad_disponible"] = df_libros["cantidad_disponible"].astype(int)
            guardar_datos(df_libros, "data/processed/libros_limpio.csv")

            print("\n--- Limpiando EQUIPOS ---")
            df_equipos = manejar_nulos(df_equipos, ["nom_equipo"], {"marca": "sin marca", "estado_equipo": "sin estado", "cantidad_disponible": 0})
            df_equipos = estandarizar_texto(df_equipos, ["nom_equipo", "marca", "tipo_equipo", "estado_equipo"])
            df_equipos = limpieza_especifica(df_equipos)
            df_equipos["cantidad_disponible"] = df_equipos["cantidad_disponible"].astype(int)
            guardar_datos(df_equipos, "data/processed/equipos_limpio.csv")

            print("\n--- Limpiando PRÉSTAMOS ---")
            # Los días de préstamo faltantes se corrigen con la mediana de la columna
            mediana = df_prestamos["dias_prestamo"].median()
            df_prestamos = manejar_nulos(df_prestamos, ["id_usuario", "id_libro"], {"estado_prestamo": "sin estado", "dias_prestamo": mediana})
            df_prestamos = estandarizar_texto(df_prestamos, ["estado_prestamo"])
            df_prestamos = eliminar_duplicados(df_prestamos, "id_prestamo")
            guardar_datos(df_prestamos, "data/processed/prestamos_limpio.csv")

            # Combinación (merge): cada préstamo se une con su usuario y su libro
            print("\n--- Combinando PRÉSTAMOS + USUARIOS + LIBROS ---")
            df_completo = df_prestamos.merge(df_usuarios, on="id_usuario").merge(df_libros, on="id_libro")
            guardar_datos(df_completo, "data/processed/prestamos_completo.csv")
            limpio = True

        case "2":
            print("Primero carga los archivos (opción 1).")

        case "3" if limpio:
            menu_analisis()

        case "3":
            print("Primero limpia los datos (opción 2).")

        case "4":
            print("\n¡Hasta luego!")
            print(Style.RESET_ALL)  # Devuelve la consola a su color normal
            break

        case _:
            print("Opción no válida.")
