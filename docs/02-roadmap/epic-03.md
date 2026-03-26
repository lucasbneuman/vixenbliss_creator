# EPICA 3 - INTEGRACION, WORKERS, API, OBSERVABILIDAD Y OPERACION

## Objetivo de la epica

Construir la columna operativa del MVP reforzado: orquestacion, workers, contratos asincronos, API interna, dashboard, observabilidad, despliegue y preparacion para Sistema 5.

---

### TAREA 3.1 - Disenar el orquestador central del MVP reforzado

**Objetivo**  
Definir como se coordinan los flujos entre identidades, datasets, entrenamiento, generacion y catalogacion.

**Resultado esperado**  
Existe un flujo maestro del MVP con transiciones de estado, precondiciones, fallos bloqueantes y puntos de reintento.

**Implementacion paso a paso**  
1. Mapear el flujo end-to-end desde creacion de identidad hasta catalogacion de contenido.  
2. Declarar estado consumido y estado producido por cada tarea ejecutable.  
3. Definir puntos de corte entre procesos sincronicos y asincronos.  
4. Establecer reglas de reintento y bloqueo por faltante de dataset, LoRA, workflow o provider.  
5. Definir la relacion entre orquestador y jobs/workers.  
6. Documentar como evolucionar luego a `LangGraph` sin depender de el en el MVP.

**Decisiones tecnicas por defecto**  
- El MVP puede usar un job runner simple si cubre el flujo.  
- `LangGraph` queda como opcion de evolucion arquitectonica, no requisito inicial.  
- El orquestador no debe acoplarse a un proveedor concreto de GPU ni a un workflow fijo.

**Entradas**  
- estados de pipeline  
- contratos de jobs  
- dependencias entre tareas

**Salidas**  
- flujo maestro del MVP  
- politica de transiciones  
- mapa de reintentos y bloqueos

**Dependencias**  
Tareas 1.2 y 1.3.

**Herramientas y servicios a usar**  
Backend Python, documentacion tecnica.

**Credenciales o accesos requeridos**  
No requiere credenciales para diseno.

**Validaciones fail-fast**  
- Si una tarea no sabe que estado consume o produce, el flujo esta incompleto.  
- Si no esta definido cuando bloquear y cuando reintentar, la ejecucion no es operable.  
- Si el orquestador depende de un proveedor concreto, pierde reemplazabilidad.

**Artefactos tecnicos a producir**  
- especificacion del orquestador  
- matriz estado actual -> accion permitida

**Criterio de done**  
Cada paso del MVP puede ubicarse en un flujo unico con dependencias y bloqueos claros.

**Evidencia minima**  
Diagrama o tabla de transiciones del flujo principal.

**Siguiente tarea desbloqueada**  
Tareas 3.2, 3.3 y 3.4.

**Responsable sugerido**  
Codex.

---

### TAREA 3.2 - Definir la estructura de jobs, workers y ejecucion asincrona

**Objetivo**  
Traducir la necesidad de colas y procesamiento asincrono a una estructura operativa concreta.

**Resultado esperado**  
Existe un contrato minimo de worker y una estrategia de ejecucion asincrona para jobs pesados del MVP.

**Implementacion paso a paso**  
1. Definir tipos de worker: generacion base, dataset, entrenamiento LoRA, generacion batch, catalogacion y video preparado.  
2. Definir estados del job runner: pendiente, tomado, corriendo, reintentando, completado y fallido.  
3. Definir politica de timeout y retries por tipo de job.  
4. Definir ownership, polling o mecanismo de consumo.  
5. Establecer como el worker persiste progreso y errores.  
6. Alinear la estructura con el orquestador central.

**Decisiones tecnicas por defecto**  
- No es obligatorio introducir una cola compleja si un runner simple cubre el MVP.  
- Todo worker debe actualizar `Job` como fuente de verdad.  
- Cada job critico debe tener timeout por defecto y reintentos limitados.

**Entradas**  
- entidades `Job`  
- flujo del orquestador

**Salidas**  
- tipos de worker  
- politica de retries  
- politica de timeout  
- reglas de cambio de estado

**Dependencias**  
Tareas 1.2 y 3.1.

**Herramientas y servicios a usar**  
Backend Python, workers propios o scheduler simple.

**Credenciales o accesos requeridos**  
No requiere credenciales para diseno.

