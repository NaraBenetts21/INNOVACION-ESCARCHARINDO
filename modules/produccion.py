import streamlit as st
import pandas as pd

from datetime import date

from database.consultas import (
    obtener_productos,
    obtener_insumos,
    registrar_lote,
    obtener_lotes,
    obtener_pedidos_para_produccion,
    finalizar_produccion
)


def mostrar_produccion():
    st.title("Control de producción")
    st.write("Registro y seguimiento de lotes de fabricación.")

    productos = obtener_productos()
    insumos = obtener_insumos()

    if not productos:
        st.warning("No hay productos registrados.")
        return

    if not insumos:
        st.warning("No hay insumos registrados.")
        return

    st.divider()

    # PEDIDOS PENDIENTES DE PRODUCCION
    st.subheader("Pedidos pendientes de producción")

    pedidos = obtener_pedidos_para_produccion()

    if pedidos:

        opciones_pedidos = {
            f"Pedido #{p['id_pedido']} - {p['cliente']} - {p['producto']}": p
            for p in pedidos
        }

        pedido_nombre = st.selectbox(
            "Seleccionar pedido para producir",
            ["Sin pedido relacionado"] + list(opciones_pedidos.keys()),
            key="pedido_produccion"
        )

        if pedido_nombre != "Sin pedido relacionado":

            pedido_seleccionado = opciones_pedidos[pedido_nombre]

            st.info(
                f"""
                **Cliente:** {pedido_seleccionado['cliente']}

                **Producto:** {pedido_seleccionado['producto']}

                **Cantidad solicitada:** {pedido_seleccionado['cantidad']} unidades

                **Volumen requerido:** {pedido_seleccionado['volumen_litros']} litros

                **Fecha de entrega:** {pedido_seleccionado['fecha_entrega']}
                """
            )

        else:
            pedido_seleccionado = None

    else:
        pedido_seleccionado = None
        st.info("No hay pedidos en preparación actualmente.")

    st.divider()

    st.subheader("Registrar nuevo lote")

    # Preparar datos del pedido seleccionado
    if pedido_seleccionado is not None:

        producto_pedido = next(
            p for p in productos
            if p["id_producto"] == pedido_seleccionado["id_producto"]
        )

        producto_predeterminado = producto_pedido["nombre"]
        volumen_predeterminado = float(
            pedido_seleccionado["volumen_litros"]
        )

        st.caption(
            f"El lote quedará relacionado con el pedido "
            f"#{pedido_seleccionado['id_pedido']}."
        )

    else:
        producto_predeterminado = productos[0]["nombre"]
        volumen_predeterminado = 10.0

    with st.form("formulario_produccion"):

        # Seleccionar producto
        opciones_productos = {
            p["nombre"]: p["id_producto"]
            for p in productos
        }

        producto_nombre = st.selectbox(
            "Producto a fabricar",
            list(opciones_productos.keys()),
            index=list(opciones_productos.keys()).index(
                producto_predeterminado
            )
        )

        volumen = st.number_input(
            "Volumen de producción (litros)",
            min_value=0.01,
            value=volumen_predeterminado,
            step=1.0
        )

        fecha = st.date_input(
            "Fecha de producción",
            value=date.today()
        )

        tiempo = st.number_input(
            "Tiempo de cocción (minutos)",
            min_value=1,
            value=60,
            step=5
        )

        responsable = st.text_input(
            "Responsable de producción"
        )

        st.divider()

        st.subheader("Consumo de insumos")

        st.caption(
            "Captura únicamente los materiales utilizados. "
            "Deja en cero los que no se utilizaron."
        )

        consumos = []

        for insumo in insumos:

            cantidad = st.number_input(
                f"{insumo['nombre']} ({insumo['unidad_medida']})",
                min_value=0.0,
                value=0.0,
                step=0.5,
                key=f"produccion_{insumo['id_insumo']}"
            )

            if cantidad > 0:
                consumos.append({
                    "id_insumo": insumo["id_insumo"],
                    "cantidad": cantidad
                })

        registrar = st.form_submit_button(
            "Registrar lote de producción",
            disabled=st.session_state.get("produccion_registrando", False)
        )

        if registrar:

            if not responsable.strip():
                st.error("Debes indicar al responsable.")

            elif not consumos:
                st.error("Debes registrar al menos un insumo.")

            else:
                st.session_state["produccion_registrando"] = True

                try:
                    id_lote = registrar_lote(
                        id_producto=opciones_productos[producto_nombre],
                        fecha=fecha,
                        volumen=volumen,
                        tiempo_coccion=tiempo,
                        responsable=responsable,
                        consumos=consumos,
                        id_pedido=(
                            pedido_seleccionado["id_pedido"]
                            if pedido_seleccionado is not None
                            else None
                        )
                    )

                    st.session_state["produccion_registrando"] = False

                    st.success(
                        f"Lote #{id_lote} registrado correctamente."
                    )

                    st.rerun()

                except Exception as error:
                    st.session_state["produccion_registrando"] = False

                    st.error(
                        f"No se pudo registrar el lote: {error}"
                    )
    st.divider()
    st.subheader("Historial de producción")

    lotes = obtener_lotes()

    if lotes:
        df_lotes = pd.DataFrame(lotes)

        df_lotes = df_lotes.rename(columns={
            "id_lote": "Número de lote",
            "producto": "Producto",
            "fecha_produccion": "Fecha de producción",
            "volumen_litros": "Volumen (litros)",
            "tiempo_coccion_min": "Tiempo de cocción (min)",
            "responsable": "Responsable",
            "estado": "Estado"
        })

        st.dataframe(
            df_lotes,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Todavía no hay lotes registrados.")

    st.divider()

    # FINALIZAR PRODUCCION
    st.subheader("Finalizar producción")

    if lotes:

        lotes_pendientes = [
            lote for lote in lotes
            if lote["estado"] != "Terminado"
        ]

        if lotes_pendientes:

            opciones_lotes = {
                f"Lote #{lote['id_lote']} - {lote['producto']}": lote
                for lote in lotes_pendientes
            }

            lote_nombre = st.selectbox(
                "Seleccionar lote para finalizar",
                list(opciones_lotes.keys()),
                key="lote_finalizar"
            )

            lote_seleccionado = opciones_lotes[lote_nombre]

            st.write(
                f"**Estado actual:** {lote_seleccionado['estado']}"
            )

            if st.button("Finalizar lote"):

                try:
                    finalizar_produccion(
                        lote_seleccionado["id_lote"]
                    )

                    st.success(
                        "Producción finalizada correctamente."
                    )

                    st.rerun()

                except Exception as error:
                    st.error(
                        f"No se pudo finalizar la producción: {error}"
                    )

        else:
            st.success("Todos los lotes están terminados.")

    else:
        st.info("No hay lotes disponibles.")


