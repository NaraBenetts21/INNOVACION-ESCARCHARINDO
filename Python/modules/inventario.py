

import streamlit as st
import pandas as pd

from database.consultas import (
    obtener_insumos,
    registrar_movimiento,
    obtener_movimientos
)
from modules.unidades import campo_cantidad


def mostrar_inventario():

    st.title("Control de inventario")
    st.write("Administración de existencias de Grupo Escarcharindo.")

    insumos = obtener_insumos()

    if not insumos:
        st.warning("No hay insumos registrados.")
        return

    # Indicadores
    total_insumos = len(insumos)

    inventario_bajo = sum(
        1 for i in insumos
        if float(i["stock_actual"]) <= float(i["stock_minimo"])
    )

    col1, col2 = st.columns(2)

    col1.metric("Insumos registrados", total_insumos)
    col2.metric("Inventarios bajos", inventario_bajo)

    st.divider()

    # Tabla de inventario
    st.subheader("Existencias actuales")

    df = pd.DataFrame(insumos)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # Alertas
    bajos = [
        i for i in insumos
        if float(i["stock_actual"]) <= float(i["stock_minimo"])
    ]

    if bajos:
        st.warning("Hay insumos que necesitan reabastecimiento.")

        for insumo in bajos:
            st.write(
                f"- {insumo['nombre']}: "
                f"{insumo['stock_actual']} "
                f"{insumo['unidad_medida']}"
            )

    st.divider()

    # Registrar movimientos
    st.subheader("Registrar movimiento")

    opciones_insumos = {
        i["nombre"]: i
        for i in insumos
    }

    # El insumo se elige FUERA del formulario para que el selector de
    # unidad (kg/g, L/ml) se ajuste de inmediato al insumo elegido.
    nombre = st.selectbox(
        "Selecciona el insumo",
        list(opciones_insumos.keys()),
        key="movimiento_insumo"
    )

    insumo = opciones_insumos[nombre]

    st.caption(
        f"Unidad de almacenamiento: {insumo['unidad_medida']} · "
        f"Existencia actual: {insumo['stock_actual']}"
    )

    with st.form("formulario_inventario"):

        tipo = st.selectbox(
            "Tipo de movimiento",
            ["Entrada", "Salida"]
        )

        cantidad = campo_cantidad(
            "Cantidad",
            insumo["unidad_medida"],
            key="movimiento",
            valor=1.0,
            minimo=0.001,
            paso=1.0
        )

        motivo = st.text_input("Motivo del movimiento")
        responsable = st.text_input("Responsable")

        enviar = st.form_submit_button(
            "Registrar movimiento"
        )

        if enviar:

            try:
                registrar_movimiento(
                    insumo["id_insumo"],
                    tipo,
                    cantidad,
                    motivo,
                    responsable
                )

                st.success("Movimiento registrado correctamente.")
                st.rerun()

            except Exception as error:
                st.error(f"No se pudo registrar: {error}")

    st.divider()

    # Historial
    st.subheader("Historial de movimientos")

    movimientos = obtener_movimientos()

    if movimientos:
        df_movimientos = pd.DataFrame(movimientos)

        st.dataframe(
            df_movimientos,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Todavía no hay movimientos registrados.")
