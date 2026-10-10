# NexoU - Análisis de datos de préstamos

Aplicación de análisis de datos en Python con Pandas para **NexoU**, un sistema de préstamo de libros y equipos tecnológicos para estudiantes. El proyecto carga los datos crudos en formato CSV, los limpia con un módulo de funciones propio y responde en la consola preguntas clave sobre los préstamos.

Proyecto del Grupo 3 de Nuevas Tecnologías (Momento 2).

## Estructura del proyecto

```
├── analisis.py          # Script principal: menú, limpieza, merge y preguntas de análisis
├── limpieza.py          # Módulo con las funciones de limpieza
├── requirements.txt     # Dependencias del proyecto
├── data/
│   ├── raw/             # Datos crudos (con nulos, duplicados y texto inconsistente)
│   │   ├── usuarios.csv
│   │   ├── libros.csv
│   │   ├── prestamos.csv
│   │   └── equipos_tecnologicos.csv
│   └── processed/       # Datos limpios, generados por la opción "Limpieza"
│       ├── usuarios_limpio.csv
│       ├── libros_limpio.csv
│       ├── equipos_limpio.csv
│       ├── prestamos_limpio.csv
│       └── prestamos_completo.csv
└── README.md
```

La carpeta `data/processed/` no está en el repositorio (está en `.gitignore`): se crea sola al ejecutar la limpieza.

## Datos

| Archivo | Registros | Contenido | Se relaciona con |
|---|---|---|---|
| `usuarios.csv` | 59 | Estudiantes registrados | `prestamos.csv` por `id_usuario` |
| `libros.csv` | 55 | Catálogo de libros | `prestamos.csv` por `id_libro` |
| `prestamos.csv` | 130 | Préstamos de libros a usuarios | `usuarios.csv` y `libros.csv` |
| `equipos_tecnologicos.csv` | 52 | Inventario de equipos | |

Los datos crudos traen problemas a propósito: valores nulos, registros duplicados, mayúsculas y minúsculas mezcladas, espacios extra e ISBN con guiones.

### Archivos generados en `data/processed/`

| Archivo | Registros | Contenido |
|---|---|---|
| `usuarios_limpio.csv` | 50 | Usuarios sin nulos en los campos clave y sin correos repetidos |
| `libros_limpio.csv` | 55 | Libros con texto estandarizado e ISBN sin guiones |
| `equipos_limpio.csv` | 52 | Equipos con texto y estado normalizados |
| `prestamos_limpio.csv` | 120 | Préstamos sin nulos en los campos clave y sin `id_prestamo` repetidos |
| `prestamos_completo.csv` | 112 | Cada préstamo unido con los datos de su usuario y de su libro |

`prestamos_completo.csv` tiene menos registros que `prestamos_limpio.csv` porque el `merge` solo conserva los préstamos cuyo usuario y libro siguen existiendo después de la limpieza.

## Configuración del entorno

Se necesita Python 3.10 o superior (el menú usa `match/case`).

1. Clonar el repositorio y entrar a la carpeta:

   ```bash
   git clone https://github.com/Azokar/Nuevas_tecnologias_grupo_3.git
   cd Nuevas_tecnologias_grupo_3
   ```

2. Crear el entorno virtual:

   ```bash
   python -m venv .venv
   ```

3. Activar el entorno virtual:

   ```bash
   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1

   # Windows (CMD)
   .venv\Scripts\activate.bat

   # Linux / macOS
   source .venv/bin/activate
   ```

4. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

   Las librerías que usa el código son **pandas** (carga, limpieza y análisis de los datos) y **colorama** (colores en la consola). El resto de `requirements.txt` son dependencias de pandas.

## Ejecución

Con el entorno virtual activado y desde la carpeta raíz del proyecto:

```bash
python analisis.py
```

El script abre un menú principal en la consola (el texto sale en color magenta gracias a `colorama`). Las opciones se usan en orden:

1. **Cargar archivos:** carga los cuatro CSV de `data/raw/` en DataFrames y muestra las filas y columnas de cada uno.
2. **Limpieza:** limpia cada tabla, combina (`merge`) los préstamos con sus usuarios y sus libros, y guarda los resultados en `data/processed/`.
3. **Análisis:** abre un submenú con una opción por cada pregunta de análisis. La `0` vuelve al menú principal.
4. **Salir:** cierra el programa y devuelve la consola a su color normal.

