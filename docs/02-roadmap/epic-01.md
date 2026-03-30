# EPICA 1 - SISTEMA 1: IDENTIDADES, DATASETS Y MODELOS

## Objetivo de la epica

Construir el pipeline que crea identidades digitales persistentes, tecnicamente trazables y compatibles con entrenamiento. La salida debe ser una identidad completa en base de datos con ficha tecnica estructurada, artefactos base, dataset balanceado, referencia a modelo base, referencia a LoRA y estado de pipeline consumible por el Sistema 2.

---

### TAREA 1.1 - Definir el modelo de datos maestro de Identidad y Ficha Tecnica

**Issue fuente**  
`DEV-6`

**Objetivo**  
Definir el contrato canonico de `Identity` y de `technical_sheet_json` para que toda identidad pueda persistirse, validarse y reutilizarse en Sistema 2 y futuro Sistema 5.

**Resultado esperado**  
Existe una especificacion de `Identity` versionada, con campos obligatorios, opcionales, enums controlados, estado inicial y correspondencia directa con persistencia relacional.

**Implementacion paso a paso**  
1. Extraer desde la base tecnica los campos de identidad descriptivos, visuales, narrativos, operativos y de trazabilidad.  
2. Separar los campos top-level persistidos en tabla de los campos anidados que viviran en `technical_sheet_json`.  
3. Definir enums y listas controladas para `status`, `pipeline_state`, `vertical` y `allowed_content_modes`.  
4. Declarar reglas de nulabilidad, valores por defecto y timestamps auditables.  
5. Documentar que slots de `technical_sheet_json` quedan listos para ser consumidos por Sistema 5.  
6. Validar que cada campo tenga una razon operacional y una futura ruta de uso.

**Decisiones tecnicas por defecto**  
- Usar schema Python con `Pydantic` o equivalente como contrato fuente.  
- Mantener `technical_sheet_json` como campo estructurado versionable, no como texto libre.  
- El estado inicial por defecto de una identidad nueva es `draft`.

**Entradas**  
- `technical_base_document.md`  
- arquitectura operativa  
- roadmap maestro

**Salidas**  
- schema `Identity`  
- contrato `technical_sheet_json`  
- definicion de `pipeline_state`  
- documento de correspondencia campo -> persistencia

**Dependencias**  
Ninguna.

**Herramientas y servicios a usar**  
Python, `Pydantic` o equivalente, `Supabase/Postgres`.

**Credenciales o accesos requeridos**  
No requiere credenciales para diseno.

**Validaciones fail-fast**  
- Si un campo requerido no tiene semantica clara, no se aprueba el contrato.  
- Si un campo de identidad no puede mapearse a persistencia ni a uso operativo, debe eliminarse o redefinirse.  
- Si `technical_sheet_json` mezcla contenido libre y estructurado sin reglas, la tarea no se considera cerrada.

**Artefactos tecnicos a producir**  
- schema versionado  
- documento de correspondencia campo a campo  
- tabla de enums y defaults

**Criterio de done**  
El equipo puede crear una identidad valida solo leyendo el contrato, sin inferir campos faltantes ni comportamiento implicito.

**Evidencia minima**  
Listado final de campos, tipos, obligatoriedad y ejemplo de payload valido.

**Siguiente tarea desbloqueada**  
Tareas 1.2 y 1.3.

**Responsable sugerido**  
Codex.

---

### TAREA 1.2 - Definir modelos de datos para Jobs, Artefactos y Catalogo de Modelos

**Issue fuente**  
`DEV-35`

**Objetivo**  
Agregar la capa de trazabilidad para jobs, artefactos y versiones de modelo.

**Resultado esperado**  
Existen contratos persistibles para `Job`, `Artifact` y `ModelRegistry`, con relaciones claras hacia `Identity` y hacia los procesos de entrenamiento y generacion.

**Implementacion paso a paso**  
1. Definir tipos de job del MVP: creacion de identidad, generacion de imagen base, armado de dataset, validacion de dataset, entrenamiento LoRA, generacion de contenido, preparacion de video, QA.  
2. Definir estados de job y reglas minimas de transicion.  
3. Definir tipos de artefacto: base image, dataset manifest, dataset package, lora model, workflow json, generated image, thumbnail, qa report.  
4. Definir `ModelRegistry` para modelos base, LoRAs y placeholders de video.  
5. Establecer claves de relacion: `identity_id`, `source_job_id`, `base_model_id`, `model_version_used`.  
6. Documentar que registros son obligatorios para cada flujo.

**Decisiones tecnicas por defecto**  
- Todo output relevante genera `Artifact`.  
- Todo proceso asincrono relevante genera `Job`.  
- Todo modelo ejecutable o referenciable genera `ModelRegistry`.  
- `payload_json` y `metadata_json` deben aceptar extensiones futuras sin romper compatibilidad.

