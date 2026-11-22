from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_option_menu import option_menu

from modules.inventario import mostrar_inventario
from modules.produccion import mostrar_produccion
from modules.mermas import mostrar_mermas
from modules.pedidos import mostrar_pedidos
from modules.entregas import mostrar_entregas
from modules.reportes import mostrar_reportes

from database.consultas import (
    obtener_pedidos,
    obtener_insumos,
    obtener_lotes,
    obtener_mermas,
)

st.set_page_config(
    page_title="Escarcharindo | Sistema de control",
    page_icon="📦",
    layout="wide",
)

# Paleta Escarcharindo
VINO, ROJO, ORO, CAFE, ROSA = "#741323", "#94172A", "#F4B52D", "#54251F", "#D8B9B3"
COLORES = [VINO, ORO, ROJO, ROSA, CAFE]

ASSETS = Path(__file__).parent / "assets"
st.markdown(
    f"<style>{(ASSETS / 'estilos.css').read_text(encoding='utf-8')}</style>",
    unsafe_allow_html=True,
)


def estilo_grafica(fig):
    """Gráficas limpias, sobre blanco, con la paleta de la marca."""
    fig.update_layout(
        colorway=COLORES,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font_color=CAFE,
        margin=dict(l=10, r=10, t=30, b=10),
        legend_title_text="",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#F0E4E1")
    return fig


# ---------- Menú lateral ----------
with st.sidebar:
    st.image(str(ASSETS / "logo_escarcharindo.png"), use_container_width=True)
    st.markdown(
        "<p style='text-align:center;font-size:.8rem;letter-spacing:.12em;"
        "opacity:.8;margin:0 0 .6rem'>CENTRO DE CONTROL DIGITAL</p>",
        unsafe_allow_html=True,
    )

    opcion = option_menu(
        None,
        ["Inicio", "Inventario", "Producción", "Mermas", "Pedidos", "Entregas", "Reportes"],
        icons=["house", "box-seam", "gear", "exclamation-triangle", "cart", "truck", "bar-chart"],
        default_index=0,
        styles={
            "container": {"padding": "0", "background-color": "transparent"},
            "icon": {"color": ORO, "font-size": "16px"},
            "nav-link": {
                "font-size": "14px", "color": "#fff", "text-align": "left",
                "margin": "2px 0", "border-radius": "8px",
                "--hover-color": "rgba(255,255,255,.12)",
            },
            "nav-link-selected": {"background-color": ROJO, "font-weight": "600"},
        },
    )


# ---------- Inicio ----------
def mostrar_inicio():
    st.title("Centro de Control Digital")
    st.caption("Panel general de operaciones · Grupo Escarcharindo")

    df_pedidos = pd.DataFrame(obtener_pedidos())
    df_insumos = pd.DataFrame(obtener_insumos())
    df_lotes = pd.DataFrame(obtener_lotes())
    df_mermas = pd.DataFrame(obtener_mermas())

    pendientes = entregados = bajos = 0
    litros = 0.0
    if not df_pedidos.empty:
        pendientes = int(df_pedidos["estado"].isin(
            ["Pendiente", "En preparación", "Listo", "En tránsito"]).sum())
        entregados = int((df_pedidos["estado"] == "Entregado").sum())
    if not df_lotes.empty:
        litros = float(df_lotes["volumen_litros"].sum())
    if not df_insumos.empty:
        alertas = df_insumos[df_insumos["stock_actual"] <= df_insumos["stock_minimo"]]
        bajos = len(alertas)

    # Una sola fila de indicadores
    k = st.columns(6)
    k[0].metric("Pedidos", len(df_pedidos))
    k[1].metric("Pendientes", pendientes)
    k[2].metric("Entregados", entregados)
    k[3].metric("Producción", f"{litros:,.1f} L")
    k[4].metric("Mermas", len(df_mermas))
    k[5].metric("Stock bajo", bajos)

    st.write("")

    # Gráficas agrupadas en pestañas
    t1, t2, t3 = st.tabs(["Pedidos", "Producción", "Inventario"])

    with t1:
        if not df_pedidos.empty:
            estados = df_pedidos["estado"].value_counts().reset_index()
            estados.columns = ["Estado", "Cantidad"]
            st.plotly_chart(
                estilo_grafica(px.pie(estados, names="Estado", values="Cantidad", hole=0.55)),
                use_container_width=True,
            )
        else:
            st.info("No hay pedidos registrados.")

    with t2:
        if not df_lotes.empty:
            st.plotly_chart(
                estilo_grafica(px.bar(
                    df_lotes, x="id_lote", y="volumen_litros", color="producto",
                    labels={"id_lote": "Lote", "volumen_litros": "Litros"})),
                use_container_width=True,
            )
        else:
            st.info("No hay producción registrada.")

    with t3:
        if not df_insumos.empty:
            st.plotly_chart(
                estilo_grafica(px.bar(
                    df_insumos, x="nombre", y="stock_actual",
                    labels={"nombre": "Insumo", "stock_actual": "Existencia"})),
                use_container_width=True,
            )
        else:
            st.info("No hay información de inventario.")

    # Secciones secundarias plegadas
    with st.expander(f"Alertas de inventario ({bajos})", expanded=bool(bajos)):
        if bajos:
            for _, i in alertas.iterrows():
                st.warning(
                    f"{i['nombre']}: {i['stock_actual']} {i['unidad_medida']} "
                    f"(mínimo {i['stock_minimo']})"
                )
        else:
            st.success("Todos los insumos están por encima del mínimo.")

    with st.expander("Últimos pedidos"):
        if not df_pedidos.empty:
            cols = ["id_pedido", "cliente", "fecha_entrega", "estado", "prioridad", "total"]
            st.dataframe(df_pedidos[cols].head(5), use_container_width=True, hide_index=True)
        else:
            st.info("Todavía no hay pedidos registrados.")


# ---------- Enrutador ----------
if opcion == "Inicio":
    mostrar_inicio()
elif opcion == "Inventario":
    mostrar_inventario()
elif opcion == "Producción":
    mostrar_produccion()
elif opcion == "Mermas":
    mostrar_mermas()
elif opcion == "Pedidos":
    mostrar_pedidos()
elif opcion == "Entregas":
    mostrar_entregas()
elif opcion == "Reportes":
    mostrar_reportes()