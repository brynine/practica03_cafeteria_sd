from threading import Lock
from uuid import uuid4

import grpc
from fastapi import (
    BackgroundTasks,
    FastAPI,
    Header,
    HTTPException,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field

from src.caja import caja_pb2, caja_pb2_grpc
from src.facturacion import facturacion_pb2, facturacion_pb2_grpc
from src.cocina import cocina_pb2, cocina_pb2_grpc

from pathlib import Path
from fastapi.responses import FileResponse

app = FastAPI(title="Cafetería Universitaria - Pedidos")


@app.get("/app", include_in_schema=False)
def mostrar_interfaz():
    ruta_html = Path(__file__).resolve().parents[1] / "web" / "index.html"

    return FileResponse(ruta_html)


@app.get("/admin", include_in_schema=False)
def mostrar_administracion():
    ruta_html = Path(__file__).resolve().parents[1] / "web" / "admin.html"

    return FileResponse(ruta_html)


# Almacenamiento temporal en memoria
pedidos = {}
claves_idempotencia = {}
candado = Lock()
conexiones_ws = {}


class PedidoCrear(BaseModel):
    producto: str = Field(min_length=1)
    cantidad: int = Field(gt=0)


@app.get("/salud")
def verificar_salud():
    return {"estado": "activo"}


@app.post("/pedidos", status_code=201)
def crear_pedido(
    datos: PedidoCrear,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1),
):
    with candado:
        pedido_id_existente = claves_idempotencia.get(idempotency_key)

        if pedido_id_existente is not None:
            pedido_existente = pedidos[pedido_id_existente]

            if (
                pedido_existente["producto"] != datos.producto
                or pedido_existente["cantidad"] != datos.cantidad
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Clave de idempotencia utilizada con otros datos",
                )

            response.status_code = 200
            return pedido_existente

        pedido_id = str(uuid4())

        pedido = {
            "pedido_id": pedido_id,
            "producto": datos.producto,
            "cantidad": datos.cantidad,
            "estado": "PENDIENTE_PAGO",
        }

        pedidos[pedido_id] = pedido
        claves_idempotencia[idempotency_key] = pedido_id

        return pedido


@app.get("/pedidos/{pedido_id}")
def consultar_pedido(pedido_id: str):
    with candado:
        pedido = pedidos.get(pedido_id)

        if pedido is None:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        return pedido.copy()


# Nuevo endpoint: solicitar el pago mediante gRPC
@app.post("/pedidos/{pedido_id}/pagar")
def pagar_pedido(pedido_id: str):

    with candado:
        pedido = pedidos.get(pedido_id)

        if pedido is None:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        # Si ya fue pagado, no necesitamos repetir la operación
        if pedido.get("pago_id"):
            return pedido.copy()

    try:
        # Abrir conexión con el microservicio de Caja
        with grpc.insecure_channel("127.0.0.1:50051") as canal:
            cliente = caja_pb2_grpc.CajaServiceStub(canal)

            solicitud = caja_pb2.PagoSolicitud(pedido_id=pedido_id)

            # Esperar como máximo 3 segundos
            respuesta = cliente.RegistrarPago(solicitud, timeout=3)

    except grpc.RpcError as error:
        # No sabemos si Caja alcanzó a registrar el pago
        with candado:
            pedido = pedidos[pedido_id]

            if not pedido.get("pago_id"):
                pedido["estado"] = "PAGO_PENDIENTE_VERIFICACION"

        raise HTTPException(
            status_code=503,
            detail={
                "mensaje": "No se pudo confirmar el pago con Caja",
                "pedido_id": pedido_id,
                "codigo_grpc": error.code().name,
            },
        ) from error

    if respuesta.estado != "APROBADO":
        with candado:
            pedido = pedidos[pedido_id]

            if not pedido.get("pago_id"):
                pedido["estado"] = "PAGO_PENDIENTE_VERIFICACION"

        raise HTTPException(
            status_code=502, detail="Caja no confirmó la aprobación del pago"
        )

    # Actualizar el pedido después de recibir la aprobación
    with candado:
        pedido = pedidos[pedido_id]
        pedido["estado"] = "PAGADO"
        pedido["pago_id"] = respuesta.pago_id

        return pedido.copy()