**Validaciones fail-fast**  
- Si un job pesado no tiene worker definido, la arquitectura esta incompleta.  
- Si no se puede distinguir job atascado de job en curso, falta politica operativa.  
- Si el error no se persiste en el `Job`, la ejecucion no es diagnosticable.

**Artefactos tecnicos a producir**  
- especificacion de job runner y workers  
- tabla `job_type -> timeout/retries/worker`

**Criterio de done**  
Todo job critico del MVP puede modelarse, ejecutarse y recuperarse bajo una politica clara.

**Evidencia minima**  
Tabla operativa de job types con estado, timeout y max retries.

**Siguiente tarea desbloqueada**  
Tareas 3.3, 3.4, 3.6 y 3.7.

**Responsable sugerido**  
Codex.

---

### TAREA 3.3 - Configurar integracion con proveedores GPU externos y politicas de recurso

**Objetivo**  
Habilitar el uso controlado de GPU para imagen, entrenamiento y preparacion de video.

**Resultado esperado**  
Existen adaptadores de proveedor GPU y reglas de mapeo job -> provider con timeouts, errores y parametros minimos por tipo de trabajo.

**Implementacion paso a paso**  
1. Elegir `Modal`, `Runpod` o combinacion por tipo de job.  
2. Definir adaptadores desacoplados del contrato superior.  
3. Mapear trabajos de imagen base, entrenamiento LoRA, generacion batch y video preparado.  
4. Persistir provider, endpoint y timeout usado por job.  
5. Definir errores tipicos y politica de fallback o fallo duro.  
6. Ejecutar una invocacion controlada por al menos un endpoint GPU.

**Decisiones tecnicas por defecto**  
- El contrato superior nunca depende del proveedor concreto.  
- `Modal` y `Runpod` son reemplazables mientras respeten payload y respuesta.  
- Si no hay fallback seguro, se falla explicita y rapidamente.

**Entradas**  
- decision de proveedor GPU  
- contratos de jobs  
- requerimientos por tipo de carga

**Salidas**  
- configuracion de proveedores  
- adaptadores  
- politica `job -> provider`

**Dependencias**  
Tareas 3.1 y 3.2.

**Herramientas y servicios a usar**  
`Modal` o `Runpod`, backend Python.

**Credenciales o accesos requeridos**  
Credenciales del proveedor GPU.

**Validaciones fail-fast**  
- Si falta credencial o endpoint para un provider activo, el job debe bloquearse antes de correr.  
- Si la respuesta del proveedor no puede mapearse al contrato interno, no se integra.  
- Si no se persiste provider y timeout usados, la trazabilidad operativa queda incompleta.

**Artefactos tecnicos a producir**  
- adaptadores y configuracion de proveedores  
- matriz `job_type -> provider`

**Criterio de done**  
Se puede invocar al menos un endpoint GPU con payload controlado y registrar la ejecucion de forma trazable.

**Evidencia minima**  
Un job que deja persistido provider, endpoint o alias, timeout y resultado.

**Siguiente tarea desbloqueada**  
Tareas 1.14, 2.5 y 2.10.

**Responsable sugerido**  
Codex o responsable infra/ML.

---

### TAREA 3.4 - Implementar la API interna del sistema con contratos presentes y futuros

**Objetivo**  
Exponer el MVP reforzado mediante una API interna coherente con la base tecnica y preparada para crecimiento.

**Resultado esperado**  
Existe una API interna funcional con endpoints para identidades, jobs, artefactos, generacion, contenidos, modelos y metricas.

**Implementacion paso a paso**  
1. Implementar contratos request/response para operaciones principales.  
2. Exponer al menos:
   - `POST /identities`
   - `GET /identities`
   - `GET /identities/{id}`
   - `POST /identities/{id}/generate-base-images`
   - `POST /identities/{id}/prepare-dataset`
   - `POST /identities/{id}/train-lora`
   - `POST /identities/{id}/generate-image`
   - `POST /identities/{id}/generate-video`
   - `GET /jobs/{id}`
   - `GET /artifacts/{id}`
   - `GET /contents`
   - `GET /models`
   - `GET /metrics`
3. Normalizar errores y codigos de estado.  
4. Asegurar que endpoints de ejecucion devuelven identificador de job o recurso consultable.  
5. Integrar validaciones previas y contratos de persistencia.  
6. Documentar payloads minimos y ejemplos.

