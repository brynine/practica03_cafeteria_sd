# ADR-002: Uso de gRPC para la comunicación entre microservicios

**Estado:** Aceptado  
**Sistema:** Cafetería Universitaria  
**Mecanismo:** gRPC con Protocol Buffers  
**Tipo de comunicación:** Síncrona

## 1. Contexto

El sistema de la Cafetería Universitaria tiene servicios independientes para gestionar pedidos, pagos, facturación y preparación de alimentos.

La API de Pedidos necesita comunicarse con Caja, Facturación y Cocina para coordinar las operaciones mediante contratos de comunicación definidos.

## 2. Problema

Se necesita un mecanismo que permita realizar solicitudes entre los microservicios, recibir respuestas y manejar errores cuando alguno no esté disponible.

También es importante definir qué datos intercambia cada servicio.

## 3. Alternativas consideradas

| Alternativa | Ventaja                                                                | Desventaja                                                                 |
| ----------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| REST        | Fácil de implementar y probar mediante HTTP.                           | Requiere definir y mantener los contratos de comunicación entre servicios. |
| gRPC        | Utiliza contratos `.proto` y genera código para clientes y servidores. | Necesita configuración y generación de archivos adicionales.               |
| Sockets TCP | Permite controlar directamente la comunicación.                        | Requiere implementar el formato de mensajes y manejo de conexiones.        |
| RPC/RMI     | Facilita la ejecución de métodos remotos.                              | Java RMI está orientado principalmente a Java.                             |

## 4. Decisión tomada

Se decidió utilizar gRPC para comunicar la API de Pedidos con Caja, Facturación y Cocina, porque permite realizar llamadas remotas mediante operaciones definidas.

REST se mantuvo para la comunicación con las interfaces web, mientras que gRPC se utilizó para las operaciones internas del sistema.

## 5. Justificación técnica

Los archivos `.proto` permiten definir los métodos y mensajes que utiliza cada microservicio. A partir de estos contratos se generan los archivos Python necesarios para realizar las llamadas mediante stubs.

La comunicación es síncrona porque la API necesita conocer el resultado de operaciones como registrar un pago o emitir un comprobante antes de actualizar el estado del pedido.

También se configuró un **timeout de 3 segundos** y un manejo de errores gRPC para evitar esperas indefinidas cuando un servicio no responde.

## 6. Consecuencias

### Positivas

- Permite comunicar los microservicios mediante contratos definidos.
- Facilita el intercambio de datos con Protocol Buffers.
- Permite identificar errores de comunicación.
- Mantiene separados los servicios de Caja, Facturación y Cocina.

### Negativas

- Requiere configurar gRPC y generar los archivos Python desde los contratos.
- Las operaciones dependen de la disponibilidad de los servicios internos.
- Es necesario controlar los tiempos de espera y posibles fallos de comunicación.

## 7. Evidencia de implementación

### Servicios

**Caja**

- Puerto: `50051`
- Operación: `RegistrarPago`
- Contrato: `src/caja/caja.proto`

**Facturación**

- Puerto: `50052`
- Operación: `EmitirComprobante`
- Contrato: `src/facturacion/facturacion.proto`

**Cocina**

- Puerto: `50053`
- Operaciones: `RecibirPedido` y `MarcarListo`
- Contrato: `src/cocina/cocina.proto`

### Integración

**Archivo principal:** `src/pedidos/main.py`

La API utiliza clientes gRPC para solicitar operaciones a los microservicios internos.

**Prueba relacionada:** `docs/tests/grpc-caja-no-disponible.md`

**Escenario de calidad relacionado:** EC-01 — Disponibilidad ante fallos de Caja.

## 8. Limitaciones

- Los servicios se ejecutan por separado, pero en una misma computadora.
- Las llamadas gRPC son síncronas y dependen de que los servicios respondan.
- Se utiliza un timeout para controlar la espera.
- Los datos se almacenan temporalmente en memoria.
- La recuperación ante fallos requiere reintentos y no está completamente automatizada.