@app.post("/pedidos/{pedido_id}/facturar")
def facturar_pedido(pedido_id: str):

    with candado:
        pedido = pedidos.get(pedido_id)

        if pedido is None:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        # No emitir nuevamente un comprobante existente
        if pedido.get("comprobante_id"):
            return pedido.copy()

        if pedido["estado"] == "FACTURACION_EN_PROCESO":
            raise HTTPException(
                status_code=409, detail="La facturación ya está en proceso"
            )

        # Solo se pueden facturar pedidos pagados
        if pedido["estado"] not in ("PAGADO", "FACTURACION_PENDIENTE_VERIFICACION"):
            raise HTTPException(
                status_code=409, detail="El pedido todavía no tiene un pago confirmado"
            )

        pago_id = pedido.get("pago_id")

        if not pago_id:
            raise HTTPException(
                status_code=409, detail="El pedido no tiene un identificador de pago"
            )

        pedido["estado"] = "FACTURACION_EN_PROCESO"

    try:
        with grpc.insecure_channel("127.0.0.1:50052") as canal:

            cliente = facturacion_pb2_grpc.FacturacionServiceStub(canal)

            solicitud = facturacion_pb2.ComprobanteSolicitud(
                pedido_id=pedido_id, pago_id=pago_id
            )

            respuesta = cliente.EmitirComprobante(solicitud, timeout=3)

    except grpc.RpcError as error:

        with candado:
            pedido = pedidos[pedido_id]
            pedido["estado"] = "FACTURACION_PENDIENTE_VERIFICACION"

        raise HTTPException(
            status_code=503,
            detail={
                "mensaje": "No se pudo confirmar la facturación",
                "pedido_id": pedido_id,
                "codigo_grpc": error.code().name,
            },
        ) from error

    # Comprobar los datos que devolvió Facturación
    if (
        respuesta.estado != "EMITIDO"
        or respuesta.pedido_id != pedido_id
        or respuesta.pago_id != pago_id
        or not respuesta.comprobante_id
    ):
        with candado:
            pedido = pedidos[pedido_id]
            pedido["estado"] = "FACTURACION_PENDIENTE_VERIFICACION"

        raise HTTPException(
            status_code=502, detail="Facturación devolvió una respuesta no válida"
        )

    # Registrar el comprobante confirmado
    with candado:
        pedido = pedidos[pedido_id]

        pedido["estado"] = "FACTURADO"
        pedido["comprobante_id"] = respuesta.comprobante_id

        return pedido.copy()


@app.post("/pedidos/{pedido_id}/enviar-cocina")
def enviar_cocina(pedido_id: str):

    with candado:
        pedido = pedidos.get(pedido_id)

        if pedido is None:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        # Evitar enviar nuevamente pedidos ya procesados
        if pedido["estado"] in ("EN_PREPARACION", "LISTO"):
            return pedido.copy()

        if pedido["estado"] == "ENVIO_COCINA_EN_PROCESO":
            raise HTTPException(
                status_code=409, detail="El envío a Cocina ya está en proceso"
            )

        # Cocina solamente recibe pedidos facturados
        if pedido["estado"] not in ("FACTURADO", "COCINA_PENDIENTE_VERIFICACION"):
            raise HTTPException(
                status_code=409,
                detail="El pedido debe estar facturado antes de enviarse a Cocina",
            )

        producto = pedido["producto"]
        cantidad = pedido["cantidad"]
        pedido["estado"] = "ENVIO_COCINA_EN_PROCESO"

    try:
        with grpc.insecure_channel("127.0.0.1:50053") as canal:

            cliente = cocina_pb2_grpc.CocinaServiceStub(canal)

            solicitud = cocina_pb2.PedidoCocinaSolicitud(
                pedido_id=pedido_id, producto=producto, cantidad=cantidad
            )

            respuesta = cliente.RecibirPedido(solicitud, timeout=3)

    except grpc.RpcError as error:
        with candado:
            pedido = pedidos[pedido_id]
            pedido["estado"] = "COCINA_PENDIENTE_VERIFICACION"

        raise HTTPException(
            status_code=503,
            detail={
                "mensaje": "No se pudo confirmar la recepción en Cocina",
                "pedido_id": pedido_id,
                "codigo_grpc": error.code().name,
            },
        ) from error

    if respuesta.pedido_id != pedido_id or respuesta.estado not in (
        "EN_PREPARACION",
        "LISTO",
    ):
        with candado:
            pedido = pedidos[pedido_id]
            pedido["estado"] = "COCINA_PENDIENTE_VERIFICACION"

        raise HTTPException(
            status_code=502, detail="Cocina devolvió una respuesta no válida"
        )

    with candado:
        pedido = pedidos[pedido_id]
        pedido["estado"] = respuesta.estado

        return pedido.copy()


