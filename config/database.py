
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnection:
    """Administra las conexiones con la base de datos RDS."""

    def __init__(self):
        self.__host = os.getenv("DB_HOST")
        self.__port = int(os.getenv("DB_PORT", "3306"))
        self.__database = os.getenv("DB_NAME")
        self.__user = os.getenv("DB_USER")
        self.__password = os.getenv("DB_PASSWORD")

    def obtener_conexion(self):
        """Abre y devuelve una conexión con MySQL."""

        datos_requeridos = {
            "DB_HOST": self.__host,
            "DB_NAME": self.__database,
            "DB_USER": self.__user,
            "DB_PASSWORD": self.__password
        }

        faltantes = [
            nombre for nombre, valor in datos_requeridos.items()
            if not valor
        ]

        if faltantes:
            raise ValueError(
                f"Faltan variables de configuración: {', '.join(faltantes)}"
            )

        return pymysql.connect(
            host=self.__host,
            port=self.__port,
            database=self.__database,
            user=self.__user,
            password=self.__password,
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )
