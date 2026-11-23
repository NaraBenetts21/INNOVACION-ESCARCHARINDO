from decimal import Decimal
from database.conexion import conectar


def obtener_insumos():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        select
            id_insumo,
            nombre,
            unidad_medida,
            stock_actual,
            stock_minimo,
            costo_unitario
        from insumos
        order by nombre
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados


def registrar_movimiento(id_insumo, tipo, cantidad, motivo, responsable):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        # Convertir cantidades al mismo tipo numerico
        cantidad = Decimal(str(cantidad))

        if cantidad <= Decimal("0"):
            raise ValueError("La cantidad debe ser mayor a cero.")

        # Consultar existencias
        cursor.execute("""
            select stock_actual
            from insumos
            where id_insumo = %s
            for update
        """, (id_insumo,))

        resultado = cursor.fetchone()

        if resultado is None:
            raise ValueError("El insumo no existe.")

        stock_actual = Decimal(str(resultado[0]))

        # Calcular nuevo inventario
        if tipo == "Entrada":
            nuevo_stock = stock_actual + cantidad

        elif tipo == "Salida":
            if cantidad > stock_actual:
                raise ValueError("No hay suficiente inventario.")

            nuevo_stock = stock_actual - cantidad

        else:
            raise ValueError("Tipo de movimiento no válido.")

        # Actualizar existencias
        cursor.execute("""
            update insumos
            set stock_actual = %s
            where id_insumo = %s
        """, (nuevo_stock, id_insumo))

        # Guardar movimiento
        cursor.execute("""
            insert into movimientos_inventario
            (id_insumo, tipo_movimiento, cantidad, motivo, responsable)
            values (%s, %s, %s, %s, %s)
        """, (id_insumo, tipo, cantidad, motivo, responsable))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()

def obtener_movimientos():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        select
            m.id_movimiento,
            i.nombre as insumo,
            m.tipo_movimiento,
            m.cantidad,
            i.unidad_medida,
            m.motivo,
            m.responsable,
            m.fecha_movimiento
        from movimientos_inventario m
        inner join insumos i
            on m.id_insumo = i.id_insumo
        order by m.fecha_movimiento desc
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados


def obtener_productos():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        select
            id_producto,
            nombre,
            presentacion,
            capacidad_ml,
            capacidad_g,
            precio_venta,
            costo_produccion
        from productos
        order by nombre
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados


