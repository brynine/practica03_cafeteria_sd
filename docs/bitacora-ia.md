# Bitácora de uso de inteligencia artificial

## 1. Objetivo

Durante el desarrollo de la Práctica 03 de Sistemas Distribuidos utilicé ChatGPT como una herramienta de apoyo para comprender mejor los temas estudiados en clase, resolver dudas de programación y revisar aspectos técnicos de mi implementación.

La herramienta también me proporcionó ejemplos y fragmentos de código que me sirvieron como referencia para desarrollar determinadas funcionalidades. Posteriormente, realicé las pruebas correspondientes en mi entorno de trabajo para comprobar su funcionamiento.

Además, utilicé la IA para mejorar la organización, ortografía y claridad de los documentos Markdown. En algunos casos también recibí propuestas de estructura y borradores que revisé para relacionarlos con el sistema desarrollado.

## 2. Registro de consultas relevantes

**Responsable de las consultas:** Estudiante desarrollador (trabajo individual).

| Tema consultado | Qué consulté | Qué respondió la IA | Cómo utilicé la respuesta |
|---|---|---|---|
| REST e idempotencia | Cómo funcionan las solicitudes HTTP y cómo evitar pedidos duplicados. | Explicó los códigos HTTP y mostró ejemplos con `Idempotency-Key`. | Utilicé las explicaciones y ejemplos como apoyo para implementar y probar el control de solicitudes repetidas. |
| Comunicación gRPC | Cómo se comunican los microservicios mediante Protocol Buffers y llamadas remotas. | Explicó los archivos `.proto`, los stubs, los servidores y los tiempos de espera. También proporcionó ejemplos de implementación. | Me apoyé en esos ejemplos para trabajar con Caja, Facturación y Cocina, y comprobé las comunicaciones ejecutando los servicios. |
| WebSockets | Cómo enviar una notificación cuando un pedido está listo. | Explicó las conexiones persistentes, los eventos y el manejo de desconexiones, con ejemplos de código. | Implementé y probé la recepción del evento `PEDIDO_LISTO` desde el navegador. |
| Errores y pruebas | Cómo interpretar errores de comunicación y respuestas HTTP. | Explicó errores como `UNAVAILABLE`, `409 Conflict` y `503 Service Unavailable`. | Utilicé las explicaciones para interpretar los resultados obtenidos al ejecutar mis pruebas. |
| Documentación Markdown | Cómo organizar y mejorar la redacción de documentos técnicos. | Sugirió estructuras, correcciones de redacción y borradores para la arquitectura, las pruebas y los ADR. | Revisé la documentación para que fuera clara, ordenada y coherente con la implementación y sus resultados. |
| Git y GitHub | Cómo registrar avances y solucionar problemas con Git. | Explicó comandos para agregar archivos, crear commits y corregir problemas con `.gitignore`. | Ejecuté los comandos en VS Code y comprobé los commits registrados en GitHub. |

## 3. Uso de IA en el código

Durante la implementación consulté ejemplos de código para comprender cómo desarrollar determinadas funcionalidades.

Entre los temas en los que recibí asistencia se encuentran la validación de pedidos, la comunicación gRPC, el manejo de excepciones, las conexiones WebSocket y la actualización de estados.

Los fragmentos utilizados a partir de las sugerencias de IA se identifican mediante comentarios en los archivos correspondientes.

El funcionamiento de estos componentes se comprobó ejecutando el sistema desde VS Code y realizando solicitudes desde Swagger y las interfaces web.

## 4. Uso de IA en la documentación

También utilicé ChatGPT como apoyo en la elaboración y revisión de los documentos Markdown de la práctica.

La herramienta me ayudó a organizar la información, mejorar la ortografía, evitar repeticiones y expresar con mayor claridad algunas explicaciones técnicas.

En la documentación de las pruebas utilicé los resultados obtenidos durante la ejecución del sistema, incluyendo los códigos HTTP, los cambios de estado y los errores observados.

La asistencia también incluyó sugerencias de estructura y redacción para los documentos arquitectónicos, que debían corresponder con los mecanismos y servicios implementados.

## 5. Reflexión sobre las limitaciones de la IA

Durante la práctica pude comprobar que las sugerencias de inteligencia artificial no siempre se pueden aplicar directamente y que es necesario revisarlas.

Por ejemplo, inicialmente intenté probar WebSockets utilizando la consola de desarrolladores de Brave. Sin embargo, el navegador tenía una protección que dificultaba pegar el código. Para continuar, utilicé una página HTML desde la cual pude comprobar que las notificaciones llegaban correctamente.

Otro aspecto importante fue comprender que WebSockets no garantiza que un estudiante reciba un mensaje enviado mientras está desconectado. En la prueba correspondiente comprobé que el pedido continuaba procesándose y que el estado final podía recuperarse mediante REST.

Estas situaciones me ayudaron a comprender que una explicación o un ejemplo de código no reemplaza las pruebas realizadas en el sistema.

## 6. Reflexión final

Considero que utilizar inteligencia artificial como herramienta de apoyo me ayudó a comprender mejor algunos conceptos de Sistemas Distribuidos que al principio me resultaban difíciles, especialmente la diferencia entre REST, gRPC y WebSockets, y cómo estos mecanismos pueden trabajar dentro de un mismo sistema.

También me resultó útil para resolver dudas sobre errores, entender ciertas partes del código y mejorar la forma de explicar los resultados en la documentación.

Sin embargo, uno de los aprendizajes más importantes fue comprobar personalmente el funcionamiento de las soluciones. Al ejecutar los servicios, encontrar errores y realizar las pruebas, pude relacionar los conceptos teóricos con su aplicación práctica.

En conclusión, la IA fue un recurso de consulta y apoyo técnico durante el desarrollo, pero para comprender el funcionamiento del sistema fue necesario revisar el código, ejecutar los componentes e interpretar los resultados de las pruebas.