**Entradas**  
- contrato `Identity`  
- requerimientos de Sistema 2  
- lista de procesos del MVP

**Salidas**  
- schema `Job`  
- schema `Artifact`  
- schema `ModelRegistry`  
- relaciones principales

**Dependencias**  
Tarea 1.1.

**Herramientas y servicios a usar**  
Python, `Supabase/Postgres`.

**Credenciales o accesos requeridos**  
No requiere credenciales para diseno.

**Validaciones fail-fast**  
- Si una imagen, dataset, LoRA o workflow no puede mapearse a un artefacto, el contrato esta incompleto.  
- Si un job no tiene `timeout_seconds`, `attempt_count` o error persistible, no esta listo para ejecucion real.  
- Si `ModelRegistry` no distingue modelo base de LoRA, debe corregirse antes de continuar.

**Artefactos tecnicos a producir**  
- especificacion de entidades tecnicas auxiliares  
- matriz flujo -> registro obligatorio

**Criterio de done**  
Todo artefacto critico y toda ejecucion importante del MVP puede persistirse y consultarse sin ambiguedad.

**Evidencia minima**  
Ejemplos validos de `Job`, `Artifact` y `ModelRegistry`.

**Siguiente tarea desbloqueada**  
Tareas 1.3, 1.4 y 3.2.

**Responsable sugerido**  
Codex.

---

### TAREA 1.3 - Crear la persistencia relacional de identidades, jobs, artefactos y modelos

**Objetivo**  
Materializar en `Supabase/Postgres` el contrato de datos maestro del MVP reforzado.

**Resultado esperado**  
Existen tablas, relaciones, restricciones e indices minimos para identidades, jobs, artefactos y catalogo de modelos.

**Implementacion paso a paso**  
1. Crear tablas `identities`, `jobs`, `artifacts` y `model_registry`.  
2. Agregar claves primarias, foraneas y restricciones de nulabilidad alineadas a los contratos.  
3. Agregar indices por `identity_id`, `status`, `pipeline_state`, `job_type`, `artifact_type`, `model_role`, `created_at`.  
4. Modelar campos JSON para `technical_sheet_json`, `payload_json` y `metadata_json`.  
5. Versionar migraciones o scripts SQL.  
6. Ejecutar una prueba minima de insercion y consulta sobre cada tabla.

**Decisiones tecnicas por defecto**  
- Usar migraciones versionadas como artefacto oficial.  
- Mantener timestamps en UTC.  
- Evitar logica de negocio en DB mas alla de constraints e indices.

**Entradas**  
- schemas de Tareas 1.1 y 1.2

**Salidas**  
- esquema SQL o migraciones  
- tablas creadas o documentadas  
- indices minimos

**Dependencias**  
Tareas 1.1 y 1.2.

**Herramientas y servicios a usar**  
`Supabase/Postgres`, SQLAlchemy o SQL directo.

**Credenciales o accesos requeridos**  
Credenciales de `Supabase/Postgres`.

**Validaciones fail-fast**  
- Si falta una clave foranea necesaria para trazabilidad, la migracion no se aprueba.  
- Si no existe indice para consultas operativas frecuentes, la persistencia queda incompleta.  
- Si una insercion de prueba no puede relacionar identidad con job, artefacto y modelo, la tarea falla.

**Artefactos tecnicos a producir**  
- migraciones versionadas  
- diagrama relacional minimo  
- script de smoke test SQL

**Criterio de done**  
El esquema puede soportar el flujo principal del MVP y las consultas operativas minimas sin cambios estructurales inmediatos.

**Evidencia minima**  
Prueba de insercion y consulta de las cuatro entidades principales.

**Siguiente tarea desbloqueada**  
Tareas 1.4, 1.5 y 3.1.

**Responsable sugerido**  
Codex o responsable backend.

---

### TAREA 1.4 - Integrar backend Python con base de datos y validaciones fail-fast

**Objetivo**  
Garantizar que el backend opere con contratos de datos consistentes y falle rapido ante configuraciones invalidas.

**Resultado esperado**  
Existe una capa de bootstrap y persistencia que valida configuracion critica al inicio y permite operar sobre DB con contratos estables.

**Implementacion paso a paso**  
1. Centralizar carga de variables de entorno de DB.  
2. Inicializar cliente o engine de base de datos.  
3. Validar conectividad, presencia de tablas y consistencia basica del esquema al arranque.  
4. Implementar repositorios o servicios de acceso a datos para identidades, jobs, artefactos y modelos.  
5. Unificar errores de configuracion y de conexion para exponer mensajes accionables.  
6. Registrar metricas o logs de arranque.

**Decisiones tecnicas por defecto**  
- Validar al inicio `SUPABASE_DB_URL` o equivalente antes de aceptar trafico.  
- No iniciar workers si el backend no puede consultar las tablas base.  
- Usar errores explicitamente tipados para credenciales faltantes, esquema faltante y timeout de conexion.

