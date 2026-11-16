from concurrent import futures
from threading import Lock
from uuid import uuid4

import grpc

from src.caja import caja_pb2, caja_pb2_grpc


class CajaService(caja_pb2_grpc.CajaServiceServicer):

    def __init__(self):
        # Los pagos se almacenan temporalmente en memoria
        self.pagos = {}
        self.candado = Lock()

    def RegistrarPago(self, request, context):
        pedido_id = request.pedido_id.strip()

        if not pedido_id:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "El identificador del pedido es obligatorio",
            )

        with self.candado:
            # Evitar registrar dos pagos para el mismo pedido
            if pedido_id not in self.pagos:
                self.pagos[pedido_id] = str(uuid4())

                print(f"Pago registrado para pedido: {pedido_id}")

            pago_id = self.pagos[pedido_id]

        return caja_pb2.PagoRespuesta(
            pago_id=pago_id, pedido_id=pedido_id, estado="APROBADO"
        )


def iniciar_servidor():
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=4))

    caja_pb2_grpc.add_CajaServiceServicer_to_server(CajaService(), servidor)

    servidor.add_insecure_port("127.0.0.1:50051")

    servidor.start()

    print("Servicio de Caja activo en puerto 50051")

    servidor.wait_for_termination()


if __name__ == "__main__":
    iniciar_servidor()
