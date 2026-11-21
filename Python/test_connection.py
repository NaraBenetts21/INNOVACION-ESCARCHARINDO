from database.conexion import conectar

try:
    # establecer conexion
    conexion = conectar()

    if conexion.is_connected():

        print("================================")
        print(" CONEXION EXITOSA")
        print(" ESCARCHARINDO SIMULADOR")
        print("================================")

        cursor = conexion.cursor()

        # consultar base de datos actual
        cursor.execute("SELECT DATABASE()")

        resultado = cursor.fetchone()

        print("Base de datos:", resultado[0])

        # consultar tablas existentes
        cursor.execute("SHOW TABLES")

        print("\nTablas disponibles:")

        for tabla in cursor.fetchall():
            print("-", tabla[0])

        cursor.close()
        conexion.close()

except Exception as error:
    print("Error de conexion:")
    print(error)

from database.consultas import obtener_insumos

print("\nINVENTARIO ACTUAL:")

insumos = obtener_insumos()

for insumo in insumos:
    print(
        insumo["nombre"],
        "| Stock:", insumo["stock_actual"],
        "| Unidad:", insumo["unidad_medida"]
    )