**Entradas**  
- esquema de DB  
- variables de entorno  
- contratos de entidad

**Salidas**  
- conexion estable a DB  
- capa de acceso a datos  
- validaciones de configuracion

**Dependencias**  
Tarea 1.3.

**Herramientas y servicios a usar**  
Python, ORM o query builder, `Supabase/Postgres`.

**Credenciales o accesos requeridos**  
Credenciales de DB.

**Validaciones fail-fast**  
- Si falta URL o credenciales de DB, el proceso debe abortar antes de exponer API o workers.  
- Si las tablas minimas no existen, el backend no debe seguir arrancando.  
- Si los contratos cargados y las columnas reales no coinciden, debe emitirse error explicito.

**Artefactos tecnicos a producir**  
- modulo de configuracion  
- modulo de bootstrap  
- repositorios o capa de persistencia

**Criterio de done**  
El backend arranca con entorno valido y falla con mensaje claro frente a variables faltantes o esquema inconsistente.

**Evidencia minima**  
Prueba de arranque exitoso y prueba de fallo controlado por variable critica ausente.

**Siguiente tarea desbloqueada**  
Tareas 1.5, 1.6 y 3.4.

**Responsable sugerido**  
Codex.

---

### TAREA 1.5 - Configurar storage para identidades, datasets, modelos y outputs

**Objetivo**  
Definir y habilitar la estrategia de almacenamiento escalable con trazabilidad por dominio y tipo de artefacto.

**Resultado esperado**  
Existen buckets o prefijos logicos para imagenes base, datasets, modelos LoRA, outputs y thumbnails, con convenciones de path estables.

**Implementacion paso a paso**  
1. Elegir `Supabase Storage` o `S3-compatible` como backend principal del MVP.  
2. Definir buckets o prefijos separados para identidades, datasets, modelos y contenidos.  
3. Establecer convencion de rutas por identidad, tipo de artefacto y version.  
4. Implementar wrapper de subida, lectura y borrado controlado.  
5. Integrar la salida del wrapper con `Artifact`.  
6. Ejecutar una subida y lectura de prueba por cada dominio.

**Decisiones tecnicas por defecto**  
- Separar por dominio logico y por identidad.  
- Incluir version o fecha en la ruta de datasets y modelos.  
- No almacenar rutas ad-hoc fuera del wrapper.

**Entradas**  
- decision de storage  
- contratos de `Artifact`  
- necesidades de imagen base, dataset, modelos y outputs

**Salidas**  
- estructura de buckets o prefijos  
- convencion de nombres  
- modulo de acceso a storage  
- mapeo `storage -> artifact registry`

**Dependencias**  
Tareas 1.2 y 1.4.

**Herramientas y servicios a usar**  
`Supabase Storage` o `S3-compatible`.

**Credenciales o accesos requeridos**  
Credenciales de storage.

**Validaciones fail-fast**  
- Si faltan credenciales de storage, no deben ejecutarse jobs que escriban artefactos.  
- Si una ruta no sigue convencion definida, el artefacto no se registra.  
- Si no puede leerse un archivo recien subido, la configuracion se considera invalida.

**Artefactos tecnicos a producir**  
- documento de rutas  
- wrapper de storage  
- prueba de conectividad por bucket o prefijo

**Criterio de done**  
El sistema puede subir y recuperar archivos de prueba en todos los dominios del MVP con rutas consistentes.

**Evidencia minima**  
Subida y lectura exitosa de un archivo de prueba por cada dominio.

**Siguiente tarea desbloqueada**  
Tareas 1.10, 1.12 y 2.9.

**Responsable sugerido**  
Codex o responsable infra.

---

### TAREA 1.6 - Definir verticales, personalidad, narrativa y limites operacionales

**Objetivo**  
Construir la taxonomia operativa que permite generar identidades coherentes y reutilizables.

**Resultado esperado**  
Existe un catalogo versionado con verticales, rasgos de personalidad, tonos, limites operacionales y modos permitidos de contenido.

**Implementacion paso a paso**  
1. Extraer verticales comerciales y rasgos narrativos desde la base tecnica.  
2. Definir listas controladas y estructura parametrizable.  
3. Separar rasgos obligatorios de rasgos opcionales.  
4. Definir `operational_limits` y `allowed_content_modes` con semantica clara.  
5. Preparar slots reutilizables para prompts, control humano y futuro chatbot.  
6. Validar que una identidad de prueba pueda construirse sin campos ambiguos.

**Decisiones tecnicas por defecto**  
- Mantener taxonomias en JSON o configuracion versionada dentro del backend.  
- Evitar texto libre como unica fuente de personalidad o limites.  
- Todo limite operativo debe poder reutilizarse en generacion y QA.

**Entradas**  
- base tecnica  
- decisiones de producto actuales

