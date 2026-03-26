# EPICA 2 - SISTEMA 2: PRODUCCION AUTOMATIZADA DE CONTENIDO

## Objetivo de la epica

Construir el sistema de produccion de contenido sobre motores visuales modulares, priorizando imagen para el MVP pero dejando preparada la interfaz tecnica para video. Debe asegurar generacion consistente por identidad, variacion controlada, metadata completa, QA tecnico y soporte para crecimiento posterior.

---

### TAREA 2.1 - Definir el modelo de datos maestro de Contenido y metadata extensible a video

**Objetivo**  
Definir el contrato canonico de `Content` y su metadata extensible a imagen y video.

**Resultado esperado**  
Existe un modelo `Content` persistible que representa outputs de imagen y deja el contrato listo para video sin rediseño posterior.

**Implementacion paso a paso**  
1. Definir campos obligatorios para imagen.  
2. Agregar campos opcionales para video: duracion, frames y frame rate.  
3. Alinear `Content` con `Job`, `Artifact` y `ModelRegistry`.  
4. Definir `generation_status` y `qa_status`.  
5. Documentar como se persisten `prompt`, `negative_prompt`, `seed`, `workflow_id`, `provider` y `model_version_used`.  
6. Verificar que el contrato cubre outputs de Tareas 2.5 a 2.10.

**Decisiones tecnicas por defecto**  
- `Content` representa el output catalogado; `Artifact` representa el archivo y sus metadatos tecnicos.  
- Imagen es obligatoria para MVP; video queda contractualmente preparado.  
- `qa_status` debe existir a nivel de contenido final.

**Entradas**  
- base tecnica  
- contratos existentes de jobs, artefactos y modelos

**Salidas**  
- schema `Content`  
- reglas de persistencia  
- metadata extensible a video

**Dependencias**  
Tareas 1.2 y 1.9.

**Herramientas y servicios a usar**  
Python, `Supabase/Postgres`.

**Credenciales o accesos requeridos**  
No requiere credenciales para diseno.

**Validaciones fail-fast**  
- Si `Content` no puede representar una imagen generada con trazabilidad completa, el modelo esta incompleto.  
- Si el contrato obliga a rediseñar para soportar video, debe corregirse antes de persistir.  
- Si `job_id` o `model_version_used` quedan ambiguos, el modelo no se aprueba.

**Artefactos tecnicos a producir**  
- schema `Content`  
- documento de correspondencia `Content <-> Artifact`

**Criterio de done**  
El sistema puede catalogar una imagen generada y dejar preparado el mismo contrato para un video futuro.

**Evidencia minima**  
Ejemplo valido de `Content` para imagen y ejemplo preparado para video.

**Siguiente tarea desbloqueada**  
Tarea 2.2.

**Responsable sugerido**  
Codex.

---

### TAREA 2.2 - Crear la persistencia de contenidos y relacionarla con jobs y artefactos

**Objetivo**  
Materializar el modelo `Content` y conectarlo con la trazabilidad del sistema.

**Resultado esperado**  
Existe tabla `contents` con relaciones operativas hacia identidad, job, artefactos y version de modelo.

**Implementacion paso a paso**  
1. Crear tabla `contents` con claves y columnas definidas.  
2. Relacionarla con `identities`, `jobs` y metadata de modelo.  
3. Agregar indices por `identity_id`, `media_modality`, `generation_status`, `qa_status`, `created_at`.  
4. Versionar migracion o SQL.  
5. Probar insercion y consulta.  
6. Validar que un output de imagen puede vincularse a sus registros previos.

**Decisiones tecnicas por defecto**  
- `Content` debe ser consultable de forma operativa por dashboard y API.  
- La relacion a `Artifact` puede ser directa o via metadata, pero debe quedar trazable.  
- Los indices deben favorecer listados recientes y filtros por identidad.

**Entradas**  
- schema `Content`  
- esquema relacional existente

**Salidas**  
- tabla `contents`  
- migracion o SQL  
- relaciones e indices

**Dependencias**  
Tareas 1.3 y 2.1.

**Herramientas y servicios a usar**  
`Supabase/Postgres`, SQLAlchemy o SQL directo.

**Credenciales o accesos requeridos**  
DB.

**Validaciones fail-fast**  
- Si `Content` no puede ligarse a identidad y job, la persistencia no esta lista.  
- Si no hay forma de filtrar por `qa_status`, el dashboard quedara incompleto.  
- Si una insercion de prueba falla por diseño del modelo, la tarea no cierra.

