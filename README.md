# API Vehículo IoT (Práctica 2.5)

Este proyecto es una API hecha con **FastAPI** y **Python**, usando **Programación Orientada a Objetos**.

La API se conecta a mi base de datos **vehiculo_iot** en **Amazon RDS** y usa los **21 Stored Procedures**.

Con ella puedo:

- Ver el vehículo, sus comandos, su estado y su historial.
- Mover el vehículo con un comando.
- Ejecutar una DEMO (varios movimientos seguidos).
- Ver todo en tiempo real con **WebSocket**.

Todo corre en mi computadora (`localhost:8000`). No está publicado en internet. Eso es de la práctica 2.6.

---

## Cómo correr el proyecto

1. Crear el entorno virtual y activarlo:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

2. Instalar lo que necesita:

```powershell
pip install -r requirements.txt
```

3. Crear el archivo `.env` (copiando `.env.example`) y poner los datos de mi base de datos:

```text
DB_HOST=host_de_mi_rds
DB_PORT=3306
DB_NAME=vehiculo_iot
DB_USER=mi_usuario
DB_PASSWORD="mi_contraseña"
```

> El archivo `.env` no se sube a GitHub.

4. Probar que conecta con la base de datos:

```powershell
python probar_conexion.py
```

Debe decir: `Conexión exitosa con RDS`.

5. Encender la API:

```powershell
uvicorn main:app --reload --port 8000
```

6. Abrir en el navegador:

- Swagger (documentación): http://localhost:8000/docs
- WebSocket: `ws://localhost:8000/ws/vehiculo/5`

---

## Qué números uso en las URLs

En mi base de datos hay estos datos:

| Qué es | Número | Dónde lo pongo |
|---|---|---|
| Vehículo | **5** (es el único) | En la URL: `/vehiculos/5/...` |
| DEMO | **2** | En la URL (`/demos/2/...`) o en el JSON (`"demo_id": 2`) |
| Comandos | **14 al 22** | En el JSON: `"comando_id": 14` |

Los comandos del vehículo 5:

| id_comando | Nombre | codigo |
|---|---|---|
| 14 | AVANZAR | 1 |
| 15 | RETROCEDER | 2 |
| 16 | GIRAR_IZQUIERDA | 3 |
| 17 | GIRAR_DERECHA | 4 |
| 18 | SUBIR_BRAZO | 5 |
| 19 | BAJAR_BRAZO | 6 |
| 20 | ABRIR_PALA | 7 |
| 21 | CERRAR_PALA | 8 |
| 22 | DETENER | 9 |

> Ojo: para mover el vehículo uso el **id_comando** (14 al 22), no el **codigo** (1 al 9).

---

## Pruebas con GET

Los GET solo consultan. No llevan JSON.

La dirección base es `http://localhost:8000`.

| URL | Qué número lleva | Qué me muestra |
|---|---|---|
| `/vehiculos/` | Ninguno | Todos los vehículos |
| `/vehiculos/5` | **5** = id del vehículo | Los datos del vehículo 5 |
| `/vehiculos/5/estado` | **5** = id del vehículo | Su último estado |
| `/vehiculos/5/historial` | **5** = id del vehículo | Sus últimos 10 movimientos |
| `/vehiculos/5/detalle-completo` | **5** = id del vehículo | Vehículo, comandos, estado y DEMOs juntos |
| `/comandos/vehiculo/5` | **5** = id del vehículo | Sus comandos |
| `/demos/vehiculo/5` | **5** = id del vehículo | Sus DEMOs |
| `/demos/2/movimientos` | **2** = id de la DEMO | Los 8 movimientos de la DEMO |

Ejemplo completo:

```http
GET http://localhost:8000/vehiculos/5/historial
```

---

## Pruebas con POST

En Thunder Client: elijo **POST**, pongo la URL, voy a **Body → JSON**, pego el JSON y le doy **Send**.

### 1. Mover el vehículo (movimiento individual)

Este movimiento **sí se guarda en el historial**.

```http
POST http://localhost:8000/vehiculos/5/movimiento
```

- **5** = id del vehículo (va en la URL).
- **14** = id del comando AVANZAR (va en el JSON).

JSON Content:

```json
{
  "comando_id": 14,
  "origen": "THUNDER_CLIENT"
}
```

Respuesta (código 201):

```json
{
  "mensaje": "Movimiento individual procesado y registrado en historial exitosamente."
}
```

Para probar otro movimiento, cambio el número. Por ejemplo, `"comando_id": 16` para girar a la izquierda.

### 2. Iniciar la DEMO

Esta DEMO **no se guarda en el historial**.

```http
POST http://localhost:8000/vehiculos/5/demo/iniciar
```

- **5** = id del vehículo (va en la URL).
- **2** = id de la DEMO (va en el JSON).

JSON Content:

```json
{
  "demo_id": 2
}
```

