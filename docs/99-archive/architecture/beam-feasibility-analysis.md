# Analisis de Factibilidad: Beam como Proveedor GPU

> Estado: `archivado`
> Fecha de archivo: `2026-04-10`
> Motivo: analisis historico de proveedor que ya no gobierna decisiones activas del repo.
> Reemplazo vigente: `docs/01-architecture/technical-base.md` para estado tecnico actual. Este documento se conserva solo como referencia historica.

## Objetivo

Evaluar si `Beam` es factible como reemplazo estrategico de la capa GPU del proyecto para:

- `S1 image`
- `S2 image`
- `LoRA training`
- `video`

El enfoque de este analisis asume:

- mantener `ComfyUI` como core del runtime
- preservar los contratos actuales del motor visual
- minimizar el delta tecnico respecto del estado actual del repo

Fecha de corte de la evaluacion:

- `2026-04-02`

## Resumen Ejecutivo

Recomendacion ejecutiva:

- `GO CON LIMITES`: `Beam` es factible para inference GPU basada en `ComfyUI` y como plan de contingencia real frente a indisponibilidad de `Runpod`, pero hoy no conviene decidir una migracion total e inmediata de toda la capa GPU sin un piloto acotado en `S1 image`.

Lectura corta:

- para `S1 image` y `S2 image`, `Beam` encaja bien por modelo operativo, DX y disponibilidad declarada de `A10G`, `RTX4090` y `H100`
- para `LoRA training` y `video`, `Beam` sigue siendo viable, pero el salto de `24 Gi` a `80 Gi` deja menos escalones intermedios que `Runpod`
- el mayor beneficio de `Beam` no es solo precio: es la combinacion de `deploy + shell + logs + task queues + volumes + buckets`
- el mayor costo de `Beam` es que factura `GPU + CPU + RAM`, por lo que el costo all-in puede quedar por encima de la lectura superficial de GPU/hora
- el mayor riesgo de migracion no esta en el contrato Python, sino en la infraestructura `infra/runpod-*`, las variables `RUNPOD_*` y el paquete de tests/serverless especifico

## Foto Actual del Repo

### Superficie ya reemplazable por contrato

El repo ya tiene una base razonable para desacoplar proveedor:

- `src/vixenbliss_creator/visual_pipeline/models.py`
  - existe un enum `Provider` con `comfyui` y `runpod`
- `src/vixenbliss_creator/visual_pipeline/adapters.py`
  - existe `build_visual_execution_client()`
  - el backend ya diferencia entre consumo HTTP directo a `ComfyUI` y consumo `Runpod Serverless`
- `src/vixenbliss_creator/visual_pipeline/service.py`
  - la orquestacion del pipeline no depende de detalles de `Runpod`

Conclusion:

- la capa de aplicacion ya esta orientada a un modelo `provider adapter`
- agregar `Provider.BEAM` es un cambio acotado en la superficie Python

### Superficie todavia especifica de Runpod

La integracion productiva real sigue estando cargada hacia `Runpod`:

- `infra/runpod-s1-image-serverless/`
- `infra/runpod-visual-serverless/`
- `infra/runpod-s1-model-loader/`
- `tests/test_visual_pipeline_runpod.py`
- `tests/test_runpod_*`
- docs y onboarding con foco operativo en `Runpod MCP`, `Runpod CLI`, endpoints y network volumes

Hallazgo operativo:

- el acople fuerte hoy esta en `infra/`, `tests/` y `docs`
- el acople mas bajo esta en el contrato del motor visual

## Necesidades Reales del Proyecto

Para que un proveedor GPU sirva de verdad en este repo, tiene que cubrir:

1. ejecutar runtimes `ComfyUI` en contenedores custom
2. soportar jobs asincronos y polling de estado
3. persistir pesos pesados entre corridas
4. montar `S3-compatible` para datasets y artifacts
5. permitir debug de workers GPU con logs utiles y shell interactiva
6. soportar timeouts, retries y warmup
7. dejar una experiencia de deploy simple desde este entorno Windows

