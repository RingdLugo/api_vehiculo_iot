from config.database import DatabaseConnection


conexion = None

try:
    db = DatabaseConnection()
    conexion = db.obtener_conexion()

    with conexion.cursor() as cursor:
        cursor.execute("SELECT DATABASE() AS base_datos")
        resultado = cursor.fetchone()

    print("Conexión exitosa con RDS")
    print("Base de datos:", resultado["base_datos"])

except Exception as error:
    print("No se pudo conectar con RDS")
    print("Error:", error)

finally:
    if conexion is not None:
        conexion.close()