El menú valida el orden: si se elige **Limpieza** sin haber cargado los archivos, o **Análisis** sin haber limpiado, el programa avisa qué paso falta. Si se vuelven a cargar los archivos, hay que repetir la limpieza antes de analizar.

### Qué se limpia en cada tabla

| Tabla | Filas eliminadas si falta | Nulos rellenados | Texto estandarizado | Otros pasos |
|---|---|---|---|---|
| Usuarios | `id_usuario`, `nombre_usuario` o `correo` | `programa` → `sin programa` | `nombre_usuario`, `programa` | Normaliza `correo` y elimina duplicados por `correo` |
| Libros | `id_libro` o `nom_libro` | `autor` → `desconocido`, `editorial` → `sin editorial`, `cantidad_disponible` → `0` | `nom_libro`, `autor`, `editorial` | Quita los guiones del `isbn` y convierte `cantidad_disponible` a entero |
| Equipos | `nom_equipo` | `marca` → `sin marca`, `estado_equipo` → `sin estado`, `cantidad_disponible` → `0` | `nom_equipo`, `marca`, `tipo_equipo`, `estado_equipo` | Convierte `cantidad_disponible` a entero |
| Préstamos | `id_usuario` o `id_libro` | `estado_prestamo` → `sin estado`, `dias_prestamo` → mediana de la columna | `estado_prestamo` | Elimina duplicados por `id_prestamo` |

Al final, los préstamos limpios se unen con los usuarios (por `id_usuario`) y con los libros (por `id_libro`) en un solo DataFrame, que es el que usan las preguntas de análisis.

## Módulo de limpieza (`limpieza.py`)

| Función | Qué hace |
|---|---|
| `cargar_datos(ruta)` | Carga un CSV en un DataFrame y muestra cuántas filas y columnas tiene |
| `manejar_nulos(df, columnas_clave, valores_relleno=None)` | Muestra los nulos por columna, elimina las filas con nulos en las columnas clave y rellena los demás con los valores indicados |
| `estandarizar_texto(df, columnas_texto)` | Pasa el texto a minúsculas y quita los espacios al inicio y al final |
| `limpieza_especifica(df)` | Normaliza `correo`, quita los guiones de `isbn` y normaliza `estado_equipo` (solo en las columnas que existan en la tabla) |
| `eliminar_duplicados(df, columna_unica)` | Elimina las filas con el mismo valor en la columna indicada e informa cuántas quitó |
| `guardar_datos(df, ruta_destino)` | Guarda el DataFrame en un CSV y crea la carpeta de destino si no existe |

Cada función imprime en la consola lo que hizo, para poder seguir el proceso paso a paso.

## Preguntas de análisis

| Opción | Tipo | Pregunta | Cómo se responde |
|---|---|---|---|
| 1 | Frecuencia | ¿Cuál es el libro con la mayor cantidad de préstamos? | `value_counts()` sobre `nom_libro`; muestra el primero y los 5 más prestados |
| 2 | Agregación | ¿Cuál es el promedio de días de préstamo por editorial? | `groupby("editorial")` y promedio de `dias_prestamo` |
| 3 | Filtrado y conteo | ¿Cuántos préstamos están en estado "retrasado"? | Filtro por `estado_prestamo`; muestra el total y la lista con usuario, libro y días |

Con los datos actuales, el libro más prestado es *Harry Potter y la piedra filosofal* (10 préstamos) y hay 16 préstamos retrasados.

## Conceptos clave

- **DataFrame:** es la estructura de datos principal de Pandas. Es una tabla de filas y columnas con nombre, parecida a una hoja de cálculo, que permite filtrar, agrupar y combinar datos con pocas líneas de código.
- **Entorno virtual:** es una carpeta con una instalación aislada de Python y sus librerías. Se usa para que las dependencias de este proyecto no se mezclen con las de otros proyectos ni con las del sistema, y para que todo el equipo trabaje con las mismas versiones (las de `requirements.txt`).

## Flujo de trabajo en Git

El repositorio sigue Git Flow: `main` tiene las versiones estables, `develop` es la base de trabajo, cada cambio se hace en una rama `feature/` que se fusiona en `develop` con un Pull Request, y las entregas se preparan en ramas `release/` (por ejemplo, `release/analisis-v1`).