**Salidas**  
- listado de verticales  
- estructura de personalidad  
- politica de limites  
- slots reutilizables

**Dependencias**  
Tarea 1.1.

**Herramientas y servicios a usar**  
Backend Python, JSON o configuracion versionada.

**Credenciales o accesos requeridos**  
No requiere credenciales.

**Validaciones fail-fast**  
- Si un limite no puede traducirse a una regla operativa, debe reformularse.  
- Si una vertical no tiene impacto en prompts, estilo o restricciones, debe eliminarse o redefinirse.  
- Si dos catalogos se contradicen, no se aprueba la taxonomia.

**Artefactos tecnicos a producir**  
- catalogo versionado  
- ejemplos de combinaciones validas

**Criterio de done**  
Se pueden crear identidades de prueba sin necesidad de inventar valores ambiguos ni reglas fuera del catalogo.

**Evidencia minima**  
Payloads de identidad de ejemplo generados solo con la taxonomia definida.

**Siguiente tarea desbloqueada**  
Tarea 1.7.

**Responsable sugerido**  
Codex con revision humana.

---

### TAREA 1.7 - Implementar el generador estructurado de identidad y ficha tecnica

**Objetivo**  
Poder crear una identidad completa en formato estructurado, no solo descriptivo.

**Resultado esperado**  
Existe un servicio backend que produce una `Identity` valida con `technical_sheet_json`, vertical, narrativa, perfil visual y limites.

**Implementacion paso a paso**  
1. Crear servicio que reciba semilla de identidad o parametros iniciales.  
2. Resolver taxonomias de vertical, personalidad, tono y limites.  
3. Construir `technical_sheet_json` con estructura valida.  
4. Generar alias, narrativa base y perfil visual minimo.  
5. Validar el payload final contra el schema `Identity`.  
6. Dejar `pipeline_state` en `draft` o `identity_created` segun la politica elegida.

**Decisiones tecnicas por defecto**  
- Priorizar logica deterministica con plantillas y reglas.  
- `Llama.cpp` es opcional para enriquecer texto, no obligatorio para cerrar el MVP.  
- La salida del servicio debe ser persistible sin transformaciones adicionales.

**Entradas**  
- taxonomias operativas  
- schema `Identity`

**Salidas**  
- payload listo para persistir  
- `technical_sheet_json` completo  
- estado inicial

**Dependencias**  
Tareas 1.1, 1.4 y 1.6.

**Herramientas y servicios a usar**  
Python. `Llama.cpp` es opcional.

**Credenciales o accesos requeridos**  
No obligatorias si se usa logica local.

**Validaciones fail-fast**  
- Si el payload no valida contra el schema, no debe persistirse.  
- Si faltan `vertical`, `visual_profile` u `operational_limits`, la identidad se rechaza.  
- Si `technical_sheet_json` no incluye slots estructurados minimos, no se considera identidad completa.

**Artefactos tecnicos a producir**  
- servicio de creacion de identidad  
- ejemplos de payload generados

**Criterio de done**  
El servicio genera una identidad valida y reproducible sin edicion manual obligatoria.

**Evidencia minima**  
Creacion de al menos una identidad de prueba con todos los campos requeridos.

**Siguiente tarea desbloqueada**  
Tarea 1.8.

**Responsable sugerido**  
Codex.

---

### TAREA 1.8 - Persistir identidad creada y registrar estado inicial del pipeline

**Objetivo**  
Guardar cada identidad como entidad durable y habilitar su consumo por el resto del sistema.

**Resultado esperado**  
La identidad generada queda persistida con timestamps, `pipeline_state` inicial y relacion preparada para jobs y artefactos futuros.

**Implementacion paso a paso**  
1. Recibir payload validado de identidad.  
2. Insertar el registro en `identities`.  
3. Aplicar estado inicial definido.  
4. Registrar metadata minima de creacion y actor solicitante si aplica.  
5. Exponer mecanismo de consulta por id.  
6. Confirmar que la identidad recien creada puede consumirse por tareas posteriores.

**Decisiones tecnicas por defecto**  
- Persistir en una transaccion unica.  
- El estado final de esta tarea debe ser `identity_created`.  
- No crear jobs ni artefactos artificiales si la operacion es totalmente sincrona.

**Entradas**  
- payload de identidad validado

**Salidas**  
- registro persistido  
- estado inicial utilizable  
- base relacional para jobs y artefactos futuros

**Dependencias**  
Tareas 1.4 y 1.7.

**Herramientas y servicios a usar**  
Python, `Supabase/Postgres`.

**Credenciales o accesos requeridos**  
DB.

**Validaciones fail-fast**  
- Si la identidad no valida, no se inserta.  
- Si la transaccion falla, no debe quedar estado parcial.  
- Si la identidad no puede consultarse luego de insertada, la tarea no se considera cerrada.

