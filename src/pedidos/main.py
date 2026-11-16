from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Cafetería Universitaria - Pedidos")

# Almacenamiento temporal de pedidos
pedidos = {}


# Estructura de los datos que envía el estudiante
class PedidoCrear(BaseModel):
    producto: str = Field(min_length=1)
    cantidad: int = Field(gt=0)


# Comprobar que la API se encuentra funcionando
@app.get("/salud")
def verificar_salud():
    return {"estado": "activo"}


# Crear un nuevo pedido
@app.post("/pedidos", status_code=201)
def crear_pedido(datos: PedidoCrear):
    pedido_id = str(uuid4())

    pedido = {
        "pedido_id": pedido_id,
        "producto": datos.producto,
        "cantidad": datos.cantidad,
        "estado": "PENDIENTE_PAGO",
    }

    pedidos[pedido_id] = pedido

    return pedido


# Consultar un pedido existente
@app.get("/pedidos/{pedido_id}")
def consultar_pedido(pedido_id: str):
    if pedido_id not in pedidos:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    return pedidos[pedido_id]
