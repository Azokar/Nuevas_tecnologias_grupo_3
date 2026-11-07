"""
Microservicio de analítica de NEXOU (FastAPI + pandas).

No tiene base de datos propia: cada petición reenvía el token (JWT) del administrador a la API
de Java, descarga las reservas y el inventario, aplica los filtros con pandas y devuelve las
métricas ya calculadas. El navegador dibuja las gráficas (interactivas) con estos datos.
Si el token no es de un ADMIN, la API responde 403 y este servicio devuelve el mismo error.

Ejecutar en local:  uvicorn servicio:app --reload --port 8000
"""
import json
import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

API_URL = os.getenv("NEXOU_API_URL", "http://localhost:8080").rstrip("/")
ORIGENES = [o.strip() for o in os.getenv("CORS_ORIGENES", "*").split(",") if o.strip()]
ZONA = ZoneInfo(os.getenv("APP_TIMEZONE", "America/Bogota"))

SIN_DATO = "Sin dato"
DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
ETIQUETA_ESTADO = {"ACTIVA": "Activa", "DEVUELTO": "Devuelto", "VENCIDO": "Vencido", "CANCELADA": "Cancelada"}

app = FastAPI(title="NEXOU - Servicio de analítica", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=ORIGENES, allow_methods=["GET"], allow_headers=["*"])


# -------------------------------------------------------
# Acceso a la API de Java
# -------------------------------------------------------
def traer(ruta: str, autorizacion: str | None) -> list[dict]:
    """Descarga una lista de la API usando el token que mandó el frontend."""
    if not autorizacion:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión")
    try:
        # timeout alto: el plan gratuito de Render tarda en "despertar" la API
        respuesta = httpx.get(f"{API_URL}{ruta}", headers={"Authorization": autorizacion}, timeout=60)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="No se pudo conectar con la API de NEXOU")
    if respuesta.status_code in (401, 403):
        raise HTTPException(status_code=respuesta.status_code, detail="Solo un administrador puede ver las estadísticas")
    if respuesta.status_code != 200:
        raise HTTPException(status_code=502, detail=f"La API respondió {respuesta.status_code}")
    return respuesta.json()