**Artefactos tecnicos a producir**  
- caso de uso transaccional de alta de identidad  
- consulta de recuperacion por id

**Criterio de done**  
Una identidad creada puede recuperarse por DB o API con estado `identity_created`.

**Evidencia minima**  
Insercion y consulta exitosa de una identidad de prueba.

**Siguiente tarea desbloqueada**  
Tareas 1.9 y 1.10.

**Responsable sugerido**  
Codex.

---

### TAREA 1.9 - Registrar catalogo de modelos base y compatibilidades

**Objetivo**  
Dejar explicito que modelo base usa cada identidad y con que pipeline es compatible.

**Resultado esperado**  
Existe un catalogo inicial de modelos base para imagen y placeholders de video, con compatibilidades declaradas.

**Implementacion paso a paso**  
1. Registrar al menos un modelo base de imagen y un placeholder de modelo de video.  
2. Definir `model_family`, `model_role`, `provider`, `version_name` y notas de compatibilidad.  
3. Documentar compatibilidad con `ComfyUI`, LoRA, `IP-Adapter`, `ControlNet` y video.  
4. Definir politica de versionado para modelos base y LoRA.  
5. Vincular identidad con `base_model_id` valido.  
6. Verificar que el catalogo soporta reemplazo futuro sin cambios en el contrato.

**Decisiones tecnicas por defecto**  
- Modelo base de imagen es obligatorio para generar imagenes base y contenido.  
- Modelo base de video puede quedar como contrato preparado.  
- `ModelRegistry` debe distinguir modelo activo de historicos.

**Entradas**  
- decisiones tecnicas sobre modelos  
- contrato `ModelRegistry`

**Salidas**  
- registros en `model_registry`  
- politica de versionado  
- asociacion `identity -> base_model_id`

**Dependencias**  
Tareas 1.2 y 1.3.

**Herramientas y servicios a usar**  
`Supabase/Postgres`, backend Python.

**Credenciales o accesos requeridos**  
DB.

**Validaciones fail-fast**  
- Si una identidad no puede referenciar un `base_model_id` valido, no puede avanzar a generacion.  
- Si compatibilidades clave no estan documentadas, el catalogo queda incompleto.  
- Si se intenta registrar un modelo sin `model_role`, debe rechazarse.

**Artefactos tecnicos a producir**  
- catalogo versionado de modelos  
- notas de compatibilidad

**Criterio de done**  
Cada identidad puede apuntar a un modelo base valido y el sistema conoce con que pipeline es compatible.

**Evidencia minima**  
Consulta de `model_registry` con al menos un modelo base de imagen y un placeholder de video.

**Siguiente tarea desbloqueada**  
Tareas 1.10, 1.14 y 2.1.

**Responsable sugerido**  
Codex con validacion tecnica humana.

---

### TAREA 1.10 - Generar imagenes base de identidad mediante workflow visual controlado

**Objetivo**  
Producir imagenes base coherentes para cada identidad usando el motor visual previsto.

**Resultado esperado**  
Existe un flujo reproducible de generacion de imagenes base que consume identidad y modelo base, dispara un workflow versionado y deja trazabilidad completa.

**Implementacion paso a paso**  
1. Seleccionar o crear un `workflow_id` inicial en `ComfyUI` para imagen base.  
2. Resolver inputs minimos: identidad, `base_model_id`, prompt, negative prompt, seed, dimensiones, cantidad de imagenes.  
3. Crear un `Job` de tipo `generate_base_images` con timeout y retries definidos.  
4. Invocar `ComfyUI` directamente o a traves de proveedor GPU segun arquitectura.  
5. Capturar resultado, parametros reales usados y errores del workflow.  
6. Actualizar el job y el `pipeline_state` de la identidad a `base_images_generated` si todo salio bien.

**Decisiones tecnicas por defecto**  
- `ComfyUI` es el motor visual canonico del MVP.  
- Todo workflow se identifica por `workflow_id` y version operativa.  
- La generacion de imagenes base debe ser reproducible mediante prompt, seed y workflow registrado.  
- Si se usa `Modal` o `Runpod`, el contrato superior no cambia.

**Entradas**  
- identidad persistida  
- modelo base asignado  
- workflow de imagen base  
- configuracion de proveedor

**Salidas**  
- imagenes base generadas  
- registro de job  
- metadata de ejecucion  
- identidad en `base_images_generated`

**Dependencias**  
Tareas 1.5, 1.8 y 1.9.

**Herramientas y servicios a usar**  
`ComfyUI`, modelo base de imagen, `Modal` o `Runpod` si aplica.

**Credenciales o accesos requeridos**  
Endpoint GPU y/o `ComfyUI`.

**Validaciones fail-fast**  
- Si falta `base_model_id`, la generacion no debe iniciar.  
- Si falta `workflow_id` activo o endpoint accesible, el job debe fallar con error persistido.  
- Si no se puede reconstruir prompt, seed y workflow usados, la tarea no se considera trazable.

