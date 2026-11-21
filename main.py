
import streamlit as st

from modules.inventario import mostrar_inventario
from modules.produccion import mostrar_produccion
from modules.mermas import mostrar_mermas
from modules.pedidos import mostrar_pedidos
from modules.entregas import mostrar_entregas
from modules.reportes import mostrar_reportes

import pandas as pd
import plotly.express as px

from database.consultas import (
    obtener_pedidos,
    obtener_insumos,
    obtener_lotes,
    obtener_mermas
)

st.set_page_config(
    page_title="Escarcharindo | Sistema de control",
    page_icon="📦",
    layout="wide"
)

# Estilos visuales de Escarcharindo

st.markdown("""

<style>

/* Fondo general */
.stApp,
[data-testid="stAppViewContainer"] {
    background-color: #F7F3F0;
}


/* Fondo de las gráficas */
[data-testid="stPlotlyChart"] {
    background-color: #FFFFFF !important;
}

[data-testid="stPlotlyChart"] > div {
    background-color: #FFFFFF !important;
}

[data-testid="stPlotlyChart"] iframe {
    background-color: #FFFFFF !important;
}


/* Texto general del contenido */
[data-testid="stMain"],
[data-testid="stMain"] p,
[data-testid="stMain"] label,
[data-testid="stMain"] span,
[data-testid="stMain"] li,
[data-testid="stMain"] .stMarkdown {
    color: #54251F !important;
}

/* Títulos */
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3 {
    color: #741323 !important;
}

/* Menú lateral */
[data-testid="stSidebar"] {
    background-color: #741323;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
}

/* Tarjetas de indicadores */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border-left: 5px solid #F4B52D;
    padding: 18px;
    border-radius: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}

[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {
    color: #54251F !important;
}

/* Campos de texto */
[data-testid="stMain"] input,
[data-testid="stMain"] textarea {
    background-color: #FFFFFF !important;
    color: #54251F !important;
    border: 1px solid #D8B9B3 !important;
}

/* Botones */
.stButton > button {
    background-color: #94172A;
    color: #FFFFFF !important;
    border: none;
    border-radius: 8px;
    font-weight: bold;
}

.stButton > button:hover {
    background-color: #F4B52D;
    color: #54251F !important;
}

/* Tablas */
[data-testid="stDataFrame"] {
    background-color: #FFFFFF;
    border-radius: 10px;
}

/* Separadores */
hr {
    border-color: #E5C7C2;
}


/* Corregir texto de botones */
.stButton > button,
.stDownloadButton > button,
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-secondary"] {
    color: #FFFFFF !important;
    background-color: #94172A !important;
    border: none !important;
}

/* Texto interno de los botones */
.stButton > button p,
.stButton > button span,
.stDownloadButton > button p,
.stDownloadButton > button span,
[data-testid="stBaseButton-primary"] *,
[data-testid="stBaseButton-secondary"] * {
    color: #FFFFFF !important;
}

/* Efecto al pasar el cursor */
.stButton > button:hover,
.stDownloadButton > button:hover {
    background-color: #F4B52D !important;
}

.stButton > button:hover *,
.stDownloadButton > button:hover * {
    color: #54251F !important;
}


/* Estilo general para TODOS los botones */
[data-testid="stMain"] button {
    background-color: #94172A !important;
    color: #FFFFFF !important;
    border: 1px solid #94172A !important;
    border-radius: 8px !important;
}

/* Forzar color de todos los elementos internos */
[data-testid="stMain"] button *,
[data-testid="stMain"] button p,
[data-testid="stMain"] button span,
[data-testid="stMain"] button div {
    color: #FFFFFF !important;
}

/* Efecto al pasar el cursor */
[data-testid="stMain"] button:hover {
    background-color: #F4B52D !important;
    border-color: #F4B52D !important;
}

[data-testid="stMain"] button:hover *,
[data-testid="stMain"] button:hover p,
[data-testid="stMain"] button:hover span {
    color: #54251F !important;
}

/* Botones deshabilitados */
[data-testid="stMain"] button:disabled {
    background-color: #D9C5C2 !important;
    color: #FFFFFF !important;
    border-color: #D9C5C2 !important;
}


/* Fondo de los contenedores de gráficas */
[data-testid="stPlotlyChart"] {
    background-color: #FFFFFF !important;
    border-radius: 12px;
    padding: 10px;
}

/* Fondo de los contenedores de gráficos */
[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"] {
    background-color: #FFFFFF !important;
}


</style>

""", unsafe_allow_html=True)

st.sidebar.image(
    "assets/logo_escarcharindo.png",
    use_container_width=True
)

