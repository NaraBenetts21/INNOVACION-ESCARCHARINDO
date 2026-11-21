
import streamlit as st
import pandas as pd

from database.consultas import (
    obtener_clientes,
    registrar_cliente,
    obtener_productos,
    registrar_pedido,
    obtener_pedidos,
    actualizar_estado_pedido
)


def mostrar_pedidos():

    st.title("Gestión de pedidos")
    st.write("Administración de clientes y pedidos comerciales.")

    st.divider()

    # REGISTRAR NUEVO CLIENTE
    st.subheader("Registrar nuevo cliente")

    with st.form("formulario_clientes"):

        nombre = st.text_input("Nombre del cliente")

        tipo_cliente = st.selectbox(
            "Tipo de cliente",
            [
                "Distribuidor",
                "Mayorista",
                "Minorista",
                "Cliente particular"
            ]
        )

        telefono = st.text_input("Teléfono")
        correo = st.text_input("Correo electrónico")
        direccion = st.text_input("Dirección")

        registrar = st.form_submit_button("Registrar cliente")

        if registrar:

            if not nombre.strip():
                st.error("Debes ingresar el nombre del cliente.")

            else:

                try:
                    registrar_cliente(
                        nombre=nombre,
                        tipo_cliente=tipo_cliente,
                        telefono=telefono,
                        correo=correo,
                        direccion=direccion
                    )

                    st.success("Cliente registrado correctamente.")
                    st.rerun()

                except Exception as error:
                    st.error(f"No se pudo registrar el cliente: {error}")

    st.divider()

    # DIRECTORIO DE CLIENTES
    st.subheader("Directorio de clientes")

    clientes = obtener_clientes()

    if clientes:
        df_clientes = pd.DataFrame(clientes)
        st.dataframe(
            df_clientes,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Todavía no hay clientes registrados.")

    st.divider()

    # CREAR NUEVO PEDIDO
    st.subheader("Crear nuevo pedido")

    clientes = obtener_clientes()
    productos = obtener_productos()

    if not clientes:
        st.warning("Primero debes registrar un cliente.")

    elif not productos:
        st.warning("No hay productos registrados.")

    else:

        opciones_clientes = {
            cliente["nombre"]: cliente["id_cliente"]
            for cliente in clientes
        }


        # OPCIONES DE PRODUCTOS
        opciones_productos = {
            (
                f"{producto['nombre']} | "
                f"{producto['presentacion']} | "
                f"${float(producto['precio_venta']):,.2f}"
            ): producto
            for producto in productos
        }

        # SELECCIONAR CLIENTE
        cliente_nombre = st.selectbox(
            "Seleccionar cliente",
            list(opciones_clientes.keys()),
            key="pedido_cliente"
        )

        # SELECCIONAR PRODUCTO
        producto_nombre = st.selectbox(
            "Producto solicitado",
            list(opciones_productos.keys()),
            key="pedido_producto"
        )

        producto_seleccionado = opciones_productos[producto_nombre]


        precio_unitario = float(
            producto_seleccionado["precio_venta"]
        )

        st.caption(
            f"Precio unitario: ${precio_unitario:,.2f}"
        )

        # CANTIDAD DE PRODUCTOS
        cantidad = st.number_input(
            "Cantidad de unidades",
            min_value=1,
            value=10,
            step=1,
            key="pedido_cantidad"
        )

        # FECHA DE ENTREGA
        fecha_entrega = st.date_input(
            "Fecha de entrega",
            key="pedido_fecha"
        )

        # PRIORIDAD
        prioridad = st.selectbox(
            "Prioridad",
            ["Normal", "Alta", "Urgente"],
            key="pedido_prioridad"
        )

        # OBSERVACIONES
        observaciones = st.text_area(
            "Observaciones del pedido",
            key="pedido_observaciones"
        )

        # CALCULAR TOTAL AUTOMATICAMENTE
        total_estimado = precio_unitario * cantidad

        st.metric(
            "Total estimado del pedido",
            f"${total_estimado:,.2f}"
        )

        # REGISTRAR PEDIDO
        if st.button("Crear pedido", key="crear_pedido"):

            try:
                id_pedido = registrar_pedido(
                    id_cliente=opciones_clientes[cliente_nombre],
                    fecha_entrega=fecha_entrega,
                    prioridad=prioridad,
                    observaciones=observaciones,
                    productos_pedido=[
                        {
                            "id_producto": producto_seleccionado["id_producto"],
                            "cantidad": cantidad
                        }
                    ]
                )

                st.success(
                    f"Pedido #{id_pedido} registrado correctamente."
                )

                st.rerun()

            except Exception as error:
                st.error(
                    f"No se pudo registrar el pedido: {error}"
                )

    st.divider()



    st.divider()

    # SEGUIMIENTO Y ACTUALIZACION DE PEDIDOS
    st.subheader("Seguimiento y actualización de pedidos")

    pedidos_estado = obtener_pedidos()

    if pedidos_estado:

        opciones_pedidos = {
            f"Pedido #{pedido['id_pedido']} - {pedido['cliente']}": pedido
            for pedido in pedidos_estado
        }

        pedido_seleccionado_nombre = st.selectbox(
            "Seleccionar pedido",
            list(opciones_pedidos.keys()),
            key="pedido_seguimiento"
        )

        pedido_seleccionado = opciones_pedidos[
            pedido_seleccionado_nombre
        ]

        st.write(
            f"Estado actual: **{pedido_seleccionado['estado']}**"
        )

        nuevo_estado = st.selectbox(
            "Nuevo estado del pedido",
            [
                "Pendiente",
                "En preparación",
                "Listo",
                "Entregado"
            ],
            key="nuevo_estado_pedido"
        )

        if st.button("Actualizar estado", key="actualizar_estado"):

            try:
                actualizar_estado_pedido(
                    id_pedido=pedido_seleccionado["id_pedido"],
                    nuevo_estado=nuevo_estado
                )

                st.success(
                    "Estado del pedido actualizado correctamente."
                )

                st.rerun()

            except Exception as error:
                st.error(
                    f"No se pudo actualizar el pedido: {error}"
                )

    else:
        st.info("No hay pedidos disponibles para actualizar.")

    st.divider()

    # HISTORIAL DE PEDIDOS
    st.subheader("Historial de pedidos")

    pedidos = obtener_pedidos()

    if pedidos:

        df_pedidos = pd.DataFrame(pedidos)

        df_pedidos = df_pedidos.rename(columns={
            "id_pedido": "Número de pedido",
            "cliente": "Cliente",
            "fecha_pedido": "Fecha de registro",
            "fecha_entrega": "Fecha de entrega",
            "estado": "Estado",
            "prioridad": "Prioridad",
            "total": "Total",
            "observaciones": "Observaciones"
        })

        st.dataframe(
            df_pedidos,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Todavía no hay pedidos registrados.")
