# Prueba: microservicio de Caja no disponible

## Objetivo

Comprobar cómo responde el sistema cuando el microservicio de Caja deja de funcionar durante una solicitud de pago y verificar que el pedido pueda recuperarse cuando el servicio vuelva a estar disponible.

## Mecanismo evaluado

**gRPC (comunicación síncrona).**

Se utiliza para comunicar la API de Pedidos con el microservicio de Caja, encargado de registrar los pagos simulados.

## Procedimiento

1. Creé un pedido del producto "Cafe prueba fallo", con cantidad 1.
2. Comprobé que su estado inicial era `PENDIENTE_PAGO`.
3. Detuve el servicio de Caja desde VS Code utilizando `Ctrl + C`.
4. Intenté registrar el pago mientras Caja estaba detenida.
5. Consulté el pedido para comprobar su estado.
6. Reinicié Caja y repetí la solicitud de pago.
7. Verifiqué que el pedido cambiara al estado `PAGADO`.

## Resultados obtenidos

- **Respuesta HTTP ante el fallo:** `503 Service Unavailable`, según el manejo de errores implementado en la API.
- **Error gRPC:** `UNAVAILABLE`.
- **Estado después del fallo:** `PAGO_PENDIENTE_VERIFICACION`.
- **¿La API continuó funcionando?:** Sí, permitió consultar el pedido.
- **Estado después del reintento:** `PAGADO`.
- **Resultado final:** Se registró el pago y se obtuvo un `pago_id`.

## Análisis

Durante la prueba comprobé que detener Caja no provoca que toda la aplicación deje de funcionar. La API detectó el error de comunicación y mantuvo el pedido en un estado pendiente de verificación.

Este comportamiento es importante porque, cuando ocurre un fallo, no siempre se puede confirmar si la operación llegó a ejecutarse. Por eso, el sistema no debe asumir automáticamente que el pago fue rechazado.

Después de reiniciar Caja, repetí la solicitud y el pago se registró correctamente. También comprobé que la API podía consultar pedidos mientras el microservicio estaba detenido.

Una limitación es que los datos se almacenan en memoria y los reintentos deben realizarse manualmente.

## Conclusión

La prueba demostró que el sistema maneja de forma controlada la falta de disponibilidad de Caja. El pedido se conservó durante el fallo y fue posible completar el pago después de reiniciar el servicio.

Esto me permitió comprender la importancia de los tiempos de espera, el manejo de errores y los estados de recuperación en sistemas distribuidos.