**Artefactos tecnicos a producir**  
- migracion de `contents`  
- consulta de verificacion

**Criterio de done**  
La persistencia de contenidos soporta catalogacion, consulta por identidad y trazabilidad al job origen.

**Evidencia minima**  
Insercion y consulta exitosa de un `Content` de prueba.

**Siguiente tarea desbloqueada**  
Tareas 2.5 y 2.9.

**Responsable sugerido**  
Codex.

---

### TAREA 2.3 - Definir el contrato del motor visual basado en ComfyUI y workflows reutilizables

**Objetivo**  
Definir la interfaz estable del motor visual para que la generacion de imagen y la preparacion de video consuman el mismo lenguaje operativo.

**Resultado esperado**  
Existe un contrato de motor visual con inputs, outputs, politicas de workflow versionado y ramas opcionales para `IP-Adapter` y `ControlNet`.

**Implementacion paso a paso**  
1. Definir inputs minimos del motor: identidad, prompt, negative prompt, seed, workflow, modelo base, LoRA, dimensiones, cantidad.  
2. Definir outputs minimos: archivos generados, metadata, provider, tiempos y errores.  
3. Declarar `workflow_id` y version operativa como identificadores canonicos.  
4. Definir flags o bloques opcionales para `IP-Adapter` y `ControlNet`.  
5. Declarar como el motor llamara a `ComfyUI` sin exponer detalles internos al resto del sistema.  
6. Dejar extension preparada para `prepare_video_generation`.

**Decisiones tecnicas por defecto**  
- `ComfyUI` es el motor visual canonico del MVP.  
- `IP-Adapter` y `ControlNet` son ramas opcionales del workflow, no acoplamientos duros.  
- El contrato superior no cambia si la ejecucion real ocurre en `Modal` o `Runpod`.

**Entradas**  
- necesidades de generacion del MVP  
- compatibilidades declaradas en `model_registry`

**Salidas**  
- contrato del motor visual  
- politica de workflow versionado  
- esquema de payloads de ejecucion

**Dependencias**  
Tareas 1.9 y 2.1.

**Herramientas y servicios a usar**  
`ComfyUI`, backend Python.

**Credenciales o accesos requeridos**  
Endpoint `ComfyUI` si se prueba integracion.

**Validaciones fail-fast**  
- Si un workflow no puede identificarse por `workflow_id`, no entra al contrato canonico.  
- Si el contrato no soporta ramas opcionales, se rompe la reemplazabilidad.  
- Si el motor no devuelve metadata suficiente para catalogacion, la tarea esta incompleta.

**Artefactos tecnicos a producir**  
- contrato del motor visual  
- ejemplo de payload de imagen  
- ejemplo de payload preparado para video

**Criterio de done**  
Los equipos pueden integrar generacion de imagen sobre `ComfyUI` sin redefinir inputs y outputs por cada caso.

**Evidencia minima**  
Especificacion de request/response del motor visual con ejemplo.

**Siguiente tarea desbloqueada**  
Tareas 2.5, 2.6, 2.7 y 2.10.

**Responsable sugerido**  
Codex.

---

### TAREA 2.4 - Definir estrategia de prompts, hooks y plantillas por vertical

**Objetivo**  
Traducir la taxonomia de identidad a una capa de prompts reutilizable y controlable.

**Resultado esperado**  
Existen plantillas de prompt por vertical, hooks y variables dinamicas compatibles con el motor visual.

**Implementacion paso a paso**  
1. Mapear verticales y rasgos de identidad a estructuras de prompt.  
2. Definir prompt base, negative prompt base y variables dinamicas.  
3. Crear hooks o variantes de entrada por tipo de contenido.  
4. Definir limites de contenido por vertical y por identidad.  
5. Preparar plantillas compatibles con batch y con futuro video.  
6. Validar que pueden renderizarse sin intervencion manual.

**Decisiones tecnicas por defecto**  
- Los prompts se almacenan como plantillas versionadas, no como textos improvisados por corrida.  
- Todo prompt final debe poder reconstruirse desde plantilla + variables.  
- Los limites operativos de identidad deben reflejarse en la plantilla o en validaciones previas.

**Entradas**  
- taxonomias de identidad  
- contrato del motor visual