@app.post("/pedidos/{pedido_id}/marcar-listo")
def marcar_pedido_listo(pedido_id: str, background_tasks: BackgroundTasks):

    with candado:
        pedido = pedidos.get(pedido_id)

        if pedido is None:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        # Si ya está listo, devolver el estado actual
        if pedido["estado"] == "LISTO":
            return pedido.copy()

        if pedido["estado"] != "EN_PREPARACION":
            raise HTTPException(
                status_code=409, detail="El pedido no está en preparación"
            )

    try:
        with grpc.insecure_channel("127.0.0.1:50053") as canal:

            cliente = cocina_pb2_grpc.CocinaServiceStub(canal)

            solicitud = cocina_pb2.PedidoIdSolicitud(pedido_id=pedido_id)

            respuesta = cliente.MarcarListo(solicitud, timeout=3)

    except grpc.RpcError as error:
        raise HTTPException(
            status_code=503,
            detail={
                "mensaje": "No se pudo confirmar el estado de Cocina",
                "codigo_grpc": error.code().name,
            },
        ) from error

    if respuesta.pedido_id != pedido_id or respuesta.estado != "LISTO":
        raise HTTPException(
            status_code=502, detail="Cocina devolvió una respuesta no válida"
        )

    with candado:
        pedido = pedidos[pedido_id]

        # Comprobar si es la primera confirmación
        primera_confirmacion = pedido["estado"] != "LISTO"

        pedido["estado"] = "LISTO"
        resultado = pedido.copy()

    # Notificar al estudiante después de actualizar el estado
    if primera_confirmacion:
        background_tasks.add_task(notificar_pedido_listo, pedido_id)

    return resultado


@app.websocket("/ws/pedidos/{pedido_id}")
async def recibir_notificaciones(websocket: WebSocket, pedido_id: str):
    with candado:
        pedido = pedidos.get(pedido_id)
        estado_actual = pedido["estado"] if pedido else None

    if estado_actual is None:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    # Registrar la conexión asociada al pedido
    conexiones_ws.setdefault(pedido_id, set()).add(websocket)

    try:
        # Informar el estado actual al conectarse
        await websocket.send_json(
            {"tipo": "ESTADO_ACTUAL", "pedido_id": pedido_id, "estado": estado_actual}
        )

        # Mantener abierta la conexión
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        print(f"Cliente desconectado del pedido: {pedido_id}")

    finally:
        # Liberar la conexión al desconectarse
        conexiones_ws[pedido_id].discard(websocket)

        if not conexiones_ws[pedido_id]:
            del conexiones_ws[pedido_id]


# Enviar notificaciones cuando un pedido esté listo
async def notificar_pedido_listo(pedido_id: str):

    mensaje = {
        "tipo": "PEDIDO_LISTO",
        "pedido_id": pedido_id,
        "estado": "LISTO",
        "mensaje": "Tu pedido está listo para retirar",
    }

    # Copiar la colección para recorrerla con seguridad
    clientes = list(conexiones_ws.get(pedido_id, set()))

    for cliente in clientes:
        try:
            await cliente.send_json(mensaje)

        except (WebSocketDisconnect, RuntimeError, OSError):
            conexiones_ws.get(pedido_id, set()).discard(cliente)


@app.get("/admin/estadisticas")
def obtener_estadisticas():

    # Obtener una copia de los pedidos registrados
    with candado:
        lista_pedidos = [pedido.copy() for pedido in pedidos.values()]

    # Solo considerar ventas con pago confirmado
    ventas = [pedido for pedido in lista_pedidos if pedido.get("pago_id")]

    # Contar los pedidos según su estado actual
    pedidos_por_estado = {}

    for pedido in lista_pedidos:
        estado = pedido["estado"]

        pedidos_por_estado[estado] = pedidos_por_estado.get(estado, 0) + 1

    # Calcular unidades vendidas por producto
    unidades_por_producto = {}

    for pedido in ventas:
        producto = pedido["producto"]
        cantidad = pedido["cantidad"]

        unidades_por_producto[producto] = (
            unidades_por_producto.get(producto, 0) + cantidad
        )

    # Identificar el producto con más unidades vendidas
    producto_mas_vendido = None

    if unidades_por_producto:
        producto_mas_vendido = max(unidades_por_producto, key=unidades_por_producto.get)

    return {
        "total_pedidos": len(lista_pedidos),
        "ventas_confirmadas": len(ventas),
        "unidades_vendidas": sum(pedido["cantidad"] for pedido in ventas),
        "pedidos_facturados": sum(
            1 for pedido in lista_pedidos if pedido.get("comprobante_id")
        ),
        "pedidos_listos": sum(
            1 for pedido in lista_pedidos if pedido["estado"] == "LISTO"
        ),
        "pedidos_por_estado": pedidos_por_estado,
        "unidades_por_producto": unidades_por_producto,
        "producto_mas_vendido": producto_mas_vendido,
    }
