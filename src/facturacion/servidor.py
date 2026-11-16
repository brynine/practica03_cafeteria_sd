from concurrent import futures
from threading import Lock
from uuid import uuid4

import grpc

from src.facturacion import (
    facturacion_pb2,
    facturacion_pb2_grpc,
)


class FacturacionService(facturacion_pb2_grpc.FacturacionServiceServicer):

    def __init__(self):
        self.comprobantes = {}
        self.candado = Lock()

    def EmitirComprobante(self, request, context):
        pedido_id = request.pedido_id.strip()
        pago_id = request.pago_id.strip()

        if not pedido_id or not pago_id:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT, "El pedido y el pago son obligatorios"
            )

        with self.candado:
            if pedido_id in self.comprobantes:
                comprobante = self.comprobantes[pedido_id]

                if comprobante["pago_id"] != pago_id:
                    context.abort(
                        grpc.StatusCode.ALREADY_EXISTS,
                        "El pedido ya tiene un comprobante asociado a otro pago",
                    )

            else:
                comprobante = {
                    "comprobante_id": str(uuid4()),
                    "pedido_id": pedido_id,
                    "pago_id": pago_id,
                    "estado": "EMITIDO",
                }

                self.comprobantes[pedido_id] = comprobante

                print(f"Comprobante emitido para pedido: {pedido_id}")

        return facturacion_pb2.ComprobanteRespuesta(**comprobante)


def iniciar_servidor():
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=4))

    facturacion_pb2_grpc.add_FacturacionServiceServicer_to_server(
        FacturacionService(), servidor
    )

    servidor.add_insecure_port("127.0.0.1:50052")

    servidor.start()

    print("Servicio de Facturación activo en puerto 50052")

    servidor.wait_for_termination()


if __name__ == "__main__":
    iniciar_servidor()