**Artefactos tecnicos a producir**  
- workflow de imagen base  
- wrapper backend de ejecucion  
- contrato de payload de generacion base

**Criterio de done**  
La identidad puede producir un set base de imagenes con parametros reproducibles y job trazable.

**Evidencia minima**  
Un job exitoso con prompt, seed, workflow y referencia a archivos generados.

**Siguiente tarea desbloqueada**  
Tarea 1.11.

**Responsable sugerido**  
Codex o responsable de pipeline visual.

---

### TAREA 1.11 - Almacenar y registrar imagenes base con artifact registry

**Objetivo**  
Registrar formalmente las imagenes base producidas y dejarlas disponibles para dataset y consistencia de identidad.

**Resultado esperado**  
Las imagenes base quedan almacenadas en storage y registradas como `Artifact`, con checksum, metadata y relacion al job origen.

**Implementacion paso a paso**  
1. Subir cada imagen base al dominio de storage correspondiente.  
2. Generar checksum o referencia de integridad.  
3. Crear un `Artifact` por imagen base.  
4. Actualizar `base_image_urls` y `reference_face_image_url` cuando corresponda.  
5. Mantener referencia a `source_job_id`, prompt, seed y workflow en `metadata_json`.  
6. Marcar el `pipeline_state` como `base_images_registered`.

**Decisiones tecnicas por defecto**  
- Toda imagen base debe tener artefacto dedicado.  
- Una de las imagenes base debe quedar marcada como referencia facial primaria.  
- `base_image_urls` se considera cache util, pero la fuente de verdad de trazabilidad es `Artifact`.

**Entradas**  
- outputs de la Tarea 1.10  
- job de origen  
- wrapper de storage

**Salidas**  
- imagenes base en storage  
- registros `Artifact`  
- campos de identidad actualizados  
- estado `base_images_registered`

**Dependencias**  
Tareas 1.5 y 1.10.

**Herramientas y servicios a usar**  
Storage, DB, backend Python.

**Credenciales o accesos requeridos**  
Storage y DB.

**Validaciones fail-fast**  
- Si una imagen no puede subirse, no debe registrarse como artefacto exitoso.  
- Si no se genera checksum o metadata minima, el artefacto queda incompleto.  
- Si la identidad no queda apuntando a imagenes recuperables, la tarea no se cierra.

**Artefactos tecnicos a producir**  
- modulo de registro de imagenes base  
- convencion de metadata de base image

**Criterio de done**  
Cada imagen base del flujo tiene archivo recuperable, artefacto persistido y vinculo claro con identidad y job origen.

**Evidencia minima**  
Consulta que devuelve al menos una imagen base con su `Artifact` asociado y checksum.

**Siguiente tarea desbloqueada**  
Tarea 1.12.

**Responsable sugerido**  
Codex.

---

### TAREA 1.12 - Preparar dataset balanceado con y sin ropa por identidad

**Objetivo**  
Construir un dataset apto para entrenamiento y consistente con la base tecnica.

**Resultado esperado**  
Existe un pipeline de armado de dataset que toma imagenes base y otras referencias permitidas, genera un manifest versionado y deja el dataset listo para validacion.

**Implementacion paso a paso**  
1. Definir reglas de composicion del dataset: conteo minimo, proporcion SFW/NSFW, naming y estructura de carpetas.  
2. Recolectar imagenes base y referencias habilitadas.  
3. Normalizar formato, dimensiones o metadata segun requerimiento del trainer.  
4. Crear `manifest` con lista de archivos, clase, origen y version.  
5. Subir dataset y manifest a storage.  
6. Registrar dataset como `Artifact` y actualizar `dataset_storage_path`.

**Decisiones tecnicas por defecto**  
- El dataset debe ser balanceado entre con ropa y sin ropa segun politica definida.  
- El manifest es obligatorio y se considera parte del dataset.  
- El dataset se versiona por identidad y por corrida de preparacion.

**Entradas**  
- imagenes base  
- reglas de dataset  
- modelo base asignado

**Salidas**  
- dataset estructurado  
- manifest versionado  
- registro de artefacto dataset  
- `dataset_storage_path`

**Dependencias**  
Tareas 1.5 y 1.11.

**Herramientas y servicios a usar**  
Backend Python, storage, DB.

**Credenciales o accesos requeridos**  
Storage y DB.

**Validaciones fail-fast**  
- Si no hay suficientes imagenes base validas, no se arma dataset.  
- Si el manifest no describe composicion, origen y version, no se considera dataset util.  
- Si el dataset no puede localizarse por path estable, no puede avanzar a validacion.

**Artefactos tecnicos a producir**  
- builder de dataset  
- manifest versionado  
- registro de dataset en `Artifact`

**Criterio de done**  
El dataset puede localizarse, inspeccionarse y reutilizarse para entrenamiento con metadata suficiente.