**Decisiones tecnicas por defecto**  
- `FastAPI` o equivalente para API interna.  
- Endpoints que disparan trabajo pesado responden de forma asincrona con `job_id`.  
- `generate-video` puede quedar como contrato preparado aunque el proveedor real sea parcial.

**Entradas**  
- casos de uso  
- contratos de datos  
- estructura de jobs y workers

**Salidas**  
- API interna funcional  
- contratos request/response  
- errores estandarizados

**Dependencias**  
Tareas 1.4, 2.2, 2.5, 2.10 y 3.2.

**Herramientas y servicios a usar**  
`FastAPI` o equivalente, backend Python.

**Credenciales o accesos requeridos**  
DB, storage y proveedores segun endpoint.

**Validaciones fail-fast**  
- Si un endpoint no valida precondiciones criticas, no debe exponer ejecucion.  
- Si una operacion pesada no devuelve `job_id` o referencia persistible, la API queda incompleta.  
- Si los errores no diferencian validacion, configuracion y fallo del proveedor, no hay operacion segura.

**Artefactos tecnicos a producir**  
- API interna documentada  
- ejemplos request/response  
- catalogo de errores

**Criterio de done**  
Se pueden disparar y consultar las operaciones principales del MVP solo usando la API.

**Evidencia minima**  
Coleccion de ejemplos exitosos y fallidos por endpoint critico.

**Siguiente tarea desbloqueada**  
Tareas 3.5, 3.6, 3.8 y 3.9.

**Responsable sugerido**  
Codex.

---

### TAREA 3.5 - Desarrollar dashboard interno minimo para supervision operativa

**Objetivo**  
Proveer una vista de control interno para validar estados, jobs, artefactos y resultados.

**Resultado esperado**  
Existe un dashboard operativo minimo que permite recorrer una identidad de punta a punta y disparar flujos principales.

**Implementacion paso a paso**  
1. Definir vistas minimas de operacion: identidades, jobs, contenidos y detalle de identidad.  
2. Mostrar para cada identidad: estado, dataset, LoRA, modelo base, jobs recientes, contenidos recientes y QA.  
3. Exponer links o acciones para disparar operaciones principales.  
4. Mostrar fallos y jobs pendientes o fallidos.  
5. Permitir inspeccionar outputs, artefactos y metadata clave.  
6. Validar el flujo de punta a punta desde el panel.

**Decisiones tecnicas por defecto**  
- Panel interno simple, no una UI comercial.  
- La fuente de verdad es la API interna.  
- El dashboard debe priorizar trazabilidad y operacion sobre estetica.

**Entradas**  
- API interna  
- datos persistidos

**Salidas**  
- dashboard funcional  
- vista operativa del pipeline

**Dependencias**  
Tareas 2.9 y 3.4.

**Herramientas y servicios a usar**  
Frontend simple o panel interno.

**Credenciales o accesos requeridos**  
Acceso a API interna.

**Validaciones fail-fast**  
- Si el panel no refleja estados reales del pipeline, no sirve como herramienta operativa.  
- Si no puede verse un job fallido con contexto suficiente, la supervision es incompleta.  
- Si no puede revisarse una identidad de punta a punta, la tarea no cierra.

**Artefactos tecnicos a producir**  
- panel interno de operaciones  
- vistas minimas de detalle y listados

**Criterio de done**  
Un operador puede seguir una identidad completa y detectar donde se encuentra bloqueada o avanzada.

**Evidencia minima**  
Recorrido de una identidad desde dashboard con acceso a jobs, modelo, dataset y contenidos.

**Siguiente tarea desbloqueada**  
Tareas 3.6 y 3.9.

**Responsable sugerido**  
Codex.

---

### TAREA 3.6 - Implementar observabilidad con OpenTelemetry y readiness para Langfuse

**Objetivo**  
Elevar logging y monitoreo a un nivel compatible con los principios data-driven y fail-fast.

**Resultado esperado**  
Existe una capa minima de trazas, logs estructurados y metricas operativas para API y jobs criticos, con posibilidad de exportacion a `Langfuse`.

**Implementacion paso a paso**  
1. Instrumentar endpoints criticos de API.  
2. Instrumentar workers y jobs de generacion, dataset y entrenamiento.  
3. Registrar duracion, provider, retries, errores y estado final.  
4. Propagar correlacion entre request, job, artefacto y contenido cuando aplique.  
5. Configurar exportacion OTLP.  
6. Dejar flags y configuracion lista para integrar `Langfuse`.

