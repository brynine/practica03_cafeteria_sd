# Prueba: microservicio de Caja no disponible

## Objetivo

Comprobar cómo responde el sistema distribuido de la cafetería cuando el microservicio de Caja deja de estar disponible durante una solicitud de pago, verificando que la API continúe funcionando y que el pedido pueda recuperarse cuando el servicio vuelva a estar activo.

## Mecanismo evaluado

**gRPC (comunicación síncrona).**

Este mecanismo se utiliza para comunicar la API de Pedidos con el microservicio de Caja, encargado de registrar y confirmar los pagos simulados.

## Procedimiento

1. Creé un pedido nuevo desde la interfaz web de la cafetería, utilizando el producto "Cafe prueba fallo" con una cantidad de 1.
2. Comprobé que el pedido se registró con el estado `PENDIENTE_PAGO`.
3. Detuve manualmente el microservicio de Caja desde la terminal de VS Code mediante `Ctrl + C`.
4. Intenté registrar el pago desde la interfaz web mientras Caja estaba detenida.
5. Consulté nuevamente el pedido para comprobar su estado y verificar que la API seguía funcionando.
6. Volví a iniciar el microservicio de Caja y repetí la solicitud de pago utilizando el mismo pedido.
7. Comprobé que el pago se registró correctamente y que el estado cambió a `PAGADO`.

## Resultados obtenidos

- **Código HTTP al fallar Caja:** `503 Service Unavailable`, según la respuesta configurada en la API.
- **Código de error gRPC:** `UNAVAILABLE`.
- **Estado del pedido después del fallo:** `PAGO_PENDIENTE_VERIFICACION`.
- **¿La API siguió funcionando?:** Sí. Pude consultar el pedido y comprobar su estado sin que la aplicación se detuviera.
- **Estado después del reintento:** `PAGADO`.
- **Resultado de la recuperación:** El sistema registró el pago y devolvió un identificador `pago_id`.

## Análisis

Durante la prueba pude comprobar que la caída del microservicio de Caja no provoca que todo el sistema deje de funcionar. Cuando intenté registrar el pago con Caja detenida, la API mostró un error indicando que no podía comunicarse con ese servicio.

El error gRPC recibido fue `UNAVAILABLE`, lo que significa que el servicio remoto no estaba disponible para atender la solicitud. En lugar de cerrar la aplicación o eliminar el pedido, el sistema cambió su estado a `PAGO_PENDIENTE_VERIFICACION`.

Considero que este comportamiento es importante porque, cuando existe un problema de comunicación entre servicios, no siempre podemos saber si la operación llegó a ejecutarse. Por eso, es mejor mantener el pedido pendiente de verificación antes que asumir directamente que el pago fue rechazado.

Después de iniciar nuevamente Caja, repetí la solicitud de pago con el mismo identificador. Esta vez la comunicación funcionó correctamente, se registró el pago y el pedido cambió a `PAGADO`.

También pude comprobar que la API REST continuó atendiendo las consultas mientras Caja estaba detenida. Esto demuestra que los procesos funcionan de manera independiente y que un fallo en uno de ellos no necesariamente debe detener a los demás.

Una limitación de la implementación actual es que los datos se almacenan en memoria. Por esta razón, si un servicio se reinicia puede perder los registros que tenía almacenados. Además, la recuperación del pago requiere realizar nuevamente la solicitud, ya que todavía no se implementan reintentos automáticos.

## Conclusión

Con esta prueba comprobé que el sistema puede manejar de forma controlada la falta de disponibilidad del microservicio de Caja. La API permitió conservar y consultar el pedido durante el fallo y, una vez recuperado el servicio, pude completar el pago mediante un nuevo intento.

La prueba también me permitió comprender la importancia de utilizar tiempos de espera, manejar errores de comunicación y conservar estados intermedios en un sistema distribuido.