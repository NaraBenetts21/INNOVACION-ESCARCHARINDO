
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

from database.consultas import (
    obtener_pedidos,
    obtener_insumos,
    obtener_lotes,
    obtener_mermas
)


def mostrar_reportes():

    st.title("Reportes y análisis")
    st.write("Indicadores generales del simulador de Grupo Escarcharindo.")

    # Obtener información de MySQL
    pedidos = obtener_pedidos()
    insumos = obtener_insumos()
    lotes = obtener_lotes()
    mermas = obtener_mermas()

    # Convertir información a DataFrames
    df_pedidos = pd.DataFrame(pedidos)
    df_insumos = pd.DataFrame(insumos)
    df_lotes = pd.DataFrame(lotes)
    df_mermas = pd.DataFrame(mermas)

    st.subheader("Indicadores generales")

    total_pedidos = len(df_pedidos)
    pedidos_entregados = 0
    total_produccion = 0
    total_mermas = len(df_mermas)

    if not df_pedidos.empty:
        pedidos_entregados = (
            df_pedidos["estado"] == "Entregado"
        ).sum()

    if not df_lotes.empty:
        total_produccion = df_lotes["volumen_litros"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Pedidos registrados", total_pedidos)
    col2.metric("Pedidos entregados", int(pedidos_entregados))
    col3.metric("Producción total", f"{total_produccion:,.2f} L")
    col4.metric("Registros de merma", total_mermas)

    st.divider()

    # Gráfica de estados de pedidos
    st.subheader("Estado de los pedidos")

    if not df_pedidos.empty:

        estados = (
            df_pedidos["estado"]
            .value_counts()
            .reset_index()
        )

        estados.columns = ["Estado", "Cantidad"]

        grafica = px.pie(
            estados,
            names="Estado",
            values="Cantidad",
            title="Distribución de pedidos por estado",
            template="plotly_white",
            hole=0.4,
        )

        st.plotly_chart(grafica, use_container_width=True)

    else:
        st.info("Todavía no hay pedidos registrados.")

    st.divider()

    # Producción por lote
    st.subheader("Producción por lote")

    if not df_lotes.empty:

        grafica_produccion = px.bar(
            df_lotes,
            x="id_lote",
            y="volumen_litros",
            color="producto",
            title="Volumen producido por lote",
            template="plotly_white",
            labels={
                "id_lote": "Número de lote",
                "volumen_litros": "Litros producidos",
            },
        )

        st.plotly_chart(
            grafica_produccion,
            use_container_width=True
        )

    else:
        st.info("Todavía no hay lotes de producción.")

    st.divider()

    # Inventario disponible
    st.subheader("Inventario disponible")

    if not df_insumos.empty:

        grafica_inventario = px.bar(
            df_insumos,
            x="nombre",
            y="stock_actual",
            title="Existencias actuales por insumo",
            template="plotly_white",
            labels={
                "nombre": "Insumo",
                "stock_actual": "Existencia"
            }
        )

        st.plotly_chart(
            grafica_inventario,
            use_container_width=True
        )

    else:
        st.info("No hay información de inventario.")

    st.divider()

    # Mermas por insumo
    st.subheader("Control de mermas")

    if not df_mermas.empty:

        mermas_por_insumo = (
            df_mermas.groupby(
                ["insumo", "unidad_medida"],
                as_index=False
            )["cantidad_perdida"].sum()
        )

        grafica_mermas = px.bar(
            mermas_por_insumo,
            x="insumo",
            y="cantidad_perdida",
            color="unidad_medida",
            title="Pérdidas registradas por insumo",
            labels={
                "insumo": "Insumo",
                "cantidad_perdida": "Cantidad perdida",
                "unidad_medida": "Unidad"
            },
            template="plotly_white",
        )

        st.plotly_chart(
            grafica_mermas,
            use_container_width=True
        )

    else:
        st.info("Todavía no hay mermas registradas.")


    st.divider()

    # Exportar reportes a Excel
    st.subheader("Exportar información")

    archivo = BytesIO()

    with pd.ExcelWriter(archivo, engine="openpyxl") as writer:

        df_pedidos.to_excel(
            writer,
            sheet_name="Pedidos",
            index=False
        )

        df_insumos.to_excel(
            writer,
            sheet_name="Inventario",
            index=False
        )

        df_lotes.to_excel(
            writer,
            sheet_name="Produccion",
            index=False
        )

        df_mermas.to_excel(
            writer,
            sheet_name="Mermas",
            index=False
        )

    st.download_button(
        label="Descargar reporte en Excel",
        data=archivo.getvalue(),
        file_name="reporte_escarcharindo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

