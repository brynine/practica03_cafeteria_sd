# Prueba: control de pedidos duplicados mediante REST

## Objetivo

Comprobar que el sistema controla las solicitudes repetidas mediante una clave de idempotencia y evita registrar pedidos duplicados.

## Mecanismo evaluado

**REST (comunicación síncrona mediante HTTP).**

## Procedimiento

1. Consulté las estadísticas de pedidos.
2. Envié un pedido del producto "Prueba REST", con cantidad 2 y la clave `prueba-rest-001`.
3. Repetí la solicitud utilizando los mismos datos y la misma clave.
4. Realicé un tercer intento sin modificar la información.
5. Cambié la cantidad a 3, manteniendo la clave anterior.
6. Consulté nuevamente las estadísticas para revisar los pedidos registrados.

## Resultados obtenidos

- **Primera solicitud:** `201 Created`.
- **Segundo intento:** `200 OK`.
- **Tercer intento:** `200 OK`.
- **Solicitud con datos diferentes:** `409 Conflict`.
- **Mensaje de error:** `Clave de idempotencia utilizada con otros datos`.
- **Identificador del pedido original:** `5d4e30cb-7e62-41da-8d6c-a9ae509872e2`.
- **Reutilización del mismo identificador:** El código devuelve el pedido existente, pero falta registrar la comparación de identificadores de las respuestas.
- **Total de pedidos antes y después:** No se conservaron los valores en la evidencia presentada.

## Análisis

Durante la prueba observé que la API respondió de manera diferente según el tipo de solicitud.

En el primer intento devolvió `201 Created`, porque se trataba de un pedido nuevo. Al repetir la misma información con la misma clave, respondió `200 OK`, ya que el sistema reconoció el reintento.

Cuando cambié la cantidad y mantuve la clave, la API devolvió `409 Conflict`. Esto evita utilizar una misma clave para registrar pedidos con información diferente.

La implementación utiliza `Idempotency-Key` para identificar las solicitudes repetidas. Una limitación es que estas claves se almacenan en memoria, por lo que se pierden al reiniciar el servidor.

## Conclusión

La prueba permitió comprobar que la API distingue entre un pedido nuevo, un reintento y una solicitud con datos diferentes.

El comportamiento observado coincide con el control de idempotencia implementado. Para completar la evidencia de que no se registraron duplicados, queda pendiente documentar la comparación de identificadores y el total de pedidos antes y después de la prueba.