def registrar_lote(
    id_producto,
    fecha,
    volumen,
    tiempo_coccion,
    responsable,
    consumos,
    id_pedido=None,
    cantidad_kg=0
):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        volumen = Decimal(str(volumen))
        cantidad_kg = Decimal(str(cantidad_kg))

        # Un lote es de litros (liquidos) o de kilos (cubetas, vasos)
        if volumen <= 0 and cantidad_kg <= 0:
            raise ValueError("La cantidad producida debe ser mayor a cero.")

        if not consumos:
            raise ValueError("Debes registrar al menos un insumo.")

        # Verificar que el producto exista
        cursor.execute("""
            select id_producto
            from productos
            where id_producto = %s
        """, (id_producto,))

        if cursor.fetchone() is None:
            raise ValueError("El producto no existe.")

        # Verificar que el pedido exista y no tenga otro lote
        if id_pedido is not None:

            cursor.execute("""
                select id_pedido
                from pedidos
                where id_pedido = %s
            """, (id_pedido,))

            if cursor.fetchone() is None:
                raise ValueError("El pedido seleccionado no existe.")

            cursor.execute("""
                select id_lote
                from produccion_lotes
                where id_pedido = %s
            """, (id_pedido,))

            if cursor.fetchone() is not None:
                raise ValueError(
                    f"El pedido #{id_pedido} ya tiene un lote registrado."
                )

        # Registrar el lote
        cursor.execute("""
            insert into produccion_lotes
            (
                id_producto,
                id_pedido,
                fecha_produccion,
                volumen_litros,
                cantidad_kg,
                tiempo_coccion_min,
                responsable,
                estado
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            id_producto,
            id_pedido,
            fecha,
            volumen,
            cantidad_kg,
            tiempo_coccion,
            responsable,
            "En proceso"
        ))

        id_lote = cursor.lastrowid

        # Registrar consumos y actualizar inventario
        for consumo in consumos:

            id_insumo = consumo["id_insumo"]
            cantidad = Decimal(str(consumo["cantidad"]))

            if cantidad <= 0:
                raise ValueError("Las cantidades deben ser mayores a cero.")

            cursor.execute("""
                select stock_actual
                from insumos
                where id_insumo = %s
                for update
            """, (id_insumo,))

            resultado = cursor.fetchone()

            if resultado is None:
                raise ValueError(
                    f"El insumo {id_insumo} no existe."
                )

            stock = Decimal(str(resultado[0]))

            if cantidad > stock:
                raise ValueError(
                    f"Inventario insuficiente para el insumo {id_insumo}."
                )

            cursor.execute("""
                update insumos
                set stock_actual = stock_actual - %s
                where id_insumo = %s
            """, (cantidad, id_insumo))

            cursor.execute("""
                insert into consumo_insumos
                (id_lote, id_insumo, cantidad_utilizada)
                values (%s, %s, %s)
            """, (id_lote, id_insumo, cantidad))

        conexion.commit()

        return id_lote

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def obtener_lotes():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        select
            p.id_lote,
            pr.nombre as producto,
            p.fecha_produccion,
            p.volumen_litros,
            p.cantidad_kg,
            p.tiempo_coccion_min,
            p.responsable,
            p.estado
        from produccion_lotes p
        inner join productos pr
            on p.id_producto = pr.id_producto
        order by p.id_lote desc
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados


def registrar_merma(id_lote, id_insumo, cantidad, motivo, responsable):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cantidad = Decimal(str(cantidad))

        if cantidad <= Decimal("0"):
            raise ValueError("La cantidad debe ser mayor a cero.")

        cursor.execute("""
            select id_lote
            from produccion_lotes
            where id_lote = %s
        """, (id_lote,))

        if cursor.fetchone() is None:
            raise ValueError("El lote seleccionado no existe.")

        cursor.execute("""
            select coalesce(sum(cantidad_utilizada), 0)
            from consumo_insumos
            where id_lote = %s and id_insumo = %s
        """, (id_lote, id_insumo))

        consumo = Decimal(str(cursor.fetchone()[0]))

        cursor.execute("""
            select coalesce(sum(cantidad_perdida), 0)
            from control_mermas
            where id_lote = %s and id_insumo = %s
        """, (id_lote, id_insumo))

        merma_anterior = Decimal(str(cursor.fetchone()[0]))

        if merma_anterior + cantidad > consumo:
            raise ValueError(
                "La merma acumulada no puede superar "
                "la cantidad consumida en producción."
            )

        cursor.execute("""
            insert into control_mermas
            (id_lote, id_insumo, cantidad_perdida, motivo, responsable)
            values (%s, %s, %s, %s, %s)
        """, (id_lote, id_insumo, cantidad, motivo, responsable))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def obtener_mermas():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        select
            m.id_merma,
            m.id_lote,
            i.nombre as insumo,
            m.cantidad_perdida,
            i.unidad_medida,
            m.motivo,
            m.responsable,
            m.fecha_registro
        from control_mermas m
        inner join insumos i
            on m.id_insumo = i.id_insumo
        order by m.fecha_registro desc
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados


def obtener_insumos_por_lote(id_lote):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        select
            i.id_insumo,
            i.nombre,
            i.unidad_medida,
            c.cantidad_utilizada
        from consumo_insumos c
        inner join insumos i
            on c.id_insumo = i.id_insumo
        where c.id_lote = %s
        order by i.nombre
    """, (id_lote,))

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados


def obtener_clientes():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        select *
        from clientes
        order by nombre
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados


def registrar_cliente(nombre, tipo_cliente, telefono, correo, direccion):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            insert into clientes
            (nombre, tipo_cliente, telefono, correo, direccion)
            values (%s, %s, %s, %s, %s)
        """, (nombre, tipo_cliente, telefono, correo, direccion))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def registrar_pedido(id_cliente, fecha_entrega, prioridad, observaciones, productos_pedido):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        if not productos_pedido:
            raise ValueError("El pedido debe incluir al menos un producto.")

        total = Decimal("0.00")

        for producto in productos_pedido:
            cantidad = int(producto["cantidad"])

            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a cero.")

            cursor.execute("""
                select precio_venta
                from productos
                where id_producto = %s
            """, (producto["id_producto"],))

            resultado = cursor.fetchone()

            if resultado is None:
                raise ValueError("Uno de los productos no existe.")

            precio = Decimal(str(resultado[0]))
            total += precio * cantidad

        cursor.execute("""
            insert into pedidos
            (id_cliente, fecha_entrega, prioridad, total, observaciones)
            values (%s, %s, %s, %s, %s)
        """, (
            id_cliente,
            fecha_entrega,
            prioridad,
            total,
            observaciones
        ))

        id_pedido = cursor.lastrowid

        for producto in productos_pedido:

            cursor.execute("""
                select precio_venta
                from productos
                where id_producto = %s
            """, (producto["id_producto"],))

            precio = Decimal(str(cursor.fetchone()[0]))

            cursor.execute("""
                insert into detalle_pedido
                (id_pedido, id_producto, cantidad, precio_unitario)
                values (%s, %s, %s, %s)
            """, (
                id_pedido,
                producto["id_producto"],
                producto["cantidad"],
                precio
            ))

        conexion.commit()
        return id_pedido

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def obtener_pedidos():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        select
            p.id_pedido,
            c.nombre as cliente,
            p.fecha_pedido,
            p.fecha_entrega,
            p.estado,
            p.prioridad,
            p.total,
            p.observaciones
        from pedidos p
        inner join clientes c
            on p.id_cliente = c.id_cliente
        order by p.id_pedido desc
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados


def actualizar_estado_pedido(id_pedido, nuevo_estado):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            update pedidos
            set estado = %s
            where id_pedido = %s
        """, (nuevo_estado, id_pedido))

        if cursor.rowcount == 0:
            raise ValueError("No se encontró el pedido.")

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def obtener_pedidos_para_produccion():

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            select
                p.id_pedido,
                c.nombre as cliente,
                p.fecha_entrega,
                p.estado,
                dp.id_producto,
                pr.nombre as producto,
                dp.cantidad,
                pr.capacidad_ml,
                pr.capacidad_g,
                dp.cantidad * pr.capacidad_ml / 1000 as volumen_litros,
                dp.cantidad * pr.capacidad_g / 1000 as cantidad_kg
            from pedidos p
            inner join clientes c
                on p.id_cliente = c.id_cliente
            inner join detalle_pedido dp
                on p.id_pedido = dp.id_pedido
            inner join productos pr
                on dp.id_producto = pr.id_producto
            where p.estado = 'En preparación'
            and not exists (
                select 1
                from produccion_lotes pl
                where pl.id_pedido = p.id_pedido
            )
            order by p.fecha_entrega asc
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()