**Evidencia minima**  
Manifest de dataset y artefacto persistido con composicion declarada.

**Siguiente tarea desbloqueada**  
Tarea 1.13.

**Responsable sugerido**  
Codex.

---

### TAREA 1.13 - Definir criterios tecnicos de calidad del dataset y validacion previa a entrenamiento

**Objetivo**  
Evitar entrenamientos sobre datasets incompletos, inconsistentes o no trazables.

**Resultado esperado**  
Existe un validador de dataset con reglas de aceptacion y bloqueo, capaz de producir resultado `apto` o `no apto` con razones persistibles.

**Implementacion paso a paso**  
1. Definir umbrales minimos de cantidad, composicion y diversidad basica.  
2. Validar presencia de manifest, archivos existentes y paths consistentes.  
3. Validar metadata minima requerida por el entrenador.  
4. Generar reporte estructurado con hallazgos.  
5. Marcar el dataset como apto o no apto.  
6. Solo si es apto, actualizar estado a `dataset_ready`.

**Decisiones tecnicas por defecto**  
- No se entrena sobre datasets sin manifest versionado.  
- El validador debe ser determinista y ejecutable sin intervencion humana.  
- La validacion humana puede complementar, pero no reemplaza la validacion tecnica minima.

**Entradas**  
- dataset preparado  
- reglas de aceptacion  
- manifest

**Salidas**  
- resultado `apto/no apto`  
- motivos de rechazo trazables  
- `pipeline_state` actualizado si corresponde

**Dependencias**  
Tarea 1.12.

**Herramientas y servicios a usar**  
Backend Python, DB, storage.

**Credenciales o accesos requeridos**  
Storage y DB.

**Validaciones fail-fast**  
- Si falta manifest, el dataset se rechaza.  
- Si faltan archivos listados o hay inconsistencia entre manifest y storage, se rechaza.  
- Si el dataset es `no apto`, el entrenamiento no debe lanzarse.

**Artefactos tecnicos a producir**  
- validador de dataset  
- reporte de validacion

**Criterio de done**  
Un dataset invalido bloquea de manera explicita el entrenamiento y uno valido actualiza estado a `dataset_ready`.

**Evidencia minima**  
Un ejemplo de validacion exitosa y un ejemplo de rechazo con motivos.

**Siguiente tarea desbloqueada**  
Tarea 1.14.

**Responsable sugerido**  
Codex.

---

### TAREA 1.14 - Integrar entrenamiento LoRA compatible con FluxSchnell y GPU externa

**Objetivo**  
Preparar el flujo de entrenamiento automatizable que genera un LoRA por identidad.

**Resultado esperado**  
Existe una interfaz desacoplada de entrenamiento que recibe dataset validado, modelo base y configuracion de proveedor, y dispara un job trazable en GPU externa o pipeline equivalente.

**Implementacion paso a paso**  
1. Diseñar contrato `train_lora(...)` con inputs minimos: identidad, dataset, modelo base, provider, version objetivo e hiperparametros relevantes.  
2. Crear adaptador de entrenamiento compatible con `FluxSchnell` o equivalente.  
3. Crear `Job` de tipo `train_lora` con timeout y retries.  
4. Mapear el job a `Modal` o `Runpod` sin acoplar la capa superior al proveedor.  
5. Persistir payload, provider y referencias de dataset y modelo base.  
6. Actualizar estado a `lora_training_pending` y luego `lora_training_running` cuando corresponda.

**Decisiones tecnicas por defecto**  
- `FluxSchnell` es la opcion prioritaria; puede reemplazarse por adaptador equivalente sin cambiar contrato.  
- El entrenamiento es asincrono por defecto.  
- La salida esperada es un archivo LoRA versionado mas metadata del entrenamiento.

**Entradas**  
- dataset validado  
- `base_model_id`  
- configuracion de proveedor GPU  
- reglas de versionado

**Salidas**  
- job de entrenamiento lanzado  
- payload de entrenamiento persistido  
- estado de pipeline actualizado

**Dependencias**  
Tareas 1.9 y 1.13.

**Herramientas y servicios a usar**  
Python, `FluxSchnell` o equivalente, `Modal` o `Runpod`.

**Credenciales o accesos requeridos**  
Credenciales del proveedor GPU y/o trainer.

**Validaciones fail-fast**  
- Si el dataset no esta `apto`, no se lanza entrenamiento.  
- Si falta `base_model_id`, el job se bloquea.  
- Si falta endpoint o credencial del proveedor elegido, el job falla antes de consumir recursos.  
- Si no se persiste el payload del entrenamiento, no hay trazabilidad suficiente.

**Artefactos tecnicos a producir**  
- adaptador de entrenamiento LoRA  
- payload de entrenamiento versionado  
- contrato proveedor -> job