## Beam vs Necesidades del Repo

### Compatibilidad operativa

`Beam` cubre bien el modelo de ejecucion que el repo necesita:

- GPUs disponibles declaradas:
  - `A10G` (`24Gi`)
  - `RTX4090` (`24Gi`)
  - `H100` (`80Gi`)
  - fuente: [GPU Acceleration](https://docs.beam.cloud/v2/environment/gpu)
- jobs largos y asincronos:
  - `task_queue` para tareas largas y polling por `task_id`
  - fuente: [Running Async Tasks](https://docs.beam.cloud/v2/task-queue/running-tasks)
  - fuente: [Querying Task Status](https://docs.beam.cloud/v2/task-queue/query-status)
- deploy y desarrollo:
  - `beam deploy`
  - `beam serve`
  - `beam shell`
  - `beam logs`
  - fuente: [CLI Reference](https://docs.beam.cloud/v2/reference/cli)
- imagenes custom y registries:
  - Beam soporta base images y custom registries, incluyendo `GHCR`
  - fuente: [Custom Registries](https://docs.beam.cloud/v2/environment/custom-registries)
- persistencia:
  - `Beam Volumes` para pesos/cache
  - `CloudBucket` para buckets propios `S3-compatible`
  - fuente: [Distributed Storage Volumes](https://docs.beam.cloud/v2/data/volume)
  - fuente: [Configuration](https://docs.beam.cloud/v2/sandbox/configuration)
- warmup, cold start, retries:
  - `keep_warm_seconds`
  - `min_containers`
  - caches en volumes
  - `timeout` y `retries`
  - fuente: [Keeping Containers Warm](https://docs.beam.cloud/v2/endpoint/keep-warm)
  - fuente: [Cold Start Performance](https://docs.beam.cloud/v2/topics/cold-start)
  - fuente: [Timeouts and Retries](https://docs.beam.cloud/v2/topics/timeouts-and-retries)

### Gaps concretos frente a Runpod

#### 1. Menos escalones de VRAM

Beam hoy documenta solo:

- `24 Gi` (`A10G`, `RTX4090`)
- `80 Gi` (`H100`)

Mientras que el editor de endpoint de `Runpod` mostrado en la captura compartida el `2026-04-02` expone muchos mas escalones:

- `16 GB`
- `24 GB`
- `24 GB PRO`
- `32 GB PRO`
- `48 GB`
- `48 GB PRO`
- `80 GB`
- `80 GB PRO`
- `96 GB`
- `141 GB`
- `180 GB PRO`

Impacto:

- `Beam` encaja muy bien para runtimes que ya viven en `24 Gi`
- para `training` y ciertos flujos de `video`, la falta de escalones intermedios obliga a decidir antes si el runtime entra en `24 Gi` o salta a `80 Gi`

#### 2. Windows requiere WSL

Beam documenta instalacion en Windows via `WSL`, no como CLI nativa primero:

- fuente: [Installation](https://docs.beam.cloud/v2/getting-started/installation)

Impacto:

- si el equipo adopta `Beam` en serio, conviene asumir `WSL` como baseline operativo para developers en Windows

#### 3. Menor continuidad con lo ya construido

El runtime actual del repo no solo usa `ComfyUI`; usa un bundle muy definido alrededor de `Runpod Serverless`:

- handler `Runpod`
- polling `/run`, `/runsync`, `/status`
- `RUNPOD_*`
- network volumes
- scripts de carga especificos

Impacto:

- el cambio no es un simple flip de variable
- hay que construir un runtime hermano `infra/beam-*` y pruebas paralelas

## Modelo de Costo y Operacion

## Beam: precios oficiales actuales

Segun la documentacion oficial de Beam:

- CPU: `$0.190/core/h`
- RAM: `$0.020/GB/h`
- `RTX4090`: `$0.69/h`
- `A10G`: `$1.05/h`
- `H100`: `$3.50/h`
- storage de archivos: `included`

Fuente:

- [Pricing and Billing](https://docs.beam.cloud/v2/resources/pricing-and-billing)

## Runpod: baseline usado para comparar

Para `Runpod` se toma como baseline la captura compartida por el usuario el `2026-04-02`, porque refleja el problema operativo que disparo este analisis y contiene los precios visibles en el editor del endpoint:

- `24 GB`: `$0.00019/s` -> `~$0.684/h`
- `16 GB`: `$0.00016/s` -> `~$0.576/h`
- `24 GB PRO`: `$0.00031/s` -> `~$1.116/h`
- `48 GB`: `$0.00034/s` -> `~$1.224/h`
- `80 GB`: `$0.00076/s` -> `~$2.736/h`
- `80 GB PRO`: `$0.00116/s` -> `~$4.176/h`

Observacion importante:

- la captura muestra precio por tier GPU en `Runpod`
- Beam publica `GPU + CPU + RAM` por separado
- por eso conviene comparar dos vistas:
  - `GPU pura`
  - `estimacion all-in`

## Comparativa por runtime

### 1. `S1 image` - inferencia `24 Gi` equivalente

Perfil mas probable:

- `ComfyUI`
- `Flux`
- `IP-Adapter`
- `FaceDetailer`
- runtime corto o mediano

Comparativa:

| Opcion | GPU VRAM | Costo visible |
|---|---:|---:|
| Runpod `24 GB` | 24 GB | `~$0.684/h` |
| Runpod `24 GB PRO` | 24 GB | `~$1.116/h` |
| Beam `RTX4090` | 24 Gi | `$0.69/h` |
| Beam `A10G` | 24 Gi | `$1.05/h` |

Lectura:

- a nivel `GPU pura`, `Beam RTX4090` y `Runpod 24 GB` quedan casi empatados
- `Beam A10G` tambien es competitivo frente a `Runpod 24 GB PRO`
- la diferencia practica es que hoy `Runpod 24 GB` esta apareciendo como `Unavailable` en la captura, mientras que Beam publica `beam machine list` para verificar disponibilidad en tiempo real

Estimacion Beam all-in para un runtime conservador:

- `2 CPU + 16 Gi RAM + RTX4090` -> `0.38 + 0.32 + 0.69 = ~$1.39/h`
- `2 CPU + 16 Gi RAM + A10G` -> `0.38 + 0.32 + 1.05 = ~$1.75/h`

Conclusion:

- si solo se mira GPU, `Beam` compite bien
- si se mira costo total de contenedor, `Beam` queda por encima del precio visible de `Runpod 24 GB`
- aun asi, `S1 image` es el mejor candidato para un piloto porque el ajuste tecnico es bajo y resuelve el dolor actual de disponibilidad

### 2. `S2 image` - inferencia sostenida

Comparativa base:

- misma clase de `24 Gi` que `S1 image`
- mas sensible a:
  - `keep_warm_seconds`
  - `min_containers`
  - colas
  - caching de pesos

Lectura:

- `Beam` ofrece mejor caja de herramientas para una operacion sostenida:
  - `task_queue`
  - `min_containers`
  - `/warmup`
  - `logs`
  - `shell`
  - volumes nativos
- pero el costo all-in castiga mas si se decide dejar contenedores calientes por mucho tiempo

Conclusion:

- `Beam` es factible para `S2 image`
- el costo queda aceptable si el runtime opera mayormente `scale-to-zero`
- si se decide operar `always-on`, el costo debe recalcularse con mucho cuidado

### 3. `LoRA training`

Escenario probable:

- algunos trainings podrian entrar en `24 Gi`
- otros empujarian a `80 Gi`

Comparativa de referencia:

| Opcion | GPU VRAM | Costo visible |
|---|---:|---:|
| Runpod `80 GB` | 80 GB | `~$2.736/h` |
| Runpod `80 GB PRO` | 80 GB | `~$4.176/h` |
| Beam `H100` | 80 Gi | `$3.50/h` |

Estimacion Beam all-in para training:

- `4 CPU + 32 Gi RAM + H100` -> `0.76 + 0.64 + 3.50 = ~$4.90/h`

Lectura:

- `Beam H100` queda por encima de `Runpod 80 GB` standard
- `Beam H100` queda por debajo de `Runpod 80 GB PRO`
- si el driver de la migracion es disponibilidad, `Beam` sigue siendo viable
- si el driver principal es `costo puro`, `Runpod` sigue siendo mejor mientras haya stock real

Conclusion:

- `Beam` sirve para `LoRA training`
- no es el punto de entrada ideal para la migracion

### 4. `video`

Escenario probable:

- `video` sera el runtime mas sensible a VRAM, warmup y tiempo de ejecucion
- segun pipeline final, podria vivir en `24 Gi` o saltar rapido a `80 Gi`

Lectura:

- `Beam` es operativamente apto
- pero su catalogo publico de GPU deja menos espacio para optimizar entre tiers
- si `Wan2.2` o runtime final exige `80 Gi`, Beam vuelve a competir contra `Runpod 80 GB` y no contra sus tiers medios

Conclusion:

- `video` es viable en Beam
- no deberia ser la primera migracion

## DX, Deploy, Debug y Conexion desde este Entorno

### Conectividad basica desde esta maquina

Pruebas ejecutadas localmente el `2026-04-02` desde esta workstation:

- `Test-NetConnection beam.cloud -Port 443` -> `TcpTestSucceeded=True`
- `Test-NetConnection api.beam.cloud -Port 443` -> `TcpTestSucceeded=True`
- `Test-NetConnection api.runpod.io -Port 443` -> `TcpTestSucceeded=True`

Mediciones HTTP simples:

- `https://beam.cloud` -> `~977 ms`
- `https://www.runpod.io` -> `~409 ms`

Lectura:

- no hay bloqueo de red evidente hacia `Beam`
- `Runpod` respondio mas rapido en la prueba superficial de landing page
- esta prueba no mide throughput real de datasets o modelos, solo reachability basica y latencia web inicial

### Experiencia de desarrollo

Ventajas claras de Beam para DX:

- `beam serve` para preview remoto con hot reload
- `beam shell` para entrar al contenedor
- `beam logs` por deployment, task o container
- `beam volume` y `beam cp` para mover archivos y cache
- manejo unificado de `secrets`

Fuentes:

- [CLI Reference](https://docs.beam.cloud/v2/reference/cli)
- [Creating a Web Endpoint](https://docs.beam.cloud/v2/endpoint/overview)

Comparado con el baseline actual del repo:

- `Runpod` esta mejor documentado internamente en este proyecto
- `Beam` ofrece una DX mas compacta y cohesionada out-of-the-box

Conclusion:

- para deploy y debug, `Beam` es mas amigable que el bundle actual basado en `Runpod Serverless`
- para adopcion inmediata del equipo en Windows, `Beam` mete una dependencia fuerte en `WSL`

## Tabla de Decision

| Criterio | Beam | Runpod hoy |
|---|---|---|
| GPU `24 Gi` | `A10G`, `RTX4090` | si, pero la captura muestra falta de stock |
| GPU `80 Gi` | `H100` | si |
| Escalones intermedios | mas limitado | mas amplio |
| Async jobs | muy bueno con `task_queue` | bueno con serverless endpoint + polling |
| Debug shell | muy bueno | mas fragmentado |
| Logs | muy bueno | bueno, mas dependiente de consola/herramientas |
| Volumes | nativos | buenos, hoy ya usados |
| Montaje bucket propio | si | si |
| Deploy DX | muy buena | aceptable |
| Windows | requiere `WSL` | hoy el equipo ya opera desde Windows con tooling actual |
| Costo GPU puro 24 Gi | competitivo | muy competitivo |
| Costo all-in | puede subir bastante | menos transparente en la comparacion visible |

## Delta Tecnico Real si se Aprueba Migracion

Cambios esperados de menor riesgo:

### Capa Python

- agregar `Provider.BEAM` en `src/vixenbliss_creator/visual_pipeline/models.py`
- agregar `BeamExecutionClient` en `src/vixenbliss_creator/visual_pipeline/adapters.py`
- extender `VisualPipelineSettings` con `BEAM_*`

Delta estimado:

- `bajo`

### Infraestructura

- crear runtime `infra/beam-s1-image/`
- definir estrategia `Beam task_queue` o `Pod` para `ComfyUI`
- definir persistencia de pesos con `Volume`
- definir buckets montados para dataset/artifacts

Delta estimado:

- `medio`

### Tests

- clonar la familia de tests `test_runpod_*` hacia una variante `beam_*`
- conservar los tests contractuales comunes sin duplicacion innecesaria

Delta estimado:

- `medio`

### Docs y tooling

- actualizar onboarding con `Beam CLI`, `WSL` y secretos
- documentar un nuevo runtime deployable
- decidir si Beam entra como baseline del repo o como proveedor opcional

Delta estimado:

- `medio`

## Camino Recomendado de Adopcion

Orden sugerido:

1. piloto en `S1 image`
2. si el piloto cierra bien, extender a `S2 image`
3. decidir despues `LoRA training`
4. dejar `video` para el final

Justificacion:

- `S1 image` usa el runtime mas claro y ya tiene bundle separado
- es donde el problema actual de stock pega mas directamente
- permite validar `ComfyUI + Beam Volume + Beam task_queue + logs + shell`
- evita comprometer desde el dia uno los runtimes mas caros

## Riesgos Abiertos

- Beam no publica hoy tantos tiers intermedios de VRAM como Runpod
- el costo all-in de Beam puede quedar por encima de la intuicion inicial si se dejan contenedores calientes
- en Windows, la adopcion seria mas limpia si el equipo estandariza `WSL`
- sin benchmark real de un runtime `ComfyUI` en Beam, la conclusion sigue siendo de factibilidad, no de performance final

## Recomendacion Final

Recomendacion cerrada:

- `GO CON LIMITES`

Una linea:

- avanzar con un piloto `Beam` para `S1 image` como contingencia y posible reemplazo de inference, pero no decidir todavia una migracion total de `training` y `video` hasta validar costo all-in y comportamiento real del runtime `ComfyUI` en Beam.

## Fuentes

### Beam

- [Pricing and Billing](https://docs.beam.cloud/v2/resources/pricing-and-billing)
- [GPU Acceleration](https://docs.beam.cloud/v2/environment/gpu)
- [CLI Reference](https://docs.beam.cloud/v2/reference/cli)
- [Installation](https://docs.beam.cloud/v2/getting-started/installation)
- [Distributed Storage Volumes](https://docs.beam.cloud/v2/data/volume)
- [Configuration](https://docs.beam.cloud/v2/sandbox/configuration)
- [Custom Registries](https://docs.beam.cloud/v2/environment/custom-registries)
- [Creating a Web Endpoint](https://docs.beam.cloud/v2/endpoint/overview)
- [Running Async Tasks](https://docs.beam.cloud/v2/task-queue/running-tasks)
- [Querying Task Status](https://docs.beam.cloud/v2/task-queue/query-status)
- [Keeping Containers Warm](https://docs.beam.cloud/v2/endpoint/keep-warm)
- [Cold Start Performance](https://docs.beam.cloud/v2/topics/cold-start)
- [Timeouts and Retries](https://docs.beam.cloud/v2/topics/timeouts-and-retries)
- [Storing Secrets](https://docs.beam.cloud/v2/environment/secrets)

### Internas del repo

- [technical-base.md](technical-base.md)
- [visual-generation-engine.md](visual-generation-engine.md)
- [developer-tooling-onboarding.md](../03-process/developer-tooling-onboarding.md)

### Baseline Runpod usado en esta comparacion

- captura del editor de endpoint compartida por el usuario el `2026-04-02`
- [Network volumes - Runpod](https://docs.runpod.io/storage/network-volumes)
