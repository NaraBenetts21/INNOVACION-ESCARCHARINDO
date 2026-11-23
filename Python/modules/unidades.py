"""Captura de cantidades con selector de unidad.

La base de datos guarda cada insumo en su unidad base (kg, L o piezas).
Aquí la persona puede escribir la cantidad en otra unidad de la misma
familia (g en lugar de kg, ml en lugar de L) y se convierte a la unidad
base antes de guardar.
"""

from decimal import Decimal, ROUND_HALF_UP

import streamlit as st

# Valor de cada unidad medido en la unidad más pequeña de su familia
FAMILIAS = {
    "masa": {"g": Decimal("1"), "kg": Decimal("1000")},
    "volumen": {"ml": Decimal("1"), "l": Decimal("1000")},
}

# Cómo se muestra cada unidad en pantalla
ETIQUETAS = {"g": "g", "kg": "kg", "ml": "ml", "l": "L"}

# Nombres con los que pueden venir escritas las unidades en la base de datos
ALIAS = {
    "kg": "kg", "kilo": "kg", "kilos": "kg", "kilogramo": "kg", "kilogramos": "kg",
    "g": "g", "gr": "g", "gramo": "g", "gramos": "g",
    "l": "l", "lt": "l", "litro": "l", "litros": "l",
    "ml": "ml", "mililitro": "ml", "mililitros": "ml",
}


def normalizar(unidad):
    """Devuelve la unidad en formato estándar (kg, g, l, ml) o None."""
    return ALIAS.get(str(unidad).strip().lower())


def unidades_compatibles(unidad_base):
    """Unidades entre las que se puede elegir. La base va primero."""
    base = normalizar(unidad_base)
    for familia in FAMILIAS.values():
        if base in familia:
            return [base] + [u for u in familia if u != base]
    return []


def convertir(cantidad, unidad_origen, unidad_base):
    """Convierte una cantidad a la unidad base. Devuelve Decimal con 3 decimales."""
    cantidad = Decimal(str(cantidad))
    origen = normalizar(unidad_origen)
    base = normalizar(unidad_base)

    for familia in FAMILIAS.values():
        if origen in familia and base in familia:
            cantidad = cantidad * familia[origen] / familia[base]
            break

    return cantidad.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def campo_cantidad(etiqueta, unidad_base, key, valor=0.0, minimo=0.0, paso=1.0):
    """Campo de cantidad con mini selector de unidad.

    Devuelve la cantidad ya convertida a la unidad base (Decimal).
    Si la unidad base no tiene equivalentes (por ejemplo, piezas),
    muestra solo el campo numérico.
    """
    opciones = unidades_compatibles(unidad_base)

    # Piezas u otras unidades sin conversión
    if not opciones:
        cantidad = st.number_input(
            f"{etiqueta} ({unidad_base})",
            min_value=minimo,
            value=valor,
            step=paso,
            key=f"{key}_cant"
        )
        return Decimal(str(cantidad))

    col_cantidad, col_unidad = st.columns([3, 1])

    cantidad = col_cantidad.number_input(
        etiqueta,
        min_value=minimo,
        value=valor,
        step=paso,
        format="%.3f",
        key=f"{key}_cant"
    )

    # La unidad base va en la llave para que el selector se reinicie
    # cuando cambia el insumo seleccionado.
    unidad = col_unidad.selectbox(
        "Unidad",
        opciones,
        format_func=lambda u: ETIQUETAS[u],
        key=f"{key}_{normalizar(unidad_base)}_uni"
    )

    return convertir(cantidad, unidad, unidad_base)