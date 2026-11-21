
import streamlit as st
import pandas as pd

from database.consultas import (
    obtener_lotes,
    obtener_insumos,
    obtener_insumos_por_lote,
    registrar_merma,
    obtener_mermas
)


def mostrar_mermas():

    st.title("Control de mermas")
    st.write("Registro y seguimiento de desperdicios durante la producción.")

    lotes = obtener_lotes()
    insumos = obtener_insumos()


    st.divider()
    st.subheader("Registrar nueva merma")

    opciones_lotes = {
        f"Lote #{lote['id_lote']} - {lote['producto']}": lote["id_lote"]
        for lote in lotes
    }

    with st.form("formulario_mermas"):

        lote_nombre = st.selectbox(
            "Selecciona el lote de producción",
            list(opciones_lotes.keys())
        )

        id_lote = opciones_lotes[lote_nombre]

        insumos_lote = obtener_insumos_por_lote(id_lote)

        if not insumos_lote:
            st.warning("Este lote no tiene insumos registrados.")
            registrar = False

        else:
            opciones_insumos = {
                insumo["nombre"]: insumo["id_insumo"]
                for insumo in insumos_lote
            }

            insumo_nombre = st.selectbox(
                "Insumo desperdiciado",
                list(opciones_insumos.keys())
            )

            cantidad = st.number_input(
                "Cantidad perdida",
                min_value=0.01,
                value=0.01,
                step=0.5
            )

            motivo = st.selectbox(
                "Motivo de la merma",
                [
                    "Derrame durante la producción",
                    "Error de preparación",
                    "Material dañado",
                    "Producto defectuoso",
                    "Exceso de material",
                    "Otro"
                ]
            )

            responsable = st.text_input("Responsable")

            registrar = st.form_submit_button("Registrar merma")

        if registrar and insumos_lote:
            if not responsable.strip():
                st.error("Debes indicar al responsable.")

            else:
                try:
                    registrar_merma(
                        id_lote=id_lote,
                        id_insumo=opciones_insumos[insumo_nombre],
                        cantidad=cantidad,
                        motivo=motivo,
                        responsable=responsable
                    )

                    st.success("Merma registrada correctamente.")
                    st.rerun()

                except Exception as error:
                    st.error(f"No se pudo registrar la merma: {error}")

    st.divider()
    st.subheader("Historial de mermas")

    mermas = obtener_mermas()

    if mermas:

        df_mermas = pd.DataFrame(mermas)

        df_mermas = df_mermas.rename(columns={
            "id_merma": "Número de merma",
            "id_lote": "Lote",
            "insumo": "Insumo",
            "cantidad_perdida": "Cantidad perdida",
            "unidad_medida": "Unidad",
            "motivo": "Motivo",
            "responsable": "Responsable",
            "fecha_registro": "Fecha de registro"
        })

        st.dataframe(
            df_mermas,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Todavía no hay mermas registradas.")