**Salidas**  
- plantillas de prompt por vertical  
- negative prompts base  
- estructura de hooks y variables

**Dependencias**  
Tareas 1.6 y 2.3.

**Herramientas y servicios a usar**  
Backend Python, configuracion versionada.

**Credenciales o accesos requeridos**  
No requiere credenciales.

**Validaciones fail-fast**  
- Si una plantilla no puede renderizarse a prompt final, no se aprueba.  
- Si no puede auditarse el prompt final desde sus componentes, la trazabilidad es insuficiente.  
- Si una plantilla contradice limites operativos de identidad, debe corregirse.

**Artefactos tecnicos a producir**  
- catalogo de plantillas  
- renderizador de prompts

**Criterio de done**  
El sistema puede generar prompts finales reproducibles y auditables por vertical e identidad.

**Evidencia minima**  
Prompts renderizados de ejemplo para al menos dos verticales.

**Siguiente tarea desbloqueada**  
Tareas 2.5 y 2.8.

**Responsable sugerido**  
Codex con revision humana.

---

### TAREA 2.5 - Implementar el generador de imagenes por identidad usando modelo base + LoRA

**Objetivo**  
Habilitar la generacion de imagen final del MVP usando identidad persistida, modelo base, LoRA validado y workflow versionado.

**Resultado esperado**  
Existe un caso de uso `generate_image` que resuelve inputs, valida precondiciones, dispara el motor visual y deja job y metadata completos.

**Implementacion paso a paso**  
1. Recibir `identity_id`, payload de prompt y opciones de generacion.  
2. Resolver identidad, `base_model_id`, LoRA validado y `workflow_id` activo.  
3. Crear `Job` de tipo `generate_image` con timeout y retries.  
4. Renderizar prompt final y negative prompt final.  
5. Invocar el motor visual sobre `ComfyUI` o proveedor GPU.  
6. Capturar outputs y actualizar estado del job.

**Decisiones tecnicas por defecto**  
- El flujo de imagen final exige LoRA validado para el caso principal del MVP.  
- Si `IP-Adapter` o `ControlNet` no estan activos, el contrato superior sigue siendo el mismo.  
- Los errores del proveedor se normalizan en `error_code` y `error_message`.

**Entradas**  
- identidad validada  
- LoRA versionado y validado  
- prompt  
- workflow  
- configuracion de proveedor

**Salidas**  
- job de generacion  
- outputs temporales o definitivos  
- metadata de ejecucion

**Dependencias**  
Tareas 1.16, 2.3 y 2.4.

**Herramientas y servicios a usar**  
`ComfyUI`, `Modal` o `Runpod`, backend Python.

**Credenciales o accesos requeridos**  
GPU externa y/o `ComfyUI`.

**Validaciones fail-fast**  
- Si falta LoRA validado o workflow activo, abortar con error claro.  
- Si el prompt final no puede renderizarse, no se lanza generacion.  
- Si no se persisten `seed`, `workflow_id` y `model_version_used`, el resultado no se considera catalogable.

**Artefactos tecnicos a producir**  
- caso de uso `generate_image`  
- adaptador job -> motor visual

**Criterio de done**  
El sistema puede lanzar una generacion de imagen final por identidad con trazabilidad completa y sin pasos manuales ocultos.

**Evidencia minima**  
Un job exitoso con prompt final, seed, workflow, modelo y archivo resultante.

**Siguiente tarea desbloqueada**  
Tareas 2.6, 2.7, 2.8 y 2.9.

**Responsable sugerido**  
Codex.

---

### TAREA 2.6 - Integrar IP-Adapter para refuerzo de consistencia de identidad

**Objetivo**  
Incorporar una via opcional de consistencia visual basada en imagen de referencia.

**Resultado esperado**  
El workflow puede aceptar `reference_face_image_url` como condicion opcional y registrar cuando `IP-Adapter` fue utilizado.

**Implementacion paso a paso**  
1. Definir parametro opcional de referencia visual en el contrato del motor.  
2. Enlazar `reference_face_image_url` de identidad con la rama `IP-Adapter`.  
3. Registrar intensidad, modelo de adapter y referencia usada en metadata.  
4. Permitir activar o desactivar la rama sin cambiar la API superior.  
5. Probar una generacion con y sin `IP-Adapter`.  
6. Comparar consistencia y dejar trazabilidad del uso.

