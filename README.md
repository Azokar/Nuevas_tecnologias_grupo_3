# NexoU - Análisis de datos de préstamos

Aplicación de análisis de datos en Python con Pandas para **NexoU**, un sistema de préstamo de libros y equipos tecnológicos para estudiantes. El proyecto carga los datos crudos en formato CSV, los limpia con un módulo de funciones propio y responde en la consola preguntas clave sobre los préstamos.

Proyecto del Grupo 3 de Nuevas Tecnologías (Momento 2).

## Estructura del proyecto

```
├── analisis.py          # Script principal: limpia, combina y responde las preguntas
├── limpieza.py          # Módulo con las funciones de limpieza
├── requirements.txt     # Dependencias del proyecto
├── data/
│   ├── raw/             # Datos crudos (con nulos, duplicados y texto inconsistente)
│   │   ├── usuarios.csv
│   │   ├── libros.csv
│   │   ├── prestamos.csv
│   │   └── equipos_tecnologicos.csv
│   └── processed/       # Datos limpios, generados al ejecutar analisis.py
└── README.md
```

## Datos

| Archivo | Registros | Contenido | Se relaciona con |
|---|---|---|---|
| `usuarios.csv` | 59 | Estudiantes registrados | `prestamos.csv` por `id_usuario` |
| `libros.csv` | 55 | Catálogo de libros | `prestamos.csv` por `id_libro` |
| `prestamos.csv` | 130 | Préstamos de libros a usuarios | `usuarios.csv` y `libros.csv` |
| `equipos_tecnologicos.csv` | 52 | Inventario de equipos | |

Los datos crudos traen problemas a propósito: valores nulos, registros duplicados, mayúsculas y minúsculas mezcladas, espacios extra e ISBN con guiones.

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

## Ejecución

Con el entorno virtual activado y desde la carpeta raíz del proyecto:

```bash
python analisis.py
```

El script abre un menú principal. Las opciones se usan en orden:

1. **Cargar archivos:** carga los CSV de `data/raw/` en DataFrames.
2. **Limpieza:** limpia cada tabla, combina (`merge`) los préstamos con sus usuarios y sus libros, y guarda el resultado en `data/processed/`.
3. **Análisis:** abre un submenú con una opción por cada pregunta de análisis. La `0` vuelve al menú principal.
4. **Salir.**

## Módulo de limpieza (`limpieza.py`)

| Función | Qué hace |
|---|---|
| `cargar_datos(ruta)` | Carga un CSV en un DataFrame |
| `manejar_nulos(df, columnas_clave, valores_relleno)` | Elimina las filas con nulos en las columnas clave y rellena los demás nulos |
| `estandarizar_texto(df, columnas_texto)` | Pasa el texto a minúsculas y quita los espacios extra |
| `limpieza_especifica(df)` | Normaliza correos, quita los guiones del ISBN y normaliza el estado de los equipos |
| `eliminar_duplicados(df, columna_unica)` | Elimina los registros repetidos |
| `guardar_datos(df, ruta_destino)` | Guarda el DataFrame limpio en un CSV |

## Preguntas de análisis

| Tipo | Pregunta |
|---|---|
| Frecuencia | ¿Cuál es el libro con la mayor cantidad de préstamos? |
| Agregación | ¿Cuál es el promedio de días de préstamo por editorial? |
| Filtrado y conteo | ¿Cuántos préstamos están en estado "retrasado"? |

## Conceptos clave

- **DataFrame:** es la estructura de datos principal de Pandas. Es una tabla de filas y columnas con nombre, parecida a una hoja de cálculo, que permite filtrar, agrupar y combinar datos con pocas líneas de código.
- **Entorno virtual:** es una carpeta con una instalación aislada de Python y sus librerías. Se usa para que las dependencias de este proyecto no se mezclen con las de otros proyectos ni con las del sistema, y para que todo el equipo trabaje con las mismas versiones (las de `requirements.txt`).

## Flujo de trabajo en Git

El repositorio sigue Git Flow: `main` tiene las versiones estables, `develop` es la base de trabajo, cada cambio se hace en una rama `feature/` que se fusiona en `develop` con un Pull Request, y las entregas se preparan en ramas `release/` (por ejemplo, `release/analisis-v1`).