Respuesta (código 200). Responde enseguida y la DEMO sigue corriendo:

```json
{
  "mensaje": "DEMO iniciada. Siga el avance por WebSocket.",
  "vehiculo_id": 5,
  "demo_id": 2,
  "total_movimientos": 8
}
```

### 3. Detener la DEMO

No lleva JSON. Solo sirve si la DEMO está corriendo.

```http
POST http://localhost:8000/vehiculos/5/demo/detener
```

- **5** = id del vehículo.

---

## Cómo ver la DEMO en el WebSocket

Thunder Client no sirve para WebSocket. Uso la consola del navegador.

1. Abro el navegador y presiono **F12**. Voy a la pestaña **Console**.
2. Pego esto y presiono Enter (el **5** es el id del vehículo):

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/vehiculo/5");
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

3. Debe salir el mensaje `conexion_establecida`.
4. Dejo abierta esa pestaña y mando el POST de **Iniciar la DEMO**.
5. En la consola van saliendo los mensajes:

| Mensaje | Cuándo sale |
|---|---|
| `demo_inicio` | Cuando empieza la DEMO |
| `demo_movimiento` | En cada movimiento (salen 8) |
| `demo_fin` | Cuando termina |
| `demo_cancelada` | Si la detengo con el POST de detener |
| `movimiento_individual` | Cuando hago un movimiento individual |
| `demo_error` | Si algo falla en la DEMO |

Ejemplo de un mensaje:

```json
{
  "tipo": "demo_movimiento",
  "vehiculo_id": 5,
  "comando_id": 14,
  "codigo": 1,
  "demo_id": 2,
  "orden": 1,
  "duracion_ms": 1000,
  "pausa_ms": 500,
  "marca_temporal": "2026-10-16T10:30:00.123456"
}
```

---

## ¿Qué se guarda en el historial?

| Acción | ¿Se guarda en el historial? | Por qué |
|---|---|---|
| Movimiento individual | **Sí** | Es una orden que yo mando a mano. Debe quedar guardada. |
| DEMO | **No** | Es una secuencia ya armada. Si se guardara, el historial se llenaría de repetidos. |

El historial solo muestra los **10 más nuevos**. La base los ordena del más nuevo al más viejo y la API se queda con los primeros 10.

Para comprobar que la DEMO no guarda nada, cuento los registros antes y después:

```sql
SELECT COUNT(*) FROM historial_comandos;
```

El número debe ser el mismo.

---

## Crear, cambiar y borrar (POST)

Todo es con POST, porque la práctica pide solo GET y POST.

> **Cuidado:** no borrar el vehículo 5, porque es el único que hay. Estos ejemplos son para probar con cosas nuevas.

### Vehículos

| URL | Número | JSON Content |
|---|---|---|
| `/vehiculos/` | Ninguno | Ver abajo |
| `/vehiculos/5/actualizar` | **5** = id del vehículo | Ver abajo |
| `/vehiculos/5/eliminar` | **5** = id del vehículo | No lleva JSON |

Crear vehículo:

```json
{
  "nombre": "Excavadora 02",
  "descripcion": "Vehículo de prueba"
}
```

Actualizar vehículo:

```json
{
  "nombre": "Excavadora 01",
  "descripcion": "Excavadora con ESP32",
  "activo": true
}
```

### Comandos

| URL | Número |
|---|---|
| `/comandos/` | Ninguno (el id del vehículo va en el JSON) |
| `/comandos/14/actualizar` | **14** = id del comando |
| `/comandos/14/eliminar` | **14** = id del comando (no lleva JSON) |

Crear comando (el `codigo` es un número y no se puede repetir en el mismo vehículo):

```json
{
  "vehiculo_id": 5,
  "nombre": "GIRAR_360",
  "codigo": 10,
  "descripcion": "Gira sobre su propio eje"
}
```

Actualizar comando:

```json
{
  "nombre": "AVANZAR",
  "codigo": 1,
  "descripcion": "Mueve el vehículo hacia adelante",
  "activo": true
}
```

### DEMOs

| URL | Número |
|---|---|
| `/demos/` | Ninguno (el id del vehículo va en el JSON) |
| `/demos/2/actualizar` | **2** = id de la DEMO |
| `/demos/2/eliminar` | **2** = id de la DEMO (no lleva JSON) |

Crear DEMO:

```json
{
  "vehiculo_id": 5,
  "nombre": "Demo corta",
  "descripcion": "Prueba con pocos movimientos"
}
```

Actualizar DEMO:

```json
{
  "nombre": "Demo principal",
  "descripcion": "Secuencia principal",
  "activo": true
}
```

### Movimientos de una DEMO

| URL | Número |
|---|---|
| `/demos/2/movimientos` | **2** = id de la DEMO |
| `/demos/movimientos/{id}/actualizar` | **{id}** = id_demo_movimiento |
| `/demos/movimientos/{id}/eliminar` | **{id}** = id_demo_movimiento (no lleva JSON) |

