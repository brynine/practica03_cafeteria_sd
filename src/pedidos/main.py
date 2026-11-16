from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI(title="Cafetería Universitaria - Pedidos")

# Almacenamiento temporal en memoria
pedidos = {}
claves_idempotencia = {}

# Evita que solicitudes simultáneas creen el mismo pedido
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
        # Comprobar si ya se utilizó esta clave
        pedido_id_existente = claves_idempotencia.get(idempotency_key)

        if pedido_id_existente is not None:
            pedido_existente = pedidos[pedido_id_existente]

            # No permitir reutilizar una clave con datos diferentes
            if (
                pedido_existente["producto"] != datos.producto
                or pedido_existente["cantidad"] != datos.cantidad
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Clave de idempotencia utilizada con otros datos",
                )

            # Devolver el pedido original sin crear otro
            response.status_code = 200
            return pedido_existente

        # Crear un pedido únicamente si la clave es nueva
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
    if pedido_id not in pedidos:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    return pedidos[pedido_id]
