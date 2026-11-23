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
from modules.unidades import campo_cantidad


def _etiqueta_producto(producto):
    """Nombre + presentación, para distinguir 1/4, 1/2 y 1 litro."""
    return f"{producto['nombre']} | {producto['presentacion']}"


def _es_solido(producto):
    """Cubetas y vasos se producen por peso (kg); lo demás por volumen (L)."""
    gramos = int(producto.get("capacidad_g") or 0)
    mililitros = int(producto.get("capacidad_ml") or 0)
    return gramos > 0 and mililitros == 0


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

            if _es_solido(pedido_seleccionado):
                requerido = (
                    f"**Peso requerido:** "
                    f"{pedido_seleccionado['cantidad_kg']} kg"
                )
            else:
                requerido = (
                    f"**Volumen requerido:** "
                    f"{pedido_seleccionado['volumen_litros']} litros"
                )

            st.info(
                f"""
                **Cliente:** {pedido_seleccionado['cliente']}

                **Producto:** {pedido_seleccionado['producto']}

                **Cantidad solicitada:** {pedido_seleccionado['cantidad']} unidades

                {requerido}

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

    # Catálogo: etiqueta (nombre | presentación) -> producto
    opciones_productos = {
        _etiqueta_producto(p): p
        for p in productos
    }
    etiquetas = list(opciones_productos.keys())

    # Producto y cantidad por defecto, según el pedido elegido
    if pedido_seleccionado is not None:

        producto_pedido = next(
            p for p in productos
            if p["id_producto"] == pedido_seleccionado["id_producto"]
        )

        producto_predeterminado = _etiqueta_producto(producto_pedido)
        clave_pedido = pedido_seleccionado["id_pedido"]

        if _es_solido(pedido_seleccionado):
            cantidad_predeterminada = float(
                pedido_seleccionado["cantidad_kg"]
            )
        else:
            cantidad_predeterminada = float(
                pedido_seleccionado["volumen_litros"]
            )

        st.caption(
            f"El lote quedará relacionado con el pedido "
            f"#{pedido_seleccionado['id_pedido']}."
        )

    else:
        producto_predeterminado = etiquetas[0]
        cantidad_predeterminada = 10.0
        clave_pedido = 0

    # El producto se elige FUERA del formulario para que el campo de
    # cantidad cambie de inmediato entre litros (líquidos) y kilos (sólidos).
    producto_nombre = st.selectbox(
        "Producto a fabricar",
        etiquetas,
        index=etiquetas.index(producto_predeterminado),
        key=f"produccion_producto_{clave_pedido}"
    )

    producto = opciones_productos[producto_nombre]
    solido = _es_solido(producto)

    # Si el producto elegido no es el del pedido, se usa un valor base
    if (
        pedido_seleccionado is not None
        and producto["id_producto"] == pedido_seleccionado["id_producto"]
    ):
        valor_inicial = cantidad_predeterminada
    else:
        valor_inicial = 10.0

    with st.form("formulario_produccion"):

        # Cubetas y vasos: kg (o g). Líquidos: L (o ml).
        cantidad_producida = campo_cantidad(
            "Peso a producir" if solido else "Volumen de producción",
            "kg" if solido else "l",
            key=f"produccion_cantidad_{clave_pedido}_{producto['id_producto']}",
            valor=max(valor_inicial, 0.001),
            minimo=0.001,
            paso=1.0
        )

        fecha = st.date_input(
            "Fecha de producción",
            value=date.today()
        )

        responsable = st.text_input(
            "Responsable de producción"
        )

        st.divider()

        st.subheader("Consumo de insumos")

        st.caption(
            "Captura únicamente los materiales utilizados. "
            "Deja en cero los que no se utilizaron. "
            "Puedes elegir la unidad (kg o g) en cada insumo."
        )

        consumos = []

        for insumo in insumos:

            cantidad = campo_cantidad(
                insumo["nombre"],
                insumo["unidad_medida"],
                key=f"produccion_{insumo['id_insumo']}",
                valor=0.0,
                minimo=0.0,
                paso=0.5
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
                        id_producto=producto["id_producto"],
                        fecha=fecha,
                        volumen=0 if solido else cantidad_producida,
                        tiempo_coccion=None,
                        responsable=responsable,
                        consumos=consumos,
                        id_pedido=(
                            pedido_seleccionado["id_pedido"]
                            if pedido_seleccionado is not None
                            else None
                        ),
                        cantidad_kg=cantidad_producida if solido else 0
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

        # El tiempo de cocción ya no se captura ni se muestra
        df_lotes = df_lotes.drop(
            columns=["tiempo_coccion_min"],
            errors="ignore"
        )

        df_lotes = df_lotes.rename(columns={
            "id_lote": "Número de lote",
            "producto": "Producto",
            "fecha_produccion": "Fecha de producción",
            "volumen_litros": "Volumen (litros)",
            "cantidad_kg": "Peso (kg)",
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