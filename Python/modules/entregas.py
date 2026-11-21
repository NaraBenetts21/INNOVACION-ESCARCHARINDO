
import streamlit as st
import pandas as pd

from database.consultas import (
    obtener_pedidos_listos_para_entrega,
    registrar_salida_entrega,
    obtener_entregas_en_transito,
    confirmar_entrega,
    obtener_historial_entregas
)


def mostrar_entregas():

    st.title("Control de entregas")
    st.write("Registro de salidas y confirmación de recepción de pedidos.")

    # Registrar salida de un pedido
    st.subheader("Registrar salida")

    pedidos = obtener_pedidos_listos_para_entrega()

    if pedidos:

        opciones = {
            f"Pedido #{p['id_pedido']} - {p['cliente']} - ${p['total']:.2f}": p
            for p in pedidos
        }

        seleccion = st.selectbox(
            "Selecciona un pedido listo para entregar",
            list(opciones.keys())
        )

        pedido = opciones[seleccion]

        st.write(f"**Cliente:** {pedido['cliente']}")
        st.write(f"**Fecha de entrega:** {pedido['fecha_entrega']}")
        st.write(f"**Prioridad:** {pedido['prioridad']}")
        st.write(f"**Total:** ${pedido['total']:.2f}")

        responsable = st.text_input(
            "Responsable de entrega",
            key="responsable_entrega"
        )

        observaciones = st.text_area(
            "Observaciones de salida",
            key="observaciones_salida"
        )

        if st.button("Registrar salida del pedido"):

            if not responsable.strip():
                st.warning("Escribe el nombre del responsable.")
            else:
                try:
                    registrar_salida_entrega(
                        pedido["id_pedido"],
                        responsable.strip(),
                        observaciones.strip()
                    )

                    st.success("Salida registrada correctamente.")
                    st.rerun()

                except Exception as e:
                    st.error(f"No se pudo registrar la salida: {e}")

    else:
        st.info("No hay pedidos listos para entregar.")

    st.divider()

    # Entregas en tránsito
    st.subheader("Entregas en tránsito")

    entregas = obtener_entregas_en_transito()

    if entregas:

        for entrega in entregas:

            with st.expander(
                f"Entrega #{entrega['id_entrega']} - "
                f"Pedido #{entrega['id_pedido']} - {entrega['cliente']}"
            ):

                st.write(f"**Fecha de salida:** {entrega['fecha_salida']}")
                st.write(f"**Responsable:** {entrega['responsable_entrega']}")
                st.write(f"**Observaciones:** {entrega['observaciones']}")

                recibido_por = st.text_input(
                    "Nombre de quien recibe",
                    key=f"recibido_{entrega['id_entrega']}"
                )

                if st.button(
                    "Confirmar recepción",
                    key=f"confirmar_{entrega['id_entrega']}"
                ):

                    if not recibido_por.strip():
                        st.warning("Escribe quién recibió el pedido.")
                    else:
                        try:
                            confirmar_entrega(
                                entrega["id_entrega"],
                                recibido_por.strip()
                            )

                            st.success("Entrega confirmada correctamente.")
                            st.rerun()

                        except Exception as e:
                            st.error(f"No se pudo confirmar: {e}")

    else:
        st.info("No hay entregas en tránsito.")

    st.divider()

    # Historial de entregas
    st.subheader("Historial de entregas")

    historial = obtener_historial_entregas()

    if historial:
        df = pd.DataFrame(historial)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Todavía no hay entregas registradas.")