**Decisiones tecnicas por defecto**  
- `IP-Adapter` es opcional y complementa al LoRA, no lo reemplaza como contrato central.  
- La referencia visual debe ser un artefacto recuperable, no un path informal.  
- El uso de `IP-Adapter` debe quedar explicitamente registrado.

**Entradas**  
- identidad con referencia facial  
- workflow compatible  
- configuracion `IP-Adapter`

**Salidas**  
- integracion opcional de `IP-Adapter`  
- metadata de uso de referencia  
- comparacion de salida con y sin adapter

**Dependencias**  
Tareas 1.11, 2.3 y 2.5.

**Herramientas y servicios a usar**  
`ComfyUI`, `IP-Adapter`.

**Credenciales o accesos requeridos**  
Acceso a `ComfyUI` o pipeline visual.

**Validaciones fail-fast**  
- Si la referencia facial no existe o no puede abrirse, no se activa `IP-Adapter`.  
- Si el workflow declara `IP-Adapter` pero no registra su uso, la trazabilidad esta rota.  
- Si la rama `IP-Adapter` rompe la interfaz superior, debe rediseñarse.

**Artefactos tecnicos a producir**  
- workflow actualizado con rama opcional de `IP-Adapter`  
- metadata de condicionamiento visual

**Criterio de done**  
El sistema puede generar una imagen con o sin `IP-Adapter` sin cambiar el contrato superior y dejando rastro del modo usado.

**Evidencia minima**  
Dos ejecuciones comparables, una con `IP-Adapter` y otra sin el.

**Siguiente tarea desbloqueada**  
Tareas 2.8 y 2.9.

**Responsable sugerido**  
Codex o responsable de pipeline visual.

---

### TAREA 2.8 - Implementar motor de variacion controlada y generacion batch

**Objetivo**  
Generar lotes de contenido variados sin perder consistencia ni trazabilidad.

**Resultado esperado**  
Existe un orquestador de batch que expande plantillas, seeds, hooks y condicionamientos en una matriz controlada por identidad.

**Implementacion paso a paso**  
1. Definir matriz de variacion por vertical e identidad.  
2. Generar combinaciones validas de prompts, seeds, poses, fondos y opciones.  
3. Filtrar combinaciones prohibidas por limites operativos.  
4. Crear job padre o grupo de jobs para batch.  
5. Ejecutar cada item preservando prompt final, seed y workflow exactos.  
6. Dejar metadata completa por item y por lote.

**Decisiones tecnicas por defecto**  
- La variacion debe ser parametrica y auditable, no aleatoria opaca.  
- Cada item del batch se persiste como ejecucion individual o item identificable.  
- La consistencia del personaje sigue dependiendo de LoRA validado y condicionamiento opcional.

**Entradas**  
- plantillas de prompt  
- workflow  
- configuraciones opcionales de `IP-Adapter` y `ControlNet`

**Salidas**  
- batch de prompts y ejecuciones  
- contenido variado por identidad  
- metadata completa por item

**Dependencias**  
Tareas 2.4, 2.5, 2.6 y 2.7.

**Herramientas y servicios a usar**  
Backend Python, `ComfyUI`, GPU externa si aplica.

**Credenciales o accesos requeridos**  
GPU y DB.

**Validaciones fail-fast**  
- Si una combinacion viola limites operativos, no debe entrar al batch.  
- Si un item del batch no conserva su `seed` o prompt final, se pierde trazabilidad.  
- Si el sistema no puede distinguir un fallo por item del lote, el diseño debe corregirse.

**Artefactos tecnicos a producir**  
- orquestador de batch por identidad  
- matriz de variacion versionada

**Criterio de done**  
El sistema puede generar un lote de imagenes variadas con trazabilidad por item y por lote.

**Evidencia minima**  
Un batch con variaciones visibles y metadata completa por item.

**Siguiente tarea desbloqueada**  
Tareas 2.9 y 2.11.

**Responsable sugerido**  
Codex.

---

### TAREA 2.9 - Almacenar y catalogar outputs de imagen con metadata completa

**Objetivo**  
Registrar formalmente cada output generado y hacerlo accesible por API y dashboard.

**Resultado esperado**  
Cada imagen generada queda subida a storage, registrada como `Artifact` y catalogada como `Content`.