def cargar_datos(autorizacion: str | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (reservas, inventario). Una fila por reserva, libros y equipos juntos."""
    reservas_libros = traer("/api/reservas-libros", autorizacion)
    reservas_equipos = traer("/api/reservas-equipos", autorizacion)
    libros = traer("/api/libros", autorizacion)
    equipos = traer("/api/equipos", autorizacion)

    categorias_libro = {l["id"]: [c["nombre"] for c in l["categorias"]] or ["Sin categoría"] for l in libros}
    categorias_equipo = {e["id"]: [e["tipoEquipo"] or "Equipo"] for e in equipos}

    filas = []
    for r in reservas_libros:
        # La API guarda solo el día: se toma el final del día límite y el mediodía de la devolución,
        # así una devolución el mismo día no cuenta como tarde.
        limite = f"{r['fechaEntregaEsperada']}T23:59:59" if r.get("fechaEntregaEsperada") else None
        real = f"{r['fechaDevolucionReal']}T12:00:00" if r.get("fechaDevolucionReal") else None
        filas.append({
            "tipo": "Libro", "id": r["id"], "articulo_id": r["libroId"], "articulo": r["libro"],
            "usuario": r["usuario"], "semestre": r.get("usuarioSemestre"), "programa": r.get("usuarioPrograma"),
            "estado": r["estadoReserva"], "fecha": r.get("fechaCreacion"), "limite": limite, "real": real,
            "categorias": categorias_libro.get(r["libroId"], ["Sin categoría"]),
        })
    for r in reservas_equipos:
        filas.append({
            "tipo": "Equipo", "id": r["id"], "articulo_id": r["equipoId"], "articulo": r["equipo"],
            "usuario": r["usuario"], "semestre": r.get("usuarioSemestre"), "programa": r.get("usuarioPrograma"),
            "estado": r["estadoReserva"], "fecha": r.get("fechaCreacion"), "limite": r.get("horaFin"),
            "real": r.get("fechaDevolucionReal"),
            "categorias": categorias_equipo.get(r["equipoId"], ["Equipo"]),
        })

    columnas = ["tipo", "id", "articulo_id", "articulo", "usuario", "semestre", "programa", "estado",
                "fecha", "limite", "real", "categorias"]
    df = pd.DataFrame(filas, columns=columnas)
    for col in ("fecha", "limite", "real"):
        # ISO8601: la API mezcla fechas con y sin microsegundos; pandas 3 infiere un solo formato y descartaría el resto
        df[col] = pd.to_datetime(df[col], format="ISO8601", errors="coerce")
    df["semestre"] = pd.to_numeric(df["semestre"], errors="coerce")
    df["programa"] = df["programa"].fillna(SIN_DATO)
    df["semestre_etiqueta"] = df["semestre"].apply(lambda v: SIN_DATO if pd.isna(v) else str(int(v)))

    # --- Retrasos ---
    ahora = datetime.now(ZONA).replace(tzinfo=None)
    devuelto_con_fecha = (df["estado"] == "DEVUELTO") & df["real"].notna()
    en_mora = (df["estado"] == "ACTIVA") & (df["limite"] < ahora)
    df["en_mora"] = en_mora
    df["tarde"] = (devuelto_con_fecha & (df["real"] > df["limite"])) | en_mora
    # "evaluable": se puede saber si fue puntual (ya devuelto con fecha, o todavía en curso)
    df["evaluable"] = devuelto_con_fecha | (df["estado"] == "ACTIVA")
    momento = df["real"].where(devuelto_con_fecha, ahora)
    df["retraso_dias"] = ((momento - df["limite"]).dt.total_seconds() / 86400).clip(lower=0).where(df["tarde"])
    df["duracion_dias"] = ((df["real"] - df["fecha"]).dt.total_seconds() / 86400).where(devuelto_con_fecha)

    inventario = pd.DataFrame(
        [{"tipo": "Libro", "id": l["id"], "etiqueta": l["nomLibro"], "total": l["cantidadTotal"],
          "disponibles": l["cantidadDisponible"], "categorias": categorias_libro[l["id"]]} for l in libros]
        + [{"tipo": "Equipo", "id": e["id"], "etiqueta": e["nomEquipo"], "total": e["cantidadTotal"],
            "disponibles": e["cantidadDisponible"], "categorias": categorias_equipo[e["id"]]} for e in equipos],
        columns=["tipo", "id", "etiqueta", "total", "disponibles", "categorias"],
    )
    return df, inventario


# -------------------------------------------------------
# Filtros
# -------------------------------------------------------
def aplicar_filtros(df: pd.DataFrame, desde, hasta, tipo, semestre, programa, categoria, estado) -> pd.DataFrame:
    if desde:
        df = df[df["fecha"] >= pd.Timestamp(desde)]
    if hasta:
        df = df[df["fecha"] < pd.Timestamp(hasta) + timedelta(days=1)]
    if tipo in ("Libro", "Equipo"):
        df = df[df["tipo"] == tipo]
    if semestre:
        df = df[df["semestre"].isna()] if semestre == "sin-dato" else df[df["semestre"] == int(semestre)]
    if programa:
        df = df[df["programa"] == programa]
    if categoria:
        df = df[df["categorias"].apply(lambda lista: categoria in lista)]
    if estado == "TARDIO":
        df = df[df["tarde"]]
    elif estado in ETIQUETA_ESTADO:
        df = df[df["estado"] == estado]
    return df


def a_lista(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> lista de diccionarios con tipos nativos (NaN pasa a null)."""
    return json.loads(df.to_json(orient="records"))


def redondear(valor, decimales=1):
    return None if pd.isna(valor) else round(float(valor), decimales)


# -------------------------------------------------------
# Métricas
# -------------------------------------------------------
def calcular_resumen(df: pd.DataFrame) -> dict:
    evaluables = int(df["evaluable"].sum())
    tardios = int(df["tarde"].sum())
    return {
        "total": int(len(df)),
        "activos": int((df["estado"] == "ACTIVA").sum()),
        "devueltos": int((df["estado"] == "DEVUELTO").sum()),
        "tardios": tardios,
        "en_mora": int(df["en_mora"].sum()),
        "porcentaje_tardios": redondear(tardios / evaluables * 100) if evaluables else None,
        "dias_promedio_retraso": redondear(df["retraso_dias"].mean()),
        "duracion_promedio_dias": redondear(df["duracion_dias"].mean()),
        "usuarios": int(df["usuario"].nunique()),
    }


def ranking_articulos(df: pd.DataFrame, top: int) -> list[dict]:
    if df.empty:
        return []
    r = df.groupby(["tipo", "articulo"]).size().reset_index(name="valor")
    r = r.sort_values(["valor", "articulo"], ascending=[False, True]).head(top)
    return a_lista(r.rename(columns={"articulo": "etiqueta"}))


def retrasos_por_articulo(df: pd.DataFrame, top: int) -> list[dict]:
    tarde = df[df["tarde"]]
    if tarde.empty:
        return []
    totales = df.groupby(["tipo", "articulo"]).size().rename("total")
    r = tarde.groupby(["tipo", "articulo"]).agg(valor=("id", "size"), promedio_dias=("retraso_dias", "mean"))
    r = r.join(totales).reset_index()
    r["promedio_dias"] = r["promedio_dias"].round(1)
    r = r.sort_values(["valor", "promedio_dias"], ascending=[False, False]).head(top)
    return a_lista(r.rename(columns={"articulo": "etiqueta"}))


def por_semestre(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    g = df.groupby("semestre_etiqueta").agg(
        prestamos=("id", "size"), personas=("usuario", "nunique"), tardios=("tarde", "sum"))
    g["promedio_por_persona"] = (g["prestamos"] / g["personas"]).round(1)
    g = g.reset_index().rename(columns={"semestre_etiqueta": "etiqueta"})
    # Semestres en orden numérico y "Sin dato" al final
    g["orden"] = g["etiqueta"].apply(lambda e: 99 if e == SIN_DATO else int(e))
    g = g.sort_values("orden").drop(columns="orden")
    g["tardios"] = g["tardios"].astype(int)
    return a_lista(g)


def por_programa(df: pd.DataFrame, top: int) -> list[dict]:
    if df.empty:
        return []
    g = df.groupby("programa").agg(valor=("id", "size"), personas=("usuario", "nunique")).reset_index()
    g = g.sort_values(["valor", "programa"], ascending=[False, True]).head(top)
    return a_lista(g.rename(columns={"programa": "etiqueta"}))


def por_categoria(df: pd.DataFrame, top: int) -> list[dict]:
    if df.empty:
        return []
    explotado = df.explode("categorias")
    g = explotado.groupby("categorias").size().reset_index(name="valor")
    g = g.sort_values(["valor", "categorias"], ascending=[False, True]).head(top)
    return a_lista(g.rename(columns={"categorias": "etiqueta"}))


def dia_semana(df: pd.DataFrame) -> list[dict]:
    conteo = df["fecha"].dropna().dt.dayofweek.value_counts() if not df.empty else pd.Series(dtype=int)
    return [{"etiqueta": nombre, "valor": int(conteo.get(i, 0))} for i, nombre in enumerate(DIAS_SEMANA)]


def usuarios_con_retrasos(df: pd.DataFrame, top: int) -> list[dict]:
    tarde = df[df["tarde"]]
    if tarde.empty:
        return []
    g = tarde.groupby("usuario").agg(valor=("id", "size"), semestre=("semestre_etiqueta", "first")).reset_index()
    g = g.sort_values(["valor", "usuario"], ascending=[False, True]).head(top)
    return a_lista(g.rename(columns={"usuario": "etiqueta"}))


def estados(df: pd.DataFrame) -> list[dict]:
    conteo = df["estado"].value_counts()
    return [{"etiqueta": ETIQUETA_ESTADO[e], "valor": int(conteo.get(e, 0)), "clave": e} for e in ETIQUETA_ESTADO]


def puntualidad(df: pd.DataFrame) -> list[dict]:
    evaluables = df[df["evaluable"]]
    tarde = int(evaluables["tarde"].sum())
    return [{"etiqueta": "A tiempo", "valor": int(len(evaluables) - tarde)}, {"etiqueta": "Con retraso", "valor": tarde}]


def serie_tiempo(df: pd.DataFrame, granularidad: str) -> list[dict]:
    datos = df.dropna(subset=["fecha"])
    if datos.empty:
        return []
    f = datos["fecha"].dt.normalize()
    if granularidad == "semana":
        periodo = f - pd.to_timedelta(f.dt.dayofweek, unit="D")
        paso = pd.DateOffset(days=7)
    elif granularidad == "mes":
        periodo = f.dt.to_period("M").dt.to_timestamp()
        paso = pd.DateOffset(months=1)
    else:
        periodo, paso = f, pd.DateOffset(days=1)

    tabla = datos.assign(periodo=periodo).groupby(["periodo", "tipo"]).size().unstack(fill_value=0)
    # Se rellenan los periodos vacíos con 0 para que el eje del tiempo sea continuo
    inicio, fin, todos = tabla.index.min(), tabla.index.max(), []
    actual = inicio
    while actual <= fin and len(todos) < 400:
        todos.append(actual)
        actual = actual + paso
    tabla = tabla.reindex(todos, fill_value=0)

    def etiqueta(p: pd.Timestamp) -> str:
        if granularidad == "mes":
            return f"{MESES[p.month - 1]} {p.year}"
        return f"{p.day} {MESES[p.month - 1]}"

    return [{"periodo": p.strftime("%Y-%m-%d"), "etiqueta": etiqueta(p),
             "libros": int(fila.get("Libro", 0)), "equipos": int(fila.get("Equipo", 0))}
            for p, fila in tabla.iterrows()]


def sin_movimiento(df: pd.DataFrame, inventario: pd.DataFrame, tipo, categoria, top: int) -> list[dict]:
    inv = inventario
    if tipo in ("Libro", "Equipo"):
        inv = inv[inv["tipo"] == tipo]
    if categoria:
        inv = inv[inv["categorias"].apply(lambda lista: categoria in lista)]
    prestados = set(zip(df["tipo"], df["articulo_id"]))
    quietos = inv[[(t, i) not in prestados for t, i in zip(inv["tipo"], inv["id"])]]
    return a_lista(quietos[["etiqueta", "tipo", "disponibles", "total"]].head(top))


def formatear_retraso(dias) -> str:
    """Los retrasos de menos de un día se dicen en horas (un equipo se presta por horas)."""
    if dias is None:
        return "—"
    return f"{max(1, round(dias * 24))} h" if dias < 1 else f"{dias} días"


def hallazgos(resumen, ranking, retrasos, semestres, categorias, dias, quietos) -> list[dict]:
    """Frases listas para mostrar: responden las preguntas más frecuentes del administrador."""
    textos = []
    if ranking:
        top = ranking[0]
        textos.append({"titulo": "Artículo más alquilado",
                       "texto": f"{top['etiqueta']} ({top['tipo'].lower()}) con {top['valor']} préstamos."})
    if retrasos:
        top = retrasos[0]
        textos.append({"titulo": "Más devuelto con retraso",
                       "texto": f"{top['etiqueta']}: {top['valor']} de {top['total']} préstamos fuera de plazo"
                                f" (retraso promedio {formatear_retraso(top['promedio_dias'])})."})
    elif resumen["total"]:
        textos.append({"titulo": "Devoluciones", "texto": "No hay devoluciones con retraso en este periodo."})
    con_dato = [s for s in semestres if s["etiqueta"] != SIN_DATO]
    if con_dato:
        mas = max(con_dato, key=lambda s: s["prestamos"])
        mejor_promedio = max(con_dato, key=lambda s: s["promedio_por_persona"])
        texto = f"El semestre {mas['etiqueta']} concentra más préstamos ({mas['prestamos']})."
        if mejor_promedio["etiqueta"] != mas["etiqueta"]:
            texto += (f" Por persona, quienes más piden son los del semestre {mejor_promedio['etiqueta']}"
                      f" ({mejor_promedio['promedio_por_persona']} cada una).")
        textos.append({"titulo": "Semestre que más alquila", "texto": texto})
    sin_semestre = next((s for s in semestres if s["etiqueta"] == SIN_DATO), None)
    if sin_semestre and resumen["total"]:
        textos.append({"titulo": "Datos incompletos",
                       "texto": f"{sin_semestre['prestamos']} préstamos son de personas que no han indicado su semestre."
                                " Pídeles completar su perfil para mejorar este análisis."})
    if resumen["porcentaje_tardios"] is not None:
        textos.append({"titulo": "Puntualidad",
                       "texto": f"{resumen['porcentaje_tardios']}% de los préstamos se devolvió fuera de plazo o sigue en mora"
                                f" ({resumen['en_mora']} activos vencidos ahora)."})
    if categorias:
        textos.append({"titulo": "Categoría más pedida", "texto": f"{categorias[0]['etiqueta']} ({categorias[0]['valor']} préstamos)."})
    if resumen["total"] and max(d["valor"] for d in dias) > 0:
        dia = max(dias, key=lambda d: d["valor"])
        textos.append({"titulo": "Día más activo", "texto": f"Los {dia['etiqueta'].lower()} se hacen más préstamos ({dia['valor']})."})
    if quietos:
        textos.append({"titulo": "Sin movimiento",
                       "texto": f"{len(quietos)} artículos no se han prestado en este periodo: considera difundirlos o revisar su compra."})
    return textos


def opciones_de_filtro(df: pd.DataFrame, inventario: pd.DataFrame) -> dict:
    semestres = sorted(int(s) for s in df["semestre"].dropna().unique())
    categorias = sorted({c for lista in inventario["categorias"] for c in lista})
    programas = sorted(p for p in df["programa"].unique() if p != SIN_DATO)
    return {
        "semestres": [str(s) for s in semestres] + (["sin-dato"] if df["semestre"].isna().any() else []),
        "programas": programas + ([SIN_DATO] if (df["programa"] == SIN_DATO).any() else []),
        "categorias": categorias,
        "estados": [{"clave": k, "etiqueta": v} for k, v in ETIQUETA_ESTADO.items()] + [{"clave": "TARDIO", "etiqueta": "Con retraso"}],
        "fecha_minima": df["fecha"].min().strftime("%Y-%m-%d") if df["fecha"].notna().any() else None,
        "fecha_maxima": df["fecha"].max().strftime("%Y-%m-%d") if df["fecha"].notna().any() else None,
    }


# -------------------------------------------------------
# Endpoints
# -------------------------------------------------------
@app.get("/health")
def health():
    return {"estado": "ok", "servicio": "nexou-analitica"}


@app.get("/analitica")
def analitica(
    authorization: str | None = Header(default=None),
    desde: date | None = Query(default=None, description="Fecha inicial del préstamo (AAAA-MM-DD)"),
    hasta: date | None = Query(default=None, description="Fecha final del préstamo (AAAA-MM-DD)"),
    tipo: str | None = Query(default=None, description="Libro o Equipo"),
    semestre: str | None = Query(default=None, description="1-12 o sin-dato"),
    programa: str | None = None,
    categoria: str | None = None,
    estado: str | None = Query(default=None, description="ACTIVA, DEVUELTO, VENCIDO, CANCELADA o TARDIO"),
    granularidad: str = Query(default="mes", pattern="^(dia|semana|mes)$"),
):
    """Todas las métricas en una sola respuesta, con los filtros aplicados."""
    df_total, inventario = cargar_datos(authorization)
    try:
        df = aplicar_filtros(df_total, desde, hasta, tipo, semestre, programa, categoria, estado)
    except ValueError:
        raise HTTPException(status_code=400, detail="Filtro inválido")

    resumen = calcular_resumen(df)
    ranking = ranking_articulos(df, 8)
    retrasos = retrasos_por_articulo(df, 8)
    semestres = por_semestre(df)
    categorias = por_categoria(df, 8)
    dias = dia_semana(df)
    quietos = sin_movimiento(df, inventario, tipo, categoria, 8)

    return {
        "resumen": resumen,
        "hallazgos": hallazgos(resumen, ranking, retrasos, semestres, categorias, dias, quietos),
        "ranking_articulos": ranking,
        "retrasos_por_articulo": retrasos,
        "por_semestre": semestres,
        "por_programa": por_programa(df, 8),
        "por_categoria": categorias,
        "dia_semana": dias,
        "usuarios_retrasos": usuarios_con_retrasos(df, 6),
        "estados": estados(df),
        "puntualidad": puntualidad(df),
        "serie_tiempo": serie_tiempo(df, granularidad),
        "sin_movimiento": quietos,
        "filtros_disponibles": opciones_de_filtro(df_total, inventario),
    }
