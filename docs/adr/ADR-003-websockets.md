# ADR-003: Uso de WebSockets para notificaciones en tiempo real

**Estado:** Aceptado  
**Sistema:** Cafetería Universitaria  
**Mecanismo:** WebSockets  
**Tipo de comunicación:** Bidireccional, con notificaciones asíncronas

## 1. Contexto

El sistema permite que los estudiantes creen pedidos y consulten su estado desde una interfaz web.

Cuando Cocina termina la preparación, es necesario avisar al estudiante que su pedido está listo para retirar, sin que tenga que actualizar constantemente la página.

## 2. Problema

REST permite consultar el estado de los pedidos, pero el estudiante tendría que realizar nuevas solicitudes para conocer cualquier cambio.

Se necesita un mecanismo que permita enviar notificaciones desde el servidor y manejar las desconexiones del navegador.

## 3. Alternativas consideradas

| Alternativa                   | Ventaja                                                    | Desventaja                                                                             |
| ----------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| REST con consultas periódicas | Sencillo de implementar con la API existente.              | Genera solicitudes repetidas y depende del intervalo de consulta.                      |
| WebSockets                    | Permite enviar mensajes mediante una conexión persistente. | Requiere gestionar conexiones y desconexiones.                                         |
| Kafka                         | Permite distribuir eventos asíncronos entre servicios.     | Necesita infraestructura adicional y otro mecanismo para comunicarse con el navegador. |

## 4. Decisión tomada

Se decidió utilizar WebSockets para notificar al estudiante cuando su pedido está listo.

Cuando Cocina confirma que terminó la preparación, la API actualiza el estado a `LISTO` y envía el evento `PEDIDO_LISTO` a los clientes conectados a ese pedido.

REST se mantiene para crear y consultar pedidos, mientras que WebSockets se utiliza para las notificaciones.

## 5. Justificación técnica

WebSockets permite mantener una conexión abierta entre el navegador y el servidor, de manera que la API puede enviar mensajes sin esperar una nueva solicitud HTTP.

En el proyecto se utilizó FastAPI para gestionar las conexiones y enviar mensajes JSON. Cada conexión se asocia con un `pedido_id` para identificar a qué estudiantes debe enviarse la notificación.

También se implementó `WebSocketDisconnect` para detectar cuando un cliente se desconecta y retirar su conexión.

Este mecanismo permite notificaciones asíncronas sin agregar un servidor de mensajería adicional.

## 6. Consecuencias

### Positivas

- El estudiante puede recibir una notificación cuando su pedido está listo.
- Evita consultar repetidamente el estado mediante REST.
- Se integra con FastAPI y JavaScript.
- Permite identificar las conexiones asociadas a cada pedido.
- La desconexión del estudiante no detiene la preparación.

### Negativas

- Se deben administrar las conexiones activas.
- Si el estudiante está desconectado, puede perder la notificación.
- No existe almacenamiento de mensajes pendientes.
- No se implementó una reconexión automática del cliente.

## 7. Evidencia de implementación

### Backend

**Archivo:** `src/pedidos/main.py`

**Endpoint:** `/ws/pedidos/{pedido_id}`

**Funciones implementadas:**

- `recibir_notificaciones()`: administra las conexiones WebSocket.
- `notificar_pedido_listo()`: envía el evento `PEDIDO_LISTO`.
- `marcar_pedido_listo()`: actualiza el estado del pedido y programa la notificación.

### Frontend

**Archivo:** `src/web/index.html`

La interfaz recibe el mensaje WebSocket y muestra el aviso:

**"Tu pedido está listo para retirar".**

**Prueba relacionada:** `docs/tests/websocket-desconexion-cliente.md`

**Escenario de calidad relacionado:** EC-03 — Recuperación ante desconexión del estudiante.

## 8. Resultados y limitaciones

Durante la prueba se cerró el navegador mientras el pedido estaba en preparación. El servidor detectó la desconexión y Cocina pudo continuar trabajando normalmente.

Después, el pedido llegó al estado `LISTO` y fue posible recuperar esa información mediante REST al regresar a la aplicación.

Con esta prueba se comprobó que la desconexión del estudiante no interrumpe el procesamiento. Sin embargo, las notificaciones enviadas mientras el cliente está desconectado no se recuperan automáticamente.