def finalizar_produccion(id_lote):

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    try:
        # Buscar el lote y su pedido relacionado
        cursor.execute("""
            select id_lote, id_pedido, estado
            from produccion_lotes
            where id_lote = %s
            for update
        """, (id_lote,))

        lote = cursor.fetchone()

        if lote is None:
            raise ValueError("No se encontró el lote.")

        if lote["estado"] == "Terminado":
            raise ValueError("Este lote ya está terminado.")

        # Finalizar el lote
        cursor.execute("""
            update produccion_lotes
            set estado = 'Terminado'
            where id_lote = %s
        """, (id_lote,))

        # Actualizar el pedido relacionado
        if lote["id_pedido"] is not None:

            cursor.execute("""
                update pedidos
                set estado = 'Listo'
                where id_pedido = %s
                  and estado = 'En preparación'
            """, (lote["id_pedido"],))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def obtener_pedidos_listos_para_entrega():

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        select
            p.id_pedido,
            c.nombre as cliente,
            p.fecha_entrega,
            p.prioridad,
            p.total,
            p.observaciones
        from pedidos p
        inner join clientes c
            on p.id_cliente = c.id_cliente
        where p.estado = 'Listo'
        order by p.fecha_entrega
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados


def registrar_salida_entrega(id_pedido, responsable, observaciones):

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            select estado
            from pedidos
            where id_pedido = %s
            for update
        """, (id_pedido,))

        pedido = cursor.fetchone()

        if pedido is None:
            raise ValueError("No se encontró el pedido.")

        if pedido["estado"] != "Listo":
            raise ValueError("El pedido todavía no está listo para entregar.")

        cursor.execute("""
            insert into entregas (
                id_pedido,
                responsable_entrega,
                observaciones,
                estado_entrega
            )
            values (%s, %s, %s, 'En tránsito')
        """, (id_pedido, responsable, observaciones))

        cursor.execute("""
            update pedidos
            set estado = 'En tránsito'
            where id_pedido = %s
        """, (id_pedido,))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def obtener_entregas_en_transito():

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        select
            e.id_entrega,
            e.id_pedido,
            c.nombre as cliente,
            e.fecha_salida,
            e.responsable_entrega,
            e.observaciones,
            e.estado_entrega
        from entregas e
        inner join pedidos p
            on e.id_pedido = p.id_pedido
        inner join clientes c
            on p.id_cliente = c.id_cliente
        where e.estado_entrega = 'En tránsito'
        order by e.fecha_salida
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados


def confirmar_entrega(id_entrega, recibido_por):

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            select id_pedido, estado_entrega
            from entregas
            where id_entrega = %s
            for update
        """, (id_entrega,))

        entrega = cursor.fetchone()

        if entrega is None:
            raise ValueError("No se encontró la entrega.")

        if entrega["estado_entrega"] != "En tránsito":
            raise ValueError("Esta entrega ya fue confirmada.")

        cursor.execute("""
            update entregas
            set estado_entrega = 'Entregado',
                recibido_por = %s,
                fecha_recepcion = current_timestamp
            where id_entrega = %s
        """, (recibido_por, id_entrega))

        cursor.execute("""
            update pedidos
            set estado = 'Entregado'
            where id_pedido = %s
        """, (entrega["id_pedido"],))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def obtener_historial_entregas():

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        select
            e.id_entrega,
            e.id_pedido,
            c.nombre as cliente,
            e.fecha_salida,
            e.responsable_entrega,
            e.recibido_por,
            e.fecha_recepcion,
            e.estado_entrega,
            e.observaciones
        from entregas e
        inner join pedidos p
            on e.id_pedido = p.id_pedido
        inner join clientes c
            on p.id_cliente = c.id_cliente
        order by e.id_entrega desc
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    return resultados