st.sidebar.markdown(
    "<h3 style='text-align:center; color:white;'>"
    "CENTRO DE CONTROL DIGITAL"
    "</h3>",
    unsafe_allow_html=True
)

st.sidebar.divider()

opcion = st.sidebar.selectbox(
    "Selecciona un módulo",
    [
        "Inicio",
        "Inventario",
        "Producción",
        "Control de mermas",
        "Pedidos",
        "Entregas",
        "Reportes"
    ]
)


if opcion == "Inicio":

    st.title("Centro de Control Digital")
    st.write("Panel general de operaciones | Grupo Escarcharindo")

    st.divider()

    # Obtener información de la base de datos
    pedidos = obtener_pedidos()
    insumos = obtener_insumos()
    lotes = obtener_lotes()
    mermas = obtener_mermas()

    df_pedidos = pd.DataFrame(pedidos)
    df_insumos = pd.DataFrame(insumos)
    df_lotes = pd.DataFrame(lotes)
    df_mermas = pd.DataFrame(mermas)

    # Calcular indicadores
    total_pedidos = len(df_pedidos)
    pedidos_pendientes = 0
    pedidos_entregados = 0
    total_produccion = 0
    total_mermas = len(df_mermas)
    insumos_bajos = 0

    if not df_pedidos.empty:
        pedidos_pendientes = df_pedidos["estado"].isin(
            ["Pendiente", "En preparación", "Listo", "En tránsito"]
        ).sum()

        pedidos_entregados = (
            df_pedidos["estado"] == "Entregado"
        ).sum()

    if not df_lotes.empty:
        total_produccion = df_lotes["volumen_litros"].sum()

    if not df_insumos.empty:
        insumos_bajos = (
            df_insumos["stock_actual"] <= df_insumos["stock_minimo"]
        ).sum()

    # Indicadores principales
    st.subheader("Resumen de operaciones")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Pedidos registrados", total_pedidos)
    col2.metric("Pedidos pendientes", int(pedidos_pendientes))
    col3.metric("Producción acumulada", f"{total_produccion:,.2f} L")
    col4.metric("Pedidos entregados", int(pedidos_entregados))

    col5, col6 = st.columns(2)

    col5.metric("Registros de merma", total_mermas)
    col6.metric("Insumos con stock bajo", int(insumos_bajos))

    st.divider()

    # Alertas de inventario
    st.subheader("Alertas de inventario")

    if not df_insumos.empty:

        alertas = df_insumos[
            df_insumos["stock_actual"] <= df_insumos["stock_minimo"]
        ]

        if not alertas.empty:
            for _, insumo in alertas.iterrows():
                st.warning(
                    f"{insumo['nombre']}: stock actual "
                    f"{insumo['stock_actual']} "
                    f"{insumo['unidad_medida']}. "
                    f"Mínimo: {insumo['stock_minimo']}."
                )
        else:
            st.success("Todos los insumos se encuentran por encima del stock mínimo.")

    st.divider()

    # Gráficas generales
    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Estado de los pedidos")

        if not df_pedidos.empty:

            estados = df_pedidos["estado"].value_counts().reset_index()
            estados.columns = ["Estado", "Cantidad"]

            grafica_pedidos = px.pie(
                estados,
                names="Estado",
                values="Cantidad",
                hole=0.4,
                template="plotly_white",
            )

            st.plotly_chart(
                grafica_pedidos,
                use_container_width=True
            )

        else:
            st.info("No hay pedidos registrados.")

    with col2:

        st.subheader("Producción por lote")

        if not df_lotes.empty:

            grafica_produccion = px.bar(
                df_lotes,
                x="id_lote",
                y="volumen_litros",
                color="producto",
                labels={
                    "id_lote": "Lote",
                    "volumen_litros": "Litros"
                },
                template="plotly_white",
            )

            st.plotly_chart(
                grafica_produccion,
                use_container_width=True
            )

        else:
            st.info("No hay producción registrada.")

    st.divider()

    # Últimos pedidos
    st.subheader("Últimos pedidos registrados")

    if not df_pedidos.empty:

        columnas = [
            "id_pedido",
            "cliente",
            "fecha_entrega",
            "estado",
            "prioridad",
            "total"
        ]

        st.dataframe(
            df_pedidos[columnas].head(5),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Todavía no hay pedidos registrados.")

    st.caption("Panel de información actualizado desde la base de datos MySQL.")


elif opcion == "Inventario":
    mostrar_inventario()

elif opcion == "Producción":
    mostrar_produccion()

elif opcion == "Control de mermas":
    mostrar_mermas()

elif opcion == "Pedidos":
    mostrar_pedidos()

elif opcion == "Entregas":
    mostrar_entregas()

elif opcion == "Reportes":
    mostrar_reportes()