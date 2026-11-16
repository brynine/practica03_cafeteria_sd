from concurrent import futures
from threading import Lock

import grpc

from src.cocina import cocina_pb2, cocina_pb2_grpc


class CocinaService(cocina_pb2_grpc.CocinaServiceServicer):

    def __init__(self):
        # Pedidos registrados temporalmente en Cocina
        self.ordenes = {}
        self.candado = Lock()

    def RecibirPedido(self, request, context):
        pedido_id = request.pedido_id.strip()
        producto = request.producto.strip()
        cantidad = request.cantidad

        if not pedido_id or not producto or cantidad <= 0:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT, "Los datos del pedido no son válidos"
            )

        with self.candado:
            if pedido_id in self.ordenes:
                orden = self.ordenes[pedido_id]

                if orden["producto"] != producto or orden["cantidad"] != cantidad:
                    context.abort(
                        grpc.StatusCode.ALREADY_EXISTS,
                        "El pedido ya existe con otros datos",
                    )

            else:
                orden = {
                    "producto": producto,
                    "cantidad": cantidad,
                    "estado": "EN_PREPARACION",
                }

                self.ordenes[pedido_id] = orden

                print(f"Pedido recibido en Cocina: {pedido_id}")

            estado = orden["estado"]

        return cocina_pb2.EstadoCocinaRespuesta(pedido_id=pedido_id, estado=estado)

    def ConsultarEstado(self, request, context):
        pedido_id = request.pedido_id.strip()

        with self.candado:
            orden = self.ordenes.get(pedido_id)

            if orden is None:
                context.abort(
                    grpc.StatusCode.NOT_FOUND, "Pedido no encontrado en Cocina"
                )

            estado = orden["estado"]

        return cocina_pb2.EstadoCocinaRespuesta(pedido_id=pedido_id, estado=estado)

    def MarcarListo(self, request, context):
        pedido_id = request.pedido_id.strip()

        with self.candado:
            orden = self.ordenes.get(pedido_id)

            if orden is None:
                context.abort(
                    grpc.StatusCode.NOT_FOUND, "Pedido no encontrado en Cocina"
                )

            orden["estado"] = "LISTO"

            print(f"Pedido listo en Cocina: {pedido_id}")

        return cocina_pb2.EstadoCocinaRespuesta(pedido_id=pedido_id, estado="LISTO")


def iniciar_servidor():
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=4))

    cocina_pb2_grpc.add_CocinaServiceServicer_to_server(CocinaService(), servidor)

    servidor.add_insecure_port("127.0.0.1:50053")

    servidor.start()

    print("Servicio de Cocina activo en puerto 50053")

    servidor.wait_for_termination()


if __name__ == "__main__":
    iniciar_servidor()
