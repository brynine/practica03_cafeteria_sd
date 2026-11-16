# ADR-004: Selección de mecanismos de comunicación del sistema distribuido

**Estado:** Aceptado  
**Sistema:** Cafetería Universitaria  
**Mecanismos seleccionados:** REST, gRPC y WebSockets

## 1. Contexto

La práctica consiste en desarrollar un sistema distribuido para gestionar pedidos, pagos, facturación y preparación de alimentos en una cafetería universitaria.

Uno de los requisitos es utilizar tres mecanismos de comunicación integrados en un mismo flujo.

REST es obligatorio y los otros dos deben seleccionarse entre Sockets TCP, RPC/RMI, gRPC, Kafka y WebSockets. Al menos uno de los mecanismos adicionales debe permitir comunicación asíncrona.

## 2. Problema

Se necesitan mecanismos adecuados para comunicar la interfaz web con la API, coordinar los microservicios internos y enviar notificaciones al estudiante.

La selección debe considerar la funcionalidad de cada mecanismo, la facilidad de implementación y la complejidad del proyecto.

## 3. Alternativas consideradas

| Mecanismo   | Ventaja                                                             | Desventaja                                                                       |
| ----------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| REST        | Fácil de utilizar desde el navegador mediante HTTP y JSON.          | Necesita consultas adicionales para conocer cambios de estado.                   |
| Sockets TCP | Ofrece control directo sobre el intercambio de datos.               | Requiere desarrollar el protocolo de comunicación.                               |
| RPC/RMI     | Permite ejecutar métodos remotos.                                   | Java RMI está orientado principalmente a Java.                                   |
| gRPC        | Utiliza contratos `.proto` y facilita las llamadas entre servicios. | Requiere generar código y configurar los servicios.                              |
| Kafka       | Permite distribuir y almacenar eventos.                             | Necesita infraestructura adicional.                                              |
| WebSockets  | Permite enviar notificaciones mediante conexiones persistentes.     | Requiere administrar conexiones y no recupera mensajes perdidos automáticamente. |

## 4. Decisión tomada

Se seleccionaron **gRPC y WebSockets** como los dos mecanismos adicionales a REST.

Cada uno cumple una función específica:

- **REST:** comunicación entre las interfaces web y la API de Pedidos.
- **gRPC:** comunicación síncrona entre Pedidos, Caja, Facturación y Cocina.
- **WebSockets:** envío asíncrono de notificaciones al estudiante.

Esta combinación permite utilizar los tres mecanismos dentro del mismo procesamiento de pedidos.

## 5. Justificación técnica

### Selección de gRPC

Se eligió gRPC porque permite que los microservicios intercambien información mediante llamadas remotas y contratos definidos en archivos `.proto`.

Por ejemplo, la API necesita recibir una respuesta de Caja para saber si el pago fue aprobado.

También permite configurar tiempos de espera y controlar errores cuando un servicio no responde.

### Selección de WebSockets

Se eligió WebSockets porque permite enviar una notificación cuando el pedido está listo, sin que el estudiante tenga que consultar constantemente su estado.

Además, se integra con FastAPI y la interfaz web desarrollada en JavaScript.

### ¿Por qué no Sockets TCP?

Aunque permite comunicar procesos, habría sido necesario desarrollar manualmente el formato de los mensajes y el manejo del protocolo.

gRPC simplificó esta parte mediante contratos y herramientas existentes.

### ¿Por qué no RPC/RMI?

Java RMI está orientado principalmente a aplicaciones Java, mientras que nuestro proyecto está desarrollado en Python.

gRPC se adaptó mejor a las tecnologías utilizadas.

### ¿Por qué no Kafka?

Kafka permite manejar eventos asíncronos y resulta útil para sistemas que necesitan almacenar y distribuir eventos entre varios consumidores.

Sin embargo, nuestro proyecto solamente necesitaba enviar una notificación al estudiante cuando su pedido estuviera listo.

Utilizar Kafka habría agregado infraestructura y complejidad que no eran necesarias para el alcance de esta práctica.

## 6. Consecuencias

### Positivas

- Cada mecanismo cumple una responsabilidad específica.
- REST facilita la interacción con las interfaces web.
- gRPC permite coordinar los microservicios.
- WebSockets permite enviar notificaciones asíncronas.
- Los tres mecanismos están integrados en un mismo flujo.
- Se evita agregar infraestructura innecesaria.

### Negativas

- Es necesario configurar y mantener tres mecanismos diferentes.
- Las llamadas gRPC dependen de la disponibilidad de los servicios internos.
- Las conexiones WebSocket deben administrarse correctamente.
- No existe almacenamiento persistente de pedidos ni de notificaciones pendientes.

## 7. Integración de los mecanismos

El procesamiento de un pedido se realiza de la siguiente manera:

1. El estudiante crea un pedido mediante REST.
2. La API registra el pedido con estado `PENDIENTE_PAGO`.
3. Se solicita el pago y la API se comunica con Caja mediante gRPC.
4. Después se solicita la facturación mediante gRPC.
5. El pedido facturado se envía a Cocina mediante gRPC.
6. Cuando Cocina confirma que terminó, la API cambia el estado a `LISTO`.
7. La API envía el evento `PEDIDO_LISTO` al estudiante mediante WebSockets.

En la implementación actual, las operaciones se ejecutan manualmente desde la interfaz web para demostrar la comunicación entre los servicios.

## 8. Evidencia de implementación

### REST

**Archivo:** `src/pedidos/main.py`

**Prueba:** `docs/tests/rest-idempotencia.md`

**Escenario relacionado:** EC-02 — Confiabilidad ante pedidos duplicados.

### gRPC

**Contratos implementados:**

- `src/caja/caja.proto`
- `src/facturacion/facturacion.proto`
- `src/cocina/cocina.proto`

**Prueba:** `docs/tests/grpc-caja-no-disponible.md`

**Escenario relacionado:** EC-01 — Disponibilidad ante fallos de Caja.

### WebSockets

**Archivos:**

- `src/pedidos/main.py`
- `src/web/index.html`

**Prueba:** `docs/tests/websocket-desconexion-cliente.md`

**Escenario relacionado:** EC-03 — Recuperación ante desconexión del estudiante.

## 9. Conclusión de la decisión

La combinación de REST, gRPC y WebSockets permitió implementar las distintas comunicaciones del sistema de acuerdo con sus necesidades.

REST se utiliza para recibir solicitudes, gRPC para coordinar los microservicios y WebSockets para enviar notificaciones.

De esta manera, se cumple el requisito de utilizar tres mecanismos integrados, manteniendo una arquitectura sencilla para el alcance de la práctica.