**Implementacion paso a paso**  
1. Subir archivo generado al storage de contenidos.  
2. Generar thumbnail si aplica.  
3. Crear `Artifact` del archivo principal y del thumbnail si corresponde.  
4. Crear registro `Content` con metadata completa de generacion.  
5. Asociar `Content` con identidad, job, modelo y workflow.  
6. Actualizar `pipeline_state` de identidad a `content_generated` cuando corresponda.

**Decisiones tecnicas por defecto**  
- `Artifact` y `Content` se crean juntos como parte del catalogado.  
- `Content` es la vista operativa para API y dashboard.  
- La metadata persistida debe permitir reconstruir el contexto exacto de generacion.

**Entradas**  
- outputs del motor de generacion  
- job de origen  
- storage y DB disponibles

**Salidas**  
- archivos en storage  
- registros `contents`  
- registros `artifacts`

**Dependencias**  
Tareas 2.2, 2.5 y 2.8.

**Herramientas y servicios a usar**  
Storage, DB, backend Python.

**Credenciales o accesos requeridos**  
Storage y DB.

**Validaciones fail-fast**  
- Si un archivo no puede subirse, no se cataloga como final.  
- Si `Content` no incluye `prompt_used`, `seed`, `workflow_id` y `model_version_used`, queda incompleto.  
- Si no puede consultarse luego por API, la tarea no esta terminada.

**Artefactos tecnicos a producir**  
- catalogador de contenido generado  
- convencion de metadata de contenido

**Criterio de done**  
Cada output final de imagen puede consultarse con metadata completa y ruta recuperable.

**Evidencia minima**  
Consulta de un `Content` con su `Artifact`, job y modelo asociados.

**Siguiente tarea desbloqueada**  
Tareas 2.11, 3.4 y 3.5.

**Responsable sugerido**  
Codex.

---

### TAREA 2.10 - Preparar interfaz tecnica para video corto sin hacerlo condicion de cierre del MVP

**Objetivo**  
Traducir la base tecnica de video a contratos reales sin convertirla aun en requisito de produccion completa.

**Resultado esperado**  
Existe una interfaz `prepare_video_generation` o `generate_video` con proveedor abstracto, metadata definida y politica de compatibilidad documentada.

**Implementacion paso a paso**  
1. Definir contrato de entrada para video: identidad, prompt, modalidad `text-to-video` o `image-to-video`, workflow, modelo base de video y opciones.  
2. Declarar salidas esperadas y metadata minima: duracion, frames, frame rate, provider, modelo, seed si aplica.  
3. Definir proveedor abstracto con implementaciones posibles `Wan2.2`, `AnimateDiff` o `SVD`.  
4. Describir compatibilidad con `ComfyUI` y con imagen base inicial si aplica.  
5. Permitir persistir una solicitud de video como job y como contenido preparado.  
6. Marcar readiness de pipeline en `video_ready_for_future_integration` cuando corresponda.

**Decisiones tecnicas por defecto**  
- El MVP no exige generar video productivo, pero si exige contrato estable y persistible.  
- `Wan2.2`, `AnimateDiff` y `SVD` se modelan como proveedores intercambiables.  
- El contrato debe permitir tanto `text-to-video` como `image-to-video`.

**Entradas**  
- contratos de contenido  
- workflows  
- catalogo de modelos  
- compatibilidades de proveedores

**Salidas**  
- contrato interno para video  
- metadata de video definida  
- placeholder operativo o adaptador base

**Dependencias**  
Tareas 1.9, 2.1 y 2.3.

**Herramientas y servicios a usar**  
Backend Python, `ComfyUI`, `Wan2.2` o equivalente.

**Credenciales o accesos requeridos**  
Solo si se prueba integracion real.

**Validaciones fail-fast**  
- Si el contrato obliga a rediseño cuando se implemente el primer proveedor real, esta incompleto.  
- Si la solicitud de video no puede persistirse como job, no hay readiness real.  
- Si la metadata no contempla modalidad y proveedor, la interfaz queda ambigua.

**Artefactos tecnicos a producir**  
- especificacion de interfaz de video desacoplada  
- ejemplo de payload `text-to-video`  
- ejemplo de payload `image-to-video`

**Criterio de done**  
El sistema puede describir, persistir y enrutar una solicitud de video sin rediseño posterior del contrato.

**Evidencia minima**  
Un ejemplo de solicitud de video persistible y consultable.

**Siguiente tarea desbloqueada**  
Tareas 3.4 y 3.8.

**Responsable sugerido**  
Codex o responsable ML.