**Decisiones tecnicas por defecto**  
- `OpenTelemetry` es obligatorio para baseline de observabilidad.  
- `Langfuse` queda como integracion preparada, no obligatoria para cerrar MVP si no hay credenciales.  
- Toda falla relevante debe quedar en logs estructurados y trazas correlacionables.

**Entradas**  
- API interna  
- workers  
- jobs principales

**Salidas**  
- trazas basicas del sistema  
- logs estructurados  
- metricas de jobs y generacion  
- readiness para `Langfuse`

**Dependencias**  
Tareas 3.2, 3.4 y 3.5.

**Herramientas y servicios a usar**  
`OpenTelemetry`, backend Python, `Langfuse` opcional.

**Credenciales o accesos requeridos**  
Endpoint OTEL y claves `Langfuse` si se conecta.

**Validaciones fail-fast**  
- Si un job falla y no deja traza o log correlacionable, la tarea esta incompleta.  
- Si la instrumentacion rompe el flujo principal, debe corregirse antes de cerrar.  
- Si no existe correlacion minima entre endpoint y job, la observabilidad no cumple objetivo operativo.

**Artefactos tecnicos a producir**  
- instrumentacion baseline  
- convencion de atributos de traza y log

**Criterio de done**  
Se puede seguir una ejecucion principal del sistema mediante trazas y logs correlacionados.

**Evidencia minima**  
Una ejecucion principal rastreable end-to-end por observabilidad.

**Siguiente tarea desbloqueada**  
Tareas 3.7 y 3.9.

**Responsable sugerido**  
Codex o responsable platform.

---

### TAREA 3.7 - Preparar despliegue minimo en Docker y Coolify

**Objetivo**  
Dejar el sistema listo para desplegarse de forma consistente y repetible.

**Resultado esperado**  
Existen artefactos de contenerizacion, configuracion de entorno y checklist de arranque compatibles con `Coolify`.

**Implementacion paso a paso**  
1. Crear `Dockerfile` y configuracion necesaria para backend y componentes minimos.  
2. Declarar variables de entorno requeridas.  
3. Documentar conectividad con DB, storage, `ComfyUI`, proveedor GPU y OTEL.  
4. Definir servicios necesarios para despliegue del MVP.  
5. Preparar configuracion basica para `Coolify`.  
6. Validar que el servicio arranca y expone API.

**Decisiones tecnicas por defecto**  
- `Docker` es el formato de despliegue canonico.  
- `Coolify` es el destino operativo previsto, pero el contenedor debe poder arrancar fuera de el.  
- El despliegue no debe ocultar variables criticas ni defaults inseguros.

**Entradas**  
- backend funcional  
- variables de entorno consolidadas  
- dependencias externas definidas

**Salidas**  
- imagen o definicion de contenedor  
- configuracion de despliegue  
- checklist de arranque

**Dependencias**  
Tareas 3.2, 3.4 y 3.6.

**Herramientas y servicios a usar**  
`Docker`, `Coolify`.

**Credenciales o accesos requeridos**  
Acceso a `Coolify` y servicios externos.

**Validaciones fail-fast**  
- Si el contenedor arranca sin validar variables criticas, el despliegue no es seguro.  
- Si la API no queda accesible luego del arranque, la tarea falla.  
- Si el contenedor depende de rutas o estados locales no declarados, debe corregirse.

**Artefactos tecnicos a producir**  
- `Dockerfile` o equivalente  
- configuracion de despliegue versionada  
- checklist de bootstrap

**Criterio de done**  
La aplicacion puede arrancar en entorno controlado y exponer su API con configuracion declarada.

**Evidencia minima**  
Arranque exitoso de la aplicacion en entorno de despliegue.

**Siguiente tarea desbloqueada**  
Tarea 3.9.

**Responsable sugerido**  
Codex o responsable infra.

---

### TAREA 3.8 - Preparar la arquitectura de entrada para Sistema 5 sin implementarlo

**Objetivo**  
Dejar lista la base tecnica para una futura capa conversacional sin expandir el alcance del MVP actual.

**Resultado esperado**  
Existen slots consumibles por LLM, endpoints internos invocables y restricciones documentadas para futura integracion conversacional.

