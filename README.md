# NexoU — Análisis de datos de préstamos

Proyecto del **Grupo 3 de Nuevas Tecnologías**. Analiza con **Python y pandas** los préstamos de **NexoU** (también llamado EduLoan),
una plataforma sin ánimo de lucro para prestar libros y equipos tecnológicos a estudiantes.

El repositorio tiene dos partes que comparten el mismo dominio pero trabajan con datos distintos:

| Parte | Carpeta | Qué hace | Fuente de datos | Cómo se usa |
|---|---|---|---|---|
| **1. Análisis en consola** (Momento 2) | raíz (`analisis.py`, `limpieza.py`) | Carga CSV crudos, los limpia, los combina y responde 3 preguntas | Archivos de `data/raw/` | Menú interactivo en la terminal |
| **2. Servicio de analítica** | `analitica/` | Calcula métricas, rankings, series de tiempo y hallazgos sobre los préstamos reales | API Java de NexoU (en vivo) | API REST con FastAPI, consumida por el panel del administrador |

La parte 1 enseña el proceso completo de limpieza con datos de ejemplo. La parte 2 lleva ese mismo trabajo con pandas
a producción: se conecta a la plataforma real y alimenta las gráficas del panel de estadísticas.

---

## Estructura del proyecto

```
├── analisis.py              # Parte 1: menú principal, limpieza, merge y preguntas de análisis
├── limpieza.py              # Parte 1: funciones de limpieza reutilizables
├── requirements.txt         # Dependencias de la parte 1
├── data/
│   ├── raw/                 # Datos crudos (con nulos, duplicados y texto inconsistente)
│   │   ├── usuarios.csv
│   │   ├── libros.csv
│   │   ├── prestamos.csv
│   │   └── equipos_tecnologicos.csv
│   └── processed/           # Datos limpios, se generan al ejecutar la limpieza (no se suben)
├── analitica/
│   ├── servicio.py          # Parte 2: microservicio FastAPI + pandas
│   └── requirements.txt     # Dependencias de la parte 2
└── README.md
```

`data/processed/` está en `.gitignore`: la crea el propio programa.

## Arquitectura general de NexoU

El servicio de analítica es una pieza de una plataforma más grande:

```
Navegador ──> Frontend React (Vercel) ──> API Java Spring Boot (Render) ──> PostgreSQL (Neon)
                        │
                        └──> Servicio de analítica Python (Render) ──> pide los datos a la API Java
```

