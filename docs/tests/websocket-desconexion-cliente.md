# Prueba: desconexión del cliente WebSocket

## Objetivo

Comprobar cómo responde el sistema cuando el estudiante pierde la conexión WebSocket durante la preparación de un pedido y verificar si puede recuperar su estado al regresar.

## Mecanismo evaluado

**WebSockets (notificaciones asíncronas).**

## Procedimiento

1. Creé un pedido del producto "Prueba desconexion", con cantidad 1.
2. Registré el pago, generé el comprobante y envié el pedido a Cocina.
3. Comprobé que su estado era `EN_PREPARACION`.
4. Cerré la pestaña del navegador para simular una desconexión.
5. Desde Swagger marqué el pedido como listo.
6. Abrí nuevamente la aplicación y consulté el pedido con su identificador.

## Resultados obtenidos

- **Desconexión detectada:** Sí, el servidor registró `Cliente desconectado del pedido`.
- **Respuesta al marcar el pedido como listo:** `200 OK`.
- **Estado final del pedido:** `LISTO`.
- **¿El procesamiento continuó?:** Sí.
- **¿Se recuperó el estado mediante REST?:** Sí.
- **¿Se restableció la conexión WebSocket?:** Sí, la interfaz mostró `WebSocket conectado`.
- **¿Se recuperó la notificación perdida?:** No se observó un nuevo evento `PEDIDO_LISTO` al reconectarse.

## Análisis

Durante la prueba comprobé que la desconexión del estudiante no impide que Cocina termine de preparar el pedido. Esto ocurre porque el procesamiento se realiza en los servicios del sistema y no depende de que el navegador permanezca abierto.

También pude observar la diferencia entre REST y WebSockets. REST permite consultar el estado actual del pedido, mientras que WebSockets envía una notificación cuando ocurre un cambio y el cliente está conectado.

Al regresar a la aplicación, pude consultar mediante REST que el pedido estaba `LISTO`, pero no recibí nuevamente la notificación anterior.

Una limitación es que el sistema no almacena los mensajes pendientes para enviarlos después. Además, si la API se reinicia, se pierden los pedidos guardados en memoria y las conexiones activas.

## Conclusión

La prueba demostró que el sistema puede continuar procesando un pedido aunque el estudiante se desconecte.

También comprobé que REST permite recuperar el estado del pedido al regresar a la aplicación. Sin embargo, WebSockets no garantiza la entrega de una notificación enviada mientras el cliente está desconectado.