**Implementacion paso a paso**  
1. Identificar los slots de identidad reutilizables por LLM.  
2. Declarar que operaciones de API puede invocar una futura capa conversacional.  
3. Definir restricciones futuras de memoria, consentimiento y politicas.  
4. Establecer contrato interno de uso de `generate_image` y `generate_video`.  
5. Preparar el lenguaje de herramientas sin construir aun el chatbot.  
6. Documentar como evolucionar a una orquestacion estilo `LangGraph`.

**Decisiones tecnicas por defecto**  
- Sistema 5 no se implementa en este MVP.  
- Se preparan contratos y slots, no UX conversacional ni WebSocket.  
- `LangGraph` se documenta como via probable de evolucion, no como dependencia actual.

**Entradas**  
- ficha tecnica de identidad  
- contratos de API  
- definicion de contenido

**Salidas**  
- lista de slots consumibles por LLM  
- contrato interno de invocacion  
- reglas futuras de memoria y restricciones

**Dependencias**  
Tareas 1.1, 2.10 y 3.4.

**Herramientas y servicios a usar**  
Backend Python, documentacion tecnica.

**Credenciales o accesos requeridos**  
No requiere credenciales obligatorias.

**Validaciones fail-fast**  
- Si un implementador futuro no puede identificar que datos y endpoints necesita, la preparacion es insuficiente.  
- Si se introduce funcionalidad conversacional productiva, se estaria expandiendo alcance.  
- Si los slots no son estructurados, no sirven para uso por LLM.

**Artefactos tecnicos a producir**  
- contrato de readiness para Sistema 5  
- lista de herramientas y slots futuros

**Criterio de done**  
Un implementador futuro puede integrar capa conversacional sin rediseñar identidades ni API internas.

**Evidencia minima**  
Documento de slots, endpoints y restricciones futuras.

**Siguiente tarea desbloqueada**  
Ninguna dentro del MVP actual.

**Responsable sugerido**  
Codex.

---

### TAREA 3.9 - Ejecutar pruebas end-to-end del MVP reforzado

**Objetivo**  
Validar que el roadmap ampliado sigue siendo ejecutable como MVP y que todos los contratos nuevos son coherentes.

**Resultado esperado**  
Existe un plan de prueba operativo con evidencia del flujo principal, fallas detectadas y brechas pendientes previas al cierre del MVP.

**Implementacion paso a paso**  
1. Ejecutar creacion de identidad y persistencia de ficha tecnica.  
2. Ejecutar generacion y registro de imagenes base.  
3. Ejecutar armado y validacion de dataset.  
4. Ejecutar lanzamiento de entrenamiento LoRA y registro del modelo.  
5. Ejecutar validacion manual del LoRA.  
6. Ejecutar generacion batch de imagenes, catalogacion, QA, consulta por API, revision por dashboard y trazas.  
7. Confirmar readiness de video y de Sistema 5 como contratos preparados.

**Decisiones tecnicas por defecto**  
- La prueba debe cubrir el flujo principal completo, no solo componentes aislados.  
- Los fallos encontrados deben dejarse en reporte accionable.  
- Video y Sistema 5 se validan como readiness contractual, no como funcionalidad productiva.

**Entradas**  
- sistema desplegado o entorno funcional de prueba  
- credenciales del entorno  
- datos de prueba

**Salidas**  
- evidencia de flujo completo  
- lista de fallas encontradas  
- ajustes pendientes antes de cierre del MVP

**Dependencias**  
Tareas 1.16, 2.11, 3.4, 3.5, 3.6 y 3.7.

**Herramientas y servicios a usar**  
API interna, dashboard, DB, storage, `OpenTelemetry`.

**Credenciales o accesos requeridos**  
Todas las del entorno de prueba.

**Validaciones fail-fast**  
- Si el flujo principal no puede completarse de punta a punta, el MVP no se considera listo.  
- Si una falla no puede diagnosticarse por job, log o traza, la observabilidad es insuficiente.  
- Si video o Sistema 5 requieren rediseño contractual, la preparacion no esta terminada.

**Artefactos tecnicos a producir**  
- checklist o reporte end-to-end  
- inventario de fallas y bloqueos

**Criterio de done**  
El flujo principal se completa con trazabilidad y con lista clara de brechas remanentes, si las hay.

**Evidencia minima**  
Reporte de prueba con resultados por paso, fallos y capturas o referencias de evidencia.

**Siguiente tarea desbloqueada**  
Cierre del MVP reforzado.

**Responsable sugerido**  
Codex con validacion humana.