**Criterio de done**  
El sistema puede lanzar un entrenamiento LoRA real o simulado con referencias completas a dataset, modelo base y proveedor.

**Evidencia minima**  
Un job `train_lora` persistido con payload, timeout, retries y estado de ejecucion.

**Siguiente tarea desbloqueada**  
Tarea 1.15.

**Responsable sugerido**  
Codex o responsable ML.

---

### TAREA 1.15 - Almacenar LoRA entrenado y registrar version, compatibilidad y validacion

**Objetivo**  
Cerrar el ciclo de entrenamiento con versionado formal del LoRA por identidad.

**Resultado esperado**  
El LoRA entrenado queda almacenado como artefacto, registrado en `model_registry`, enlazado a la identidad y listo para validacion humana.

**Implementacion paso a paso**  
1. Recuperar salida del job de entrenamiento.  
2. Subir el archivo LoRA al storage de modelos.  
3. Registrar `Artifact` del LoRA con checksum y metadata del entrenamiento.  
4. Registrar el LoRA en `model_registry` como nueva version.  
5. Actualizar `lora_model_path`, `lora_version` y `base_model_id` de la identidad.  
6. Marcar estado de pipeline en `lora_trained`.

**Decisiones tecnicas por defecto**  
- Todo LoRA entrenado es versionado y no sobrescribe historico.  
- `compatibility_notes` debe indicar el modelo base con el que es compatible.  
- El LoRA no se considera operativo para generacion final hasta pasar validacion humana.

**Entradas**  
- salida del job `train_lora`  
- metadata del entrenamiento  
- storage de modelos

**Salidas**  
- artefacto LoRA almacenado  
- registro en `model_registry`  
- identidad actualizada  
- estado `lora_trained`

**Dependencias**  
Tareas 1.5 y 1.14.

**Herramientas y servicios a usar**  
Storage, DB, backend Python.

**Credenciales o accesos requeridos**  
Storage y DB.

**Validaciones fail-fast**  
- Si el job no produjo archivo recuperable, no se registra LoRA.  
- Si el LoRA no puede asociarse a un modelo base valido, no se publica en catalogo.  
- Si no hay checksum o metadata minima, el artefacto queda incompleto.

**Artefactos tecnicos a producir**  
- modulo de registro de LoRA entrenado  
- entrada versionada en `model_registry`

**Criterio de done**  
La identidad apunta a un LoRA versionado, recuperable y asociado a su modelo base.

**Evidencia minima**  
Consulta de identidad con `lora_model_path`, `lora_version` y referencia a `model_registry`.

**Siguiente tarea desbloqueada**  
Tarea 1.16 y Tarea 2.5.

**Responsable sugerido**  
Codex.

---

### TAREA 1.16 - Validar manualmente la consistencia visual del modelo entrenado

**Objetivo**  
Confirmar con evidencia humana que el LoRA entrenado mantiene la identidad esperada antes de usarlo para generacion masiva.

**Resultado esperado**  
Existe una validacion humana estructurada que marca el LoRA como aprobado, rechazado o sujeto a retraining.

**Implementacion paso a paso**  
1. Generar muestras de prueba controladas usando el LoRA entrenado.  
2. Presentar las muestras junto con referencia facial y metadata basica.  
3. Evaluar consistencia de rostro, cuerpo, estilo y estabilidad general.  
4. Registrar resultado de validacion humana y observaciones.  
5. Si aprueba, mover estado a `lora_validated`.  
6. Si rechaza, dejar trazabilidad del motivo y ruta de reentrenamiento.

**Decisiones tecnicas por defecto**  
- La validacion humana es obligatoria para cerrar el ciclo del LoRA en MVP.  
- Debe existir un formato de decision simple: `approved`, `rejected`, `needs_retraining`.  
- El rechazo no elimina el LoRA; lo deja historizado con estado correspondiente.

**Entradas**  
- LoRA entrenado  
- muestras de prueba  
- referencias de identidad

**Salidas**  
- decision humana  
- observaciones  
- estado `lora_validated` o rechazo documentado

**Dependencias**  
Tarea 1.15.

**Herramientas y servicios a usar**  
Dashboard, storage, DB.

**Credenciales o accesos requeridos**  
Acceso a dashboard o storage.

**Validaciones fail-fast**  
- Si no hay muestras comparables, no se valida.  
- Si no queda registro de la decision, el estado no cambia.  
- Si el LoRA es rechazado, no debe habilitarse generacion principal con ese modelo.

**Artefactos tecnicos a producir**  
- registro de validacion humana  
- muestras de prueba asociadas

**Criterio de done**  
El LoRA queda claramente aprobado o rechazado con evidencia humana trazable.

**Evidencia minima**  
Registro de decision y muestras revisadas.

**Siguiente tarea desbloqueada**  
Tarea 2.5.

**Responsable sugerido**  
Humano con soporte del sistema.
