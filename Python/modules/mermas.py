import streamlit as st
import pandas as pd

from database.consultas import (
    obtener_lotes,
    obtener_insumos_por_lote,
    registrar_merma,
    obtener_mermas
)
from modules.unidades import campo_cantidad


def mostrar_mermas():

    st.title("Control de mermas")
    st.write("Registro y seguimiento de desperdicios durante la producción.")

    lotes = obtener_lotes()

    st.divider()
    st.subheader("Registrar nueva merma")

    # Sin lotes no hay nada que capturar
    if not lotes:
        st.info(
            "Todavía no hay lotes de producción. "
            "Registra un lote en la sección Producción para poder capturar mermas."
        )

    else:
        opciones_lotes = {
            f"Lote #{lote['id_lote']} - {lote['producto']}": lote["id_lote"]
            for lote in lotes
        }

        # Lote e insumo se eligen FUERA del formulario para que la lista de
        # insumos y el selector de unidad se actualicen de inmediato.
        lote_nombre = st.selectbox(
            "Selecciona el lote de producción",
            list(opciones_lotes.keys()),
            key="merma_lote"
        )

        id_lote = opciones_lotes[lote_nombre]
        insumos_lote = obtener_insumos_por_lote(id_lote)

        if not insumos_lote:
            st.warning("Este lote no tiene insumos registrados.")

        else:
            opciones_insumos = {
                insumo["nombre"]: insumo
                for insumo in insumos_lote
            }

            insumo_nombre = st.selectbox(
                "Insumo desperdiciado",
                list(opciones_insumos.keys()),
                key=f"merma_insumo_{id_lote}"
            )

            insumo = opciones_insumos[insumo_nombre]

            with st.form("formulario_mermas"):

                cantidad = campo_cantidad(
                    "Cantidad perdida",
                    insumo["unidad_medida"],
                    key=f"merma_{id_lote}",
                    valor=1.0,
                    minimo=0.001,
                    paso=0.5
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

            if registrar:
                if not responsable.strip():
                    st.error("Debes indicar al responsable.")

                else:
                    try:
                        registrar_merma(
                            id_lote=id_lote,
                            id_insumo=insumo["id_insumo"],
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