---

### TAREA 2.11 - Implementar control tecnico de calidad y revision humana de muestras

**Objetivo**  
Introducir una capa minima de QA antes de considerar util un lote de outputs.

**Resultado esperado**  
Existe un flujo de QA tecnico y humano que marca contenidos o lotes como aprobados, rechazados o sujetos a reintento.

**Implementacion paso a paso**  
1. Definir reglas tecnicas de QA minima: integridad de metadata, accesibilidad del archivo, consistencia basica y ausencia de fallos tecnicos evidentes.  
2. Ejecutar chequeos automaticos sobre cada output o muestra representativa.  
3. Registrar `qa_status` y observaciones.  
4. Permitir revision humana de una muestra del lote.  
5. Señalar reintento, descarte o aprobacion.  
6. Exponer el estado al dashboard y a la API.

**Decisiones tecnicas por defecto**  
- El MVP exige QA minima; no exige automatizacion avanzada de vision por computadora.  
- `qa_status` debe existir a nivel de contenido final.  
- La revision humana es complementaria y se aplica al menos sobre muestras.

**Entradas**  
- lotes de contenido almacenados  
- metadata completa por contenido

**Salidas**  
- `qa_status` por contenido o lote  
- observaciones  
- señales para reintento o descarte

**Dependencias**  
Tarea 2.9.

**Herramientas y servicios a usar**  
Dashboard, DB, storage.

**Credenciales o accesos requeridos**  
Acceso al dashboard o storage.

**Validaciones fail-fast**  
- Si el contenido no tiene metadata completa, no entra a QA.  
- Si no queda registro del resultado de QA, el contenido no se considera aprobado.  
- Si un lote falla QA, no debe marcarse como listo para consumo operativo.

**Artefactos tecnicos a producir**  
- registro QA con estatus por output  
- vista de QA para dashboard

**Criterio de done**  
Una muestra o contenido individual puede aprobarse o rechazarse con motivo persistido.

**Evidencia minima**  
Un contenido marcado como aprobado y otro como rechazado con observaciones.

**Siguiente tarea desbloqueada**  
Tarea 3.9.

**Responsable sugerido**  
Humano con soporte del sistema.

---

### TAREA 2.7 - Integrar ControlNet para pose, encuadre y variacion estructural

**Objetivo**  
Agregar condicionamiento estructural al workflow sin romper la modularidad del motor visual.

**Resultado esperado**  
El sistema soporta uno o mas modos de `ControlNet` con activacion opcional y metadata persistible.

**Implementacion paso a paso**  
1. Definir inputs estructurales opcionales: pose, depth, canny u otros permitidos.  
2. Incorporar nodos o configuracion `ControlNet` al workflow.  
3. Registrar tipo de condicion, fuente y parametros usados.  
4. Mantener el mismo contrato superior del motor.  
5. Probar una generacion condicionada y una no condicionada.  
6. Verificar que la metadata distingue ambos casos.

**Decisiones tecnicas por defecto**  
- `ControlNet` es opcional y no debe ser requerido por todos los prompts.  
- La interfaz superior no cambia aunque cambie el tipo de `ControlNet` activo.  
- La condicion estructural debe quedar trazable en metadata.

**Entradas**  
- workflow compatible  
- configuracion base de `ControlNet`

**Salidas**  
- integracion de pose o control estructural  
- metadata de condicion aplicada

**Dependencias**  
Tareas 2.3 y 2.5.

**Herramientas y servicios a usar**  
`ComfyUI`, `ControlNet`.

**Credenciales o accesos requeridos**  
Acceso al motor visual configurado.

**Validaciones fail-fast**  
- Si falta recurso estructural requerido para un modo condicionado, la generacion debe fallar de forma explicita.  
- Si `ControlNet` altera la interfaz superior, la integracion no se aprueba.  
- Si la metadata no indica el modo de control usado, el resultado no es auditable.

**Artefactos tecnicos a producir**  
- workflow con nodos activables de `ControlNet`  
- metadata de condicionamiento estructural

**Criterio de done**  
Se puede producir una imagen condicionada por estructura sin romper la API superior ni perder trazabilidad.

**Evidencia minima**  
Una imagen condicionada correctamente registrada.

**Siguiente tarea desbloqueada**  
Tareas 2.8 y 2.9.

**Responsable sugerido**  
Codex o responsable de pipeline visual.