El `id_demo_movimiento` lo veo con `GET /demos/2/movimientos`.

Agregar movimiento a la DEMO 2 (el `orden` no se puede repetir en la misma DEMO):

```json
{
  "comando_id": 14,
  "orden": 9,
  "duracion_ms": 1000,
  "pausa_ms": 500
}
```

Actualizar movimiento:

```json
{
  "comando_id": 15,
  "orden": 9,
  "duracion_ms": 2000,
  "pausa_ms": 500
}
```

> `duracion_ms` y `pausa_ms` están en milisegundos (1000 = 1 segundo).

---

## Los 21 Stored Procedures que uso

La API no escribe consultas SQL directas. Todo lo hace con los **21 Stored Procedures** de la base `vehiculo_iot`. Cada uno tiene su URL:

| # | Stored Procedure | Dónde lo uso |
|---|---|---|
| 1 | `sp_obtener_vehiculos` | GET `/vehiculos/` |
| 2 | `sp_obtener_vehiculo` | GET `/vehiculos/5` |
| 3 | `sp_crear_vehiculo` | POST `/vehiculos/` |
| 4 | `sp_actualizar_vehiculo` | POST `/vehiculos/5/actualizar` |
| 5 | `sp_eliminar_vehiculo` | POST `/vehiculos/5/eliminar` |
| 6 | `sp_obtener_comandos_vehiculo` | GET `/comandos/vehiculo/5` |
| 7 | `sp_crear_comando` | POST `/comandos/` |
| 8 | `sp_actualizar_comando` | POST `/comandos/14/actualizar` |
| 9 | `sp_eliminar_comando` | POST `/comandos/14/eliminar` |
| 10 | `sp_obtener_demos` | GET `/demos/vehiculo/5` |
| 11 | `sp_obtener_movimientos_demo` | GET `/demos/2/movimientos` y al iniciar la DEMO |
| 12 | `sp_crear_demo` | POST `/demos/` |
| 13 | `sp_actualizar_demo` | POST `/demos/2/actualizar` |
| 14 | `sp_eliminar_demo` | POST `/demos/2/eliminar` |
| 15 | `sp_agregar_movimiento_demo` | POST `/demos/2/movimientos` |
| 16 | `sp_actualizar_movimiento_demo` | POST `/demos/movimientos/{id}/actualizar` |
| 17 | `sp_eliminar_movimiento_demo` | POST `/demos/movimientos/{id}/eliminar` |
| 18 | `sp_obtener_estado` | GET `/vehiculos/5/estado` |
| 19 | `sp_actualizar_estado` | POST `/vehiculos/5/movimiento` y en cada paso de la DEMO |
| 20 | `sp_registrar_historial` | POST `/vehiculos/5/movimiento` (solo el individual, la DEMO no lo usa) |
| 21 | `sp_obtener_historial` | GET `/vehiculos/5/historial` |

Por grupos:

| Grupo | Cantidad |
|---|---|
| Vehículos | 5 |
| Comandos | 4 |
| DEMO y sus movimientos | 8 |
| Estado e historial | 4 |
| **Total** | **21** |

Para ver que los 21 existen en mi base de datos:

```sql
SELECT ROUTINE_NAME FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'vehiculo_iot' AND ROUTINE_TYPE = 'PROCEDURE'
ORDER BY ROUTINE_NAME;
```

---

## Códigos que me puede responder

| Código | Qué quiere decir |
|---|---|
| 200 / 201 | Salió bien |
| 400 | Algo está mal en los datos (por ejemplo, un comando que no es de ese vehículo) |
| 404 | No encontró el vehículo o el estado |
| 409 | Ya hay una DEMO corriendo en ese vehículo, o el dato ya existe |
| 422 | El JSON está mal escrito o le falta un campo |
| 500 | Error en el servidor o en la base de datos |

---

## Si algo falla

| Problema | Qué hago |
|---|---|
| No conecta con la base de datos | Reviso el `.env`. En AWS, la instancia debe permitir mi IP en el puerto 3306. |
| Sale `409` al iniciar la DEMO | Ya hay una corriendo. Espero a que termine o la detengo. |
| No salen mensajes en el WebSocket | Me conecto al vehículo **5** antes de iniciar la DEMO. |
| Sale `400` en el movimiento | Reviso que el `comando_id` sea de 14 a 22. |
| Sale error de módulo | Activo el `.venv` y repito `pip install -r requirements.txt`. |

---

## Carpetas del proyecto

```text
config/        Conexión a la base de datos
repositories/  Llaman a los Stored Procedures
services/      Reglas del movimiento y de la DEMO
routers/       Las URLs (GET, POST y WebSocket)
schemas/       Revisan el JSON que mando
ws_manager/    Maneja las conexiones WebSocket
main.py        Enciende la API
```
