# Escenarios de atributos de calidad

## Sistema distribuido de la Cafetería Universitaria

Los escenarios se presentan por orden de prioridad,
considerando la disponibilidad, la confiabilidad
y el funcionamiento correcto de los pedidos.

## EC-01. Disponibilidad ante fallos de Caja

**Prioridad:** Alta

- Fuente: Microservicio de Caja.
- Estímulo: Caja deja de responder durante un pago.
- Entorno: El sistema está funcionando y recibe solicitudes.
- Artefacto: API de Pedidos y comunicación gRPC.
- Respuesta: La API devuelve un error controlado y mantiene
  el pedido pendiente de verificación.
- Medida: HTTP 503 ante la indisponibilidad; la API
  continúa respondiendo consultas. La llamada gRPC
  tiene configurado un timeout de 3 segundos.

**Prueba relacionada:**
`docs/tests/grpc-caja-no-disponible.md`

## EC-02. Confiabilidad ante pedidos duplicados

**Prioridad:** Alta

- Fuente: Estudiante o cliente REST.
- Estímulo: Envía nuevamente un pedido utilizando
  la misma clave de idempotencia.
- Entorno: API REST funcionando normalmente.
- Artefacto: Servicio de Pedidos.
- Respuesta: Devuelve el pedido existente sin duplicarlo.
- Medida: Primera solicitud HTTP 201; reintento HTTP 200
  con el mismo identificador. Si los datos cambian,
  devuelve HTTP 409. Solo se registra un pedido.

**Prueba relacionada:**
`docs/tests/rest-idempotencia.md`

## EC-03. Recuperación ante desconexión del estudiante

**Prioridad:** Alta

- Fuente: Estudiante.
- Estímulo: Cierra la conexión WebSocket mientras
  su pedido está en preparación.
- Entorno: Cocina continúa procesando el pedido.
- Artefacto: API de Pedidos y conexión WebSocket.
- Respuesta: El sistema continúa el procesamiento.
  Cuando el estudiante regresa, puede consultar
  el estado mediante REST.
- Medida: El pedido llega a LISTO y puede recuperarse
  con HTTP 200 al consultar el identificador.

**Prueba relacionada:**
`docs/tests/websocket-desconexion-cliente.md`

## EC-04. Consistencia del procesamiento

**Prioridad:** Media

- Fuente: Usuario que ejecuta operaciones fuera de orden.
- Estímulo: Intenta facturar un pedido sin pagar
  o enviarlo a Cocina sin facturarlo.
- Entorno: El pedido existe, pero no ha cumplido
  los pasos anteriores.
- Artefacto: API de Pedidos.
- Respuesta: Rechaza la operación sin avanzar el estado.
- Medida: HTTP 409 y el pedido conserva su estado válido.

**Evidencia:**
Pruebas realizadas durante la integración de
Facturación y Cocina.

## EC-05. Modificabilidad de los servicios

**Prioridad:** Media

- Fuente: Desarrollador del sistema.
- Estímulo: Se incorpora el servicio de Cocina
  al flujo existente.
- Entorno: Caja, Facturación y Pedidos ya funcionan.
- Artefacto: Arquitectura de microservicios.
- Respuesta: Se crea el servicio de Cocina y se integra
  mediante un contrato gRPC, sin reescribir Caja
  ni Facturación.
- Medida propuesta: Verificar en Git que la integración
  incorpora Cocina y modifica el coordinador de Pedidos,
  sin requerir cambios en los servidores de Caja
  y Facturación.

**Evidencia:**
Commits de implementación e integración de Cocina.

## Justificación de prioridades

Los tres primeros escenarios se consideran de prioridad
alta porque representan situaciones que afectan
directamente la continuidad y confiabilidad de los pedidos.

Los escenarios de consistencia y modificabilidad
también son importantes, pero se consideran de prioridad
media para el alcance académico de esta implementación.

## Limitaciones

Las medidas corresponden a una implementación local,
con una instancia de cada servicio y almacenamiento
temporal en memoria.

No se garantiza la persistencia de datos ante reinicios
ni la recuperación automática de notificaciones perdidas.