- **API Java** ([nexou-api](https://github.com/SantiagoMJaramillo/nexou-api)): usuarios, catálogo, reservas y seguridad con JWT (roles `ADMIN` y `USER`).
- **Servicio de analítica** (este repositorio, `analitica/`): no tiene base de datos propia. Por cada petición reenvía el token del
  administrador a la API Java, descarga reservas e inventario, los procesa con pandas y devuelve las métricas ya calculadas.
- **Frontend**: dibuja las gráficas interactivas con la respuesta del servicio.

---

## Requisitos

- **Python 3.10 o superior.** La parte 1 usa `match/case`; la parte 2 usa anotaciones como `str | None`.
- Git.

Se recomienda **un entorno virtual por parte**, porque cada una fija su propia versión de pandas:
la parte 1 usa `pandas 3.0.6` y la parte 2 usa `pandas 3.1.1`.

```bash
git clone https://github.com/Azokar/Nuevas_tecnologias_grupo_3.git
cd Nuevas_tecnologias_grupo_3
```

Activar un entorno virtual creado con `python -m venv <carpeta>`:

```bash
# Windows (PowerShell)
<carpeta>\Scripts\Activate.ps1
# Windows (CMD)
<carpeta>\Scripts\activate.bat
# Linux / macOS
source <carpeta>/bin/activate
```

---

## Parte 1 — Análisis en consola

### Instalación y ejecución

```bash
python -m venv .venv
# activar .venv (ver arriba)
pip install -r requirements.txt
python analisis.py
```

Las librerías que usa el código son **pandas** (carga, limpieza y análisis) y **colorama** (texto en color magenta en la consola).
El resto de `requirements.txt` son dependencias de pandas.

### Menú

| Opción | Qué hace |
|---|---|
| 1. Cargar archivos | Carga los cuatro CSV de `data/raw/` y muestra filas y columnas de cada uno |
| 2. Limpieza | Limpia cada tabla, une préstamos con usuarios y libros (`merge`) y guarda todo en `data/processed/` |
| 3. Análisis | Abre el submenú de preguntas (la `0` vuelve al menú principal) |
| 4. Salir | Cierra el programa y restablece el color de la consola |

El menú obliga a seguir el orden: si se pide **Limpieza** sin cargar o **Análisis** sin limpiar, avisa qué paso falta.
Si se vuelven a cargar los archivos, hay que repetir la limpieza antes de analizar.

### Datos

| Archivo crudo | Registros | Contenido | Se relaciona con |
|---|---|---|---|
| `usuarios.csv` | 59 | Estudiantes registrados | `prestamos.csv` por `id_usuario` |
| `libros.csv` | 55 | Catálogo de libros | `prestamos.csv` por `id_libro` |
| `prestamos.csv` | 130 | Préstamos de libros | `usuarios.csv` y `libros.csv` |
| `equipos_tecnologicos.csv` | 52 | Inventario de equipos | — |

Los datos traen problemas a propósito: nulos, duplicados, mayúsculas mezcladas, espacios sobrantes e ISBN con guiones.

| Archivo generado | Registros | Contenido |
|---|---|---|
| `usuarios_limpio.csv` | 50 | Sin nulos en campos clave ni correos repetidos |
| `libros_limpio.csv` | 55 | Texto estandarizado e ISBN sin guiones |
| `equipos_limpio.csv` | 52 | Texto y estado normalizados |
| `prestamos_limpio.csv` | 120 | Sin nulos en campos clave ni `id_prestamo` repetidos |
| `prestamos_completo.csv` | 112 | Cada préstamo unido con su usuario y su libro |

`prestamos_completo.csv` tiene menos filas que `prestamos_limpio.csv` porque el `merge` solo conserva los préstamos
cuyo usuario y libro siguen existiendo después de la limpieza.

### Qué se limpia en cada tabla

| Tabla | Se elimina la fila si falta | Nulos rellenados | Texto estandarizado | Otros pasos |
|---|---|---|---|---|
| Usuarios | `id_usuario`, `nombre_usuario` o `correo` | `programa` → `sin programa` | `nombre_usuario`, `programa` | Normaliza `correo` y quita duplicados por `correo` |
| Libros | `id_libro` o `nom_libro` | `autor` → `desconocido`, `editorial` → `sin editorial`, `cantidad_disponible` → `0` | `nom_libro`, `autor`, `editorial` | Quita guiones del `isbn`; `cantidad_disponible` a entero |
| Equipos | `nom_equipo` | `marca` → `sin marca`, `estado_equipo` → `sin estado`, `cantidad_disponible` → `0` | `nom_equipo`, `marca`, `tipo_equipo`, `estado_equipo` | `cantidad_disponible` a entero |
| Préstamos | `id_usuario` o `id_libro` | `estado_prestamo` → `sin estado`, `dias_prestamo` → mediana | `estado_prestamo` | Quita duplicados por `id_prestamo` |

### Módulo `limpieza.py`

| Función | Qué hace |
|---|---|
| `cargar_datos(ruta)` | Carga un CSV y muestra cuántas filas y columnas tiene |
| `manejar_nulos(df, columnas_clave, valores_relleno=None)` | Muestra los nulos, elimina filas con nulos en columnas clave y rellena el resto |
| `estandarizar_texto(df, columnas_texto)` | Minúsculas y sin espacios al inicio ni al final |
| `limpieza_especifica(df)` | Normaliza `correo`, quita guiones de `isbn` y normaliza `estado_equipo` (si existen) |
| `eliminar_duplicados(df, columna_unica)` | Elimina filas repetidas por esa columna e informa cuántas |
| `guardar_datos(df, ruta_destino)` | Guarda el CSV y crea la carpeta si no existe |

### Preguntas de análisis

| Opción | Tipo | Pregunta | Cómo se responde | Resultado con los datos actuales |
|---|---|---|---|---|
| 1 | Frecuencia | ¿Qué libro tiene más préstamos? | `value_counts()` sobre `nom_libro` (muestra el top 5) | *Harry Potter y la piedra filosofal*, 10 préstamos |
| 2 | Agregación | ¿Cuál es el promedio de días de préstamo por editorial? | `groupby("editorial")["dias_prestamo"].mean()` | Tabla por editorial |
| 3 | Filtrado y conteo | ¿Cuántos préstamos están retrasados? | Filtro `estado_prestamo == "retrasado"` | 16 préstamos |

---

## Parte 2 — Servicio de analítica (`analitica/`)

Microservicio **FastAPI + pandas** que responde las preguntas del administrador de NexoU sobre los préstamos reales:
qué se presta más, quién devuelve tarde, qué semestres usan más el servicio y qué artículos no se mueven.

### Cómo funciona

1. El frontend llama a `GET /analitica` con el header `Authorization: Bearer <token>` del administrador.
2. El servicio reenvía ese token a la API Java y descarga `/api/reservas-libros`, `/api/reservas-equipos`, `/api/libros` y `/api/equipos`.
   Esas rutas son solo para `ADMIN`: si el token no es de un administrador, la API responde 403 y el servicio devuelve el mismo error.
3. Con pandas une libros y equipos en un solo DataFrame (una fila por reserva), convierte fechas y calcula retrasos.
4. Aplica los filtros pedidos y devuelve todas las métricas en una sola respuesta JSON.

**Reglas de cálculo de retrasos:**

- Libros: el límite es el final del día de entrega esperada y la devolución se toma al mediodía; devolver el mismo día no cuenta como tarde.
- Equipos: el límite es `horaFin` de la reserva (se prestan por horas).
- Un préstamo es **tardío** si se devolvió después del límite o si sigue `ACTIVA` con el límite vencido (**en mora**).
- Los retrasos de menos de un día se expresan en horas.

### Instalación y ejecución local

```bash
cd analitica
python -m venv .venv
# activar .venv (ver arriba)
pip install -r requirements.txt
uvicorn servicio:app --reload --port 8000
```

Necesita la API Java corriendo (por defecto en `http://localhost:8080`). La documentación interactiva queda en
`http://localhost:8000/docs`.

### Variables de entorno

| Variable | Por defecto | Para qué sirve |
|---|---|---|
| `NEXOU_API_URL` | `http://localhost:8080` | URL base de la API Java |
| `CORS_ORIGENES` | `*` | Orígenes del frontend permitidos, separados por coma (`*` solo en desarrollo) |
| `APP_TIMEZONE` | `America/Bogota` | Zona horaria para decidir qué préstamos están en mora |

El servicio no guarda secretos: solo reenvía el token que recibe.

### Endpoints

| Método y ruta | Descripción |
|---|---|
| `GET /health` | Estado del servicio: `{"estado": "ok", "servicio": "nexou-analitica"}` |
| `GET /analitica` | Todas las métricas con los filtros aplicados (requiere token de `ADMIN`) |

**Filtros de `/analitica`** (todos opcionales, por query string):

| Parámetro | Valores |
|---|---|
| `desde`, `hasta` | Fecha del préstamo, `AAAA-MM-DD` |
| `tipo` | `Libro` o `Equipo` |
| `semestre` | `1` a `12`, o `sin-dato` |
| `programa` | Nombre del programa académico |
| `categoria` | Categoría del libro o tipo de equipo |
| `estado` | `ACTIVA`, `DEVUELTO`, `VENCIDO`, `CANCELADA` o `TARDIO` (con retraso) |
| `granularidad` | `dia`, `semana` o `mes` (por defecto `mes`) para la serie de tiempo |

Ejemplo: `GET /analitica?tipo=Libro&desde=2026-08-01&granularidad=semana`

### Qué devuelve

| Campo | Contenido |
|---|---|
| `resumen` | Totales: préstamos, activos, devueltos, tardíos, en mora, % de tardíos, días promedio de retraso, duración promedio y usuarios distintos |
| `hallazgos` | Frases listas para mostrar: artículo más alquilado, más devuelto tarde, semestre que más pide, datos incompletos, puntualidad, categoría y día más activos, artículos sin movimiento |
| `ranking_articulos` | Top 8 de artículos más prestados |
| `retrasos_por_articulo` | Top 8 de artículos con más devoluciones tardías y su retraso promedio |
| `por_semestre` | Préstamos, personas, tardíos y promedio por persona en cada semestre |
| `por_programa` | Top 8 de programas académicos |
| `por_categoria` | Top 8 de categorías (un libro con varias categorías cuenta en cada una) |
| `dia_semana` | Préstamos por día de la semana |
| `usuarios_retrasos` | Top 6 de usuarios con más retrasos |
| `estados` | Conteo por estado de la reserva |
| `puntualidad` | A tiempo frente a con retraso |
| `serie_tiempo` | Préstamos de libros y equipos por periodo, sin huecos en el eje |
| `sin_movimiento` | Artículos del inventario que no se prestaron en el periodo |
| `filtros_disponibles` | Opciones válidas para llenar los filtros del panel |

### Errores

| Código | Cuándo |
|---|---|
| 401 | Falta el token o la API lo rechaza |
| 403 | El token no es de un administrador |
| 400 | Un filtro tiene un valor inválido (por ejemplo, un semestre que no es número) |
| 422 | Un parámetro no cumple el formato (fecha mal escrita o granularidad desconocida) |
| 502 | La API Java no responde o devuelve un error |

### Despliegue

Se despliega en Render como servicio web de Python:

- Directorio raíz: `analitica`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn servicio:app --host 0.0.0.0 --port $PORT`
- Variables: `NEXOU_API_URL` (URL pública de la API Java) y `CORS_ORIGENES` (URL del frontend)

En el plan gratuito de Render los servicios se duermen; por eso el servicio espera hasta 60 segundos a la API Java en la primera petición.

---

## Conceptos clave

- **DataFrame:** la estructura principal de pandas. Es una tabla con filas y columnas con nombre, parecida a una hoja de cálculo,
  que permite filtrar, agrupar y combinar datos con pocas líneas de código.
- **Entorno virtual:** una instalación aislada de Python y sus librerías. Evita que las dependencias de un proyecto se mezclen con
  las de otros y garantiza que todo el equipo use las mismas versiones.
- **Microservicio:** un programa pequeño con una sola responsabilidad (aquí, calcular estadísticas) que se comunica con los demás
  por HTTP. Así la analítica en Python puede evolucionar sin tocar la API Java.

## Flujo de trabajo en Git

El repositorio sigue Git Flow:

- `main`: versiones estables.
- `develop`: base de trabajo.
- `feature/...`: cada cambio; se integra a `develop` con un Pull Request.
- `release/...`: preparación de entregas (por ejemplo, `release/analisis-v1`).

Los commits siguen Conventional Commits en español (`feat(analitica): ...`, `docs: ...`).
