from threading import Lock
from uuid import uuid4

import grpc
from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, Field

from src.caja import caja_pb2, caja_pb2_grpc
from src.facturacion import facturacion_pb2, facturacion_pb2_grpc

app = FastAPI(title="Cafetería Universitaria - Pedidos")

# Almacenamiento temporal en memoria
pedidos = {}
claves_idempotencia = {}
candado = Lock()


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
