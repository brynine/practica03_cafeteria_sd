# ADR-001: Uso de REST para la API de Pedidos

**Estado:** Aceptado  
**Sistema:** Cafetería Universitaria  
**Mecanismo:** REST mediante HTTP y JSON

## 1. Contexto

El sistema de la Cafetería Universitaria necesita que los estudiantes puedan crear pedidos y consultar su información desde una interfaz web.

También se requiere gestionar las operaciones de pago, facturación y preparación, además de consultar las estadísticas de ventas.

REST es un mecanismo obligatorio de esta práctica.

## 2. Problema

Se necesita una forma de comunicación que permita al navegador enviar solicitudes al sistema y recibir respuestas claras sobre el resultado de cada operación.

También se deben controlar las solicitudes repetidas para evitar la creación de pedidos duplicados.

## 3. Alternativas consideradas

| Mecanismo  | Ventaja                                                                         | Limitación para este uso                                                                        |
| ---------- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| REST       | Utiliza HTTP y es sencillo de consumir desde el navegador.                      | Para conocer cambios posteriores necesita nuevas consultas o complementarse con otro mecanismo. |
| gRPC       | Define contratos mediante Protocol Buffers y facilita llamadas entre servicios. | Requiere herramientas adicionales para utilizarlo directamente desde navegadores.               |
| WebSockets | Mantiene una conexión abierta para intercambiar mensajes.                       | No es necesario mantener una conexión persistente para cada operación de creación o consulta.   |

## 4. Decisión tomada

Se decidió utilizar REST como mecanismo principal de comunicación entre las interfaces web y la API de Pedidos, porque permite realizar las operaciones mediante solicitudes HTTP de forma sencilla.

Para las demás necesidades del sistema se utilizaron gRPC en la comunicación entre microservicios y WebSockets para las notificaciones al estudiante.

## 5. Justificación técnica

Se utilizó FastAPI porque facilita la creación de endpoints REST y el intercambio de información en formato JSON.

Los códigos HTTP permiten identificar el resultado de cada solicitud: `201` cuando se crea un pedido, `200` cuando una operación se realiza correctamente, `404` cuando no existe el pedido y `409` cuando hay un conflicto.

También se implementó la cabecera `Idempotency-Key` para reconocer solicitudes repetidas y evitar registrar el mismo pedido varias veces.

## 6. Consecuencias

### Positivas

- Facilita la comunicación entre el navegador y el sistema.
- Permite probar los endpoints desde Swagger.
- Los códigos HTTP ayudan a identificar errores y resultados.
- El control de idempotencia evita pedidos duplicados por reintentos.

### Negativas

- REST no envía notificaciones automáticamente cuando cambia el estado de un pedido.
- Las operaciones dependen de que la API esté disponible.
- Se necesita complementar REST con WebSockets para las notificaciones en tiempo real.

## 7. Evidencia de implementación

**Archivo principal:** `src/pedidos/main.py`

**Endpoints REST implementados:**

- `POST /pedidos`
- `GET /pedidos/{pedido_id}`
- `POST /pedidos/{pedido_id}/pagar`
- `POST /pedidos/{pedido_id}/facturar`
- `POST /pedidos/{pedido_id}/enviar-cocina`
- `POST /pedidos/{pedido_id}/marcar-listo`
- `GET /admin/estadisticas`
- `GET /salud`

**Prueba relacionada:** `docs/tests/rest-idempotencia.md`

**Escenario de calidad relacionado:** EC-02 — Confiabilidad ante pedidos duplicados.

## 8. Limitaciones

- Los pedidos y las claves de idempotencia se almacenan temporalmente en memoria.
- El control de idempotencia funciona en una única instancia del servidor.
- No existe autenticación ni autorización para restringir las operaciones.
