# Analisis de Portfolio Serverless GPU para VixenBliss

> Estado: `archivado`
> Fecha de archivo: `2026-04-10`
> Motivo: analisis comparativo historico de proveedores. Se conserva como contexto, no como fuente de verdad activa.
> Reemplazo vigente: `docs/01-architecture/technical-base.md` y la configuracion real de `infra/`.

## Objetivo

Rehacer la investigacion de proveedores `serverless GPU` para `VixenBliss Creator` con una mirada de portfolio y no de reemplazo unico.

El objetivo no es responder "cual es el mejor proveedor" en abstracto, sino definir:

- que proveedores encajan mejor con el runtime actual del repo
- cuando conviene operar con uno solo
- cuando conviene operar con dos proveedores complementarios
- que opciones sirven para pruebas baratas o con credito gratuito
- que opciones sirven como complemento futuro aunque no sean reemplazo del runtime visual actual

Fecha de corte de la evaluacion:

- `2026-04-02`

## Resumen ejecutivo

Recomendacion ejecutiva:

- `PORTFOLIO DUAL RECOMENDADO`
- `Tier 1 principal`: `Modal` o `Beam`
- `Tier 1 secundario / contingencia inmediata`: `Runpod`
- `Tier 2 complementario`: `Vast`
- `Tier 3 complementario futuro`: `Together` y `fal`
- `No recomendado por ahora para el runtime visual principal`: `Salad`
- `Sin evidencia suficiente`: `Meshive.ai`

Lectura corta:

- el repo actual sigue encajando mejor con `Runpod` por continuidad operativa y por la infraestructura ya construida en `infra/runpod-*`
- si el objetivo es reducir dependencia y mejorar portabilidad, hoy el mejor salto ordenado no es "migrar todo", sino agregar un proveedor principal mas limpio de plataforma: `Modal` o `Beam`
- `Modal` sale muy fuerte por DX, amplitud de hardware, colas, endpoints, custom images y credito gratuito mensual real
- `Beam` sigue saliendo muy fuerte por contenedores custom, task queues, volumes y simplicidad para runtimes GPU tipo `ComfyUI`, con menor variedad de VRAM pero muy buen encaje operativo
- `Runpod` sigue siendo excelente como baseline real para este repo y como contingencia inmediata, especialmente por `network volumes` y por la separacion `S1 image / S2 image / train / video` ya aterrizada
- `Vast` es muy atractivo como segundo proveedor por costo, amplitud de mercado y programa de `startup credits`, pero hay que asumir mas variabilidad y mas trabajo operativo
- `Together` y `fal` no son la mejor opcion para reemplazar ya mismo el runtime visual tipo `ComfyUI`, pero si son candidatos serios para servicios futuros mas especializados
- `Salad` hoy muestra demasiadas fricciones para el runtime visual principal del repo: nodos residenciales, persistencia externa obligatoria, variabilidad y limites mas duros para tareas largas

## Foto actual del repo

La comparacion no puede hacerse desde cero. El repo ya tiene una forma operativa bastante concreta:

- el motor visual expone un contrato estable en `src/vixenbliss_creator/visual_pipeline/`
- la integracion productiva aterrizada hoy esta orientada a `Runpod Serverless`
- hay bundles especificos en:
  - `infra/runpod-s1-image-serverless`
  - `infra/runpod-visual-serverless`
  - `infra/runpod-s1-model-loader`
- el runtime esperado usa:
  - `ComfyUI`
  - contenedores custom
  - polling asincrono
  - cache de modelos pesados
  - storage persistente para pesos
  - separacion por etapa operativa

Esto vuelve especialmente relevantes estos criterios:

1. contenedores custom reales
2. colas o jobs asincronos con polling
3. storage persistente o volumen montable
4. tiempos de startup y warm/cold start
5. logs y debugging del worker
6. costo real de mantener workers calientes
7. compatibilidad con runtimes pesados tipo `Flux + IPAdapter + FaceDetailer`

## Criterios de evaluacion

### Criterios tecnicos

- `Custom container fit`: que tan directo es correr un runtime propio tipo `ComfyUI`
- `Async fit`: colas, jobs, polling, retries
- `Storage fit`: volumenes, mounts, buckets o storage externo obligatorio
- `Hardware fit`: escalones de VRAM utiles para `S1`, `S2`, `LoRA`, `video`
- `Ops fit`: logs, shell, CLI, depuracion, deploy

### Criterios economicos

- precio real y modelo de billing
- si cobra solo GPU o `GPU + CPU + RAM`
- si cobra startup, idle o keep-warm
- disponibilidad de credito gratuito o programa startup

### Criterios estrategicos

- riesgo de lock-in
- riesgo de marketplace / hardware variable
- utilidad como proveedor secundario
- encaje para futuros servicios ademas del runtime visual principal

## Baseline actual: Runpod

`Runpod` no es solo una referencia historica: es el baseline real del repo.

Lo que ya juega a favor:

- `Runpod Serverless` ya esta integrado en docs, runtime bundles y variables
- pricing oficial clara por segundo con `Flex` y `Active` workers
- soporte de `network volumes` y `S3-compatible API`
- buena amplitud de VRAM util para `S1 image`, `S2 image`, `LoRA` y `video`

Hallazgos oficiales relevantes:

- `Serverless` cobra por segundo desde que el worker empieza hasta que se detiene por completo
- distingue `Flex workers` y `Active workers`
- ofrece `network volumes` persistentes montables en `/runpod-volume`
- precios oficiales serverless actuales incluyen `24 GB`, `48 GB`, `80 GB`, `141 GB` y `180 GB`

Fuentes:

- [Runpod Serverless pricing](https://docs.runpod.io/serverless/pricing)
- [Runpod network volumes](https://docs.runpod.io/serverless/storage/network-volumes)
- [Runpod S3-compatible API](https://docs.runpod.io/serverless/storage/s3-api)

Lectura para este repo:

- `Runpod` sigue siendo el mas corto camino para seguir operando sin redisenar `infra/`
- no resuelve por si solo el riesgo de dependencia
- sigue siendo muy buen candidato como proveedor secundario aunque se elija otro como principal estrategico

## Analisis por proveedor

### 1. Modal

#### Fortalezas

- muy buen modelo `serverless` para contenedores y funciones GPU
- soporte oficial de `custom images`, `web endpoints`, `job processing`, `queues`, `retries`, `timeouts`
- `Volumes` como filesystem distribuido pensado para pesos y distribucion de inferencia
- mucho mejor amplitud de hardware que `Beam` para elegir escalones de VRAM
- credito gratuito oficial de `30 USD/mes` en plan `Starter`
- programa startup oficial de hasta `25k USD`

#### Riesgos / limites

- `Volumes v2` sigue documentado como `beta` y no recomiendan usarlo para datos criticos
- las funciones GPU siguen sujetas a preemption; `nonpreemptible` no aplica a GPU
- el modelo mental es menos "infra container-first" que `Runpod`, aunque soporta muy bien ese uso

#### Hallazgos oficiales

- `Starter` incluye `30 USD/mes` de creditos gratis
- `Team` incluye `100 USD/mes` de creditos
- `startup credits` de hasta `25k USD`
- GPUs soportadas: `T4`, `L4`, `A10`, `L40S`, `A100 40/80`, `RTX PRO 6000`, `H100`, `H200`, `B200`
- las `Volumes` estan pensadas para `model weights`
- job queue oficial via `.spawn()` + polling con `FunctionCall.get()`

Fuentes:

- [Modal pricing](https://modal.com/pricing)
- [Modal GPU acceleration](https://modal.com/docs/guide/gpu)
- [Modal Volumes](https://modal.com/docs/guide/volumes)
- [Modal job processing](https://frontend.modal.com/docs/guide/job-queue)
- [Modal retries](https://modal.com/docs/guide/retries)
- [Modal timeouts](https://modal.com/docs/guide/timeouts)
- [Modal preemption](https://modal.com/docs/guide/preemption)

#### Lectura para VixenBliss

- es el candidato mas fuerte si queremos una plataforma principal mas limpia, mas portable y con mejor DX
- encaja muy bien para:
  - `S1 image`
  - `S2 image`
  - parte de `video`
  - servicios futuros de backend intensivos
- para `LoRA` y tareas largas hay que diseñar bien checkpoints y tolerancia a interrupciones

Clasificacion:

- `Tier 1`

### 2. Beam Cloud

#### Fortalezas

- modelo muy natural para runtimes GPU custom con `endpoints`, `task queues`, `volumes`, `shell`, `logs`
- buen soporte de `custom registries`
- `scale-to-zero` real
- no factura espera de maquina ni image pull
- `Beam Volumes` encajan muy bien con cache de pesos y datasets
- credito de alta utilidad para prueba inicial: `15 horas de free credit`

#### Riesgos / limites

- variedad de GPUs bastante mas acotada que `Modal` o `Runpod`
- la documentacion de instalacion en Windows va por `WSL`
- el costo all-in sigue incluyendo `GPU + CPU + RAM`, no solo GPU

#### Hallazgos oficiales

- `15 hours of free credit` al crear cuenta
- pricing oficial:
  - `RTX 4090` `0.69 USD/h`
  - `A10G` `1.05 USD/h`
  - `H100` `3.50 USD/h`
  - `CPU` `0.190/core/h`
  - `RAM` `0.020/GB/h`
- `Volumes` montados directamente al contenedor y recomendados para model weights
- `task_queue` oficial para async tasks
- `keep_warm_seconds` y defaults de warmup por tipo de deployment

Fuentes:

- [Beam introduction](https://docs.beam.cloud/v2/getting-started/introduction)
- [Beam pricing and billing](https://docs.beam.cloud/v2/resources/pricing-and-billing)
- [Beam volumes](https://docs.beam.cloud/v2/data/volume)
- [Beam task queues](https://docs.beam.cloud/v2/task-queue/running-tasks)
- [Beam keep warm](https://docs.beam.cloud/v2/endpoint/keep-warm)
- [Beam installation](https://docs.beam.cloud/v2/getting-started/installation)
- [Beam custom registries](https://docs.beam.cloud/v2/environment/custom-registries)

#### Lectura para VixenBliss

- sigue siendo un candidato excelente para un runtime hermano del actual
- es especialmente atractivo para:
  - `S1 image`
  - `S2 image`
  - pilotos de `ComfyUI` serverless con storage persistente
- es menos flexible que `Modal` en variedad de VRAM, pero mas directo en el modelo de contenedor GPU orientado a app

Clasificacion:

- `Tier 1`

### 3. Vast.ai

#### Fortalezas

- muy fuerte en costo y amplitud de mercado
- tiene `Serverless` oficial con `Endpoints`, `Workergroups`, logs y routing
- hay evidencia oficial de template `ComfyUI Image Generation`
- programa startup oficial de hasta `2,500 USD` en creditos
- sirve tanto para serverless como para instancias mas manuales

#### Riesgos / limites

- modelo operativo mas complejo que `Modal` o `Beam`
- al ser marketplace, la variabilidad operativa y de performance es parte del sistema
- el cliente debe convivir con conceptos propios del engine como `route`, `cost estimate`, `worker groups`

#### Hallazgos oficiales

- serverless oficial con `Endpoint` y `Workergroup`
- logs de endpoint y worker accesibles por UI y CLI
- startup program oficial con hasta `2,500 USD` en creditos
- marketplace de miles de GPUs y hosts independientes
- quickstart oficial requiere fondear creditos y operar endpoint group

Fuentes:

- [Vast serverless architecture](https://docs.vast.ai/documentation/serverless/architecture)
- [Vast serverless quickstart](https://docs.vast.ai/documentation/serverless/getting-started-with-serverless)
- [Vast route API](https://docs.vast.ai/serverless/route)
- [Vast logs](https://docs.vast.ai/documentation/serverless/logging)
- [Vast startup program](https://vast.ai/article/vast-ai-startup-program)
- [Vast marketplace overview](https://vast.ai/press-kit)

#### Lectura para VixenBliss

- no lo elegiria como primer proveedor principal si la prioridad es simplicidad operativa
- si lo elegiria como:
  - proveedor secundario barato
  - overflow / contingencia
  - opcion para entrenamientos o jobs de costo sensible
- es muy interesante para no depender solo de clouds cerradas y para aprovechar mercado amplio

Clasificacion:

- `Tier 2`

### 4. Together.ai

#### Fortalezas

- ya no es solo APIs cerradas: hoy tiene `Dedicated Containers`, `Queue API`, `Managed Storage`, `Sandbox` y `GPU Clusters`
- muy buen fit para servicios futuros con colas asincronas y contenedores dedicados
- pricing oficial transparente para `serverless inference`, `dedicated inference`, `storage` y `fine-tuning`

#### Riesgos / limites

- no ofrece free trial general hoy
- la self-service principal sigue muy orientada a inference managed
- `Dedicated Containers` requiere habilitacion comercial / acceso
- el abanico de hardware visible esta muy sesgado a GPUs grandes, no al tramo barato de `24 GB`

#### Hallazgos oficiales

- `Together` ya no ofrece free trial general; requiere compra minima de `5 USD`
- las promociones de signup credits se terminaron
- pricing oficial de `Dedicated Inference`:
  - `1x H100 80GB`: `3.99 USD/h`
  - `1x H200 141GB`: `5.49 USD/h`
  - `1x B200 180GB`: `9.95 USD/h`
- `Managed Storage` a `0.16 USD/GiB/mes`
- `Dedicated Containers` ofrece contenedores custom con autoscaling, job queues y observabilidad

Fuentes:

- [Together pricing](https://www.together.ai/pricing)
- [Together dedicated inference](https://docs.together.ai/docs/dedicated-inference)
- [Together dedicated containers](https://docs.together.ai/docs/dedicated-container-inference)
- [Together Queue API](https://docs.together.ai/docs/deployments-queue)
- [Together cluster storage](https://docs.together.ai/docs/cluster-storage)
- [Together support article: no free trial](https://support.together.ai/articles/1862638756-changes-to-free-tier-and-billing-july-2025)
- [Together support article: no signup credits](https://support.together.ai/articles/7378830629-how-many-free-credits-do-i-get-when-i-sign-up)

#### Lectura para VixenBliss

- no lo tomaria hoy como reemplazo directo del runtime visual principal
- si lo considero valioso para futuro si aparecen necesidades de:
  - inference dedicada de modelos propios
  - servicios de IA no visuales
  - colas largas sobre contenedores dedicados
- para `ComfyUI + Flux` hoy no es el camino mas corto

Clasificacion:

- `Tier 3` para el runtime visual actual
- `Tier 2` para servicios futuros no necesariamente atados a `ComfyUI`

### 5. fal.ai

#### Fortalezas

- plataforma muy fuerte para generative media
- diferencia clara entre `Model APIs`, `Serverless` y `Compute`
- soporta deploy de apps propias en `Serverless`
- permite migrar server Docker o contenedor propio
- tiene pricing clara por lifecycle del runner en `Serverless`

#### Riesgos / limites

- `Serverless` custom aparece documentado como feature con acceso habilitado por cuenta / enterprise
- su posicionamiento principal sigue siendo fuerte en `model APIs` mas que como cloud generalista para runtime propio
- usa modelo prepago por creditos para APIs

#### Hallazgos oficiales

- `fal Serverless` deploya apps propias sobre GPUs on-demand con autoscaling desde cero
- soporta migrar `Docker server` y `custom container`
- `Serverless` factura por tiempo de runner en estados `SETUP`, `IDLE`, `RUNNING`, `DRAINING`, `TERMINATING`
- pricing publica de compute custom "starting at":
  - `A100 40GB`: `0.99 USD/h`
  - `H100 80GB`: `1.89 USD/h`
  - `H200 141GB`: `2.10 USD/h`
- `Model APIs` usan prepago y cobran por output o por GPU-second segun endpoint

Fuentes:

- [fal pricing](https://fal.ai/pricing)
- [fal serverless introduction](https://docs.fal.ai/serverless/introduction)
- [fal serverless pricing](https://docs.fal.ai/documentation/serverless/pricing)
- [fal model APIs pricing](https://fal.ai/docs/documentation/model-apis/pricing)
- [fal concurrency limits](https://fal.ai/docs/documentation/model-apis/concurrency-limits)
- [fal quick start](https://fal.ai/docs/documentation/quickstart)

#### Lectura para VixenBliss

- hoy lo veo mejor como proveedor complementario para:
  - APIs de generacion ya optimizadas
  - servicios especificos de imagen o video
  - futuros productos donde convenga comprar media generation como servicio
- no lo tomaria como primera eleccion para portar el runtime `ComfyUI` del repo

Clasificacion:

- `Tier 3`

### 6. Salad Cloud

#### Fortalezas

- costo potencialmente muy bajo
- soporta contenedores Linux sobre red distribuida de GPUs de consumidor
- free trial documentado para `SaladCloud`
- `SCE Secure` aparece como oferta enterprise mas robusta

#### Riesgos / limites

- `persistent storage` no esta soportado en `SCE` community
- los nodos se ejecutan sobre hardware de usuarios con `Windows + WSL2`
- hay variabilidad esperable de performance
- los jobs largos exigen queue externa y checkpoints
- las colas propias tienen limites duros y las interrupciones cuentan como fallos

#### Hallazgos oficiales

- `SCE` trata los contenedores como `stateless workloads`
- no soporta `persistent storage`; recomiendan usar storage externo tipo `S3`
- no autoescala por performance en container groups clasicos; el escalado se hace bajo demanda o via `Job Queue`
- `Job Queues` reintentan hasta 3 veces y no son buena opcion para tareas extremadamente largas
- la propia documentacion recomienda `queue + checkpoint + cloud storage` para tareas largas como `LoRA training` y `LLM finetuning`
- quickstart oficial menciona `free trial`
- `SCE Secure` promete entorno mas enterprise y H100 por menos de `1 USD/h`, pero es oferta de ventas, no self-serve publica cerrada

Fuentes:

- [Salad SCE introduction](https://docs.salad.com/products/sce/introduction)
- [Salad quickstart API](https://docs.salad.com/products/sce/getting-started/quickstart-api)
- [Salad job queues](https://docs.salad.com/container-engine/explanation/job-processing/job-queues)
- [Salad queue autoscaling](https://docs.salad.com/products/sce/autoscaling/enable-autoscaling)
- [Salad long-running tasks with SQS](https://docs.salad.com/container-engine/how-to-guides/job-processing/sqs)
- [Salad Kelpie](https://docs.salad.com/guides/long-running-tasks/kelpie)
- [Salad SCE Secure](https://salad.com/salad-container-engine-secure)
- [Salad pricing/get started](https://salad.com/get-started)

#### Lectura para VixenBliss

- como proveedor principal para el runtime visual actual, hoy queda demasiado condicionado por:
  - falta de persistencia nativa
  - hardware heterogeneo
  - operacion sobre `WSL2`
  - mas complejidad para tareas largas y reanudables
- puede ser util para workloads mas batch, tolerantes a interrupcion y fuertemente costo-sensibles

Clasificacion:

- `No recomendado por ahora` para el runtime visual principal
- `Tier 3` solo para casos batch muy tolerantes a variabilidad

### 7. Meshive.ai

#### Hallazgo

Se pudo resolver el dominio `https://meshive.ai/`, que expone el titulo:

- `Meshive - High-Performance GPU Computing On-Demand`

Pero no aparecieron:

- documentacion oficial indexable
- pricing oficial verificable
- docs de colas, storage o hardware
- articulos oficiales suficientes para evaluar el servicio con el mismo rigor que el resto

Fuentes:

- [meshive.ai](https://meshive.ai/)

#### Lectura para VixenBliss

- hoy no hay evidencia oficial suficiente para recomendarlo o compararlo seriamente
- no debe inferirse que es equivalente a `Meshy AI`, porque seria otro proveedor distinto

Clasificacion:

- `Sin evidencia suficiente para evaluacion`

## Matriz resumida

| Proveedor | Contenedores custom | Async / colas | Storage persistente | Credito gratis | Fit actual con runtime visual | Riesgo principal |
| --- | --- | --- | --- | --- | --- | --- |
| Runpod | Muy bueno | Muy bueno | Muy bueno | No relevante / no identificado como signup credit general | Muy alto | dependencia actual |
| Modal | Muy bueno | Muy bueno | Bueno, con `Volumes v2 beta` | Muy bueno | Alto | preemption GPU / volumen beta |
| Beam | Muy bueno | Muy bueno | Muy bueno | Muy bueno | Alto | menos VRAM / WSL en Windows |
| Vast | Bueno | Bueno | Depende del enfoque | Bueno via startup program | Medio-alto | marketplace y complejidad |
| Together | Bueno en `Dedicated Containers` | Muy bueno | Bueno | No | Medio | acceso comercial y foco en inference |
| fal | Bueno, pero mas gated | Bueno | No es su fortaleza central para este caso | No general confirmado | Medio-bajo | foco principal en APIs y acceso |
| Salad | Bueno en contenedor, debil en persistencia | Medio | Debil | Trial general documentado | Bajo | variabilidad y falta de persistencia |
| Meshive.ai | No verificable | No verificable | No verificable | No verificable | No evaluable | falta de evidencia |

## Recomendacion de estrategia

### Opcion A - principal + contingencia

Recomendada si queremos bajar dependencia sin rehacer todo a la vez.

- `Principal`: `Modal`
- `Secundario / contingencia`: `Runpod`

Por que:

- `Modal` ofrece mejor portfolio general para crecer a mas servicios
- `Runpod` conserva continuidad inmediata sobre lo que ya existe
- la migracion podria hacerse por runtime, no por big bang

### Opcion B - principal infra limpia + alternativo de misma familia

Recomendada si queremos dos proveedores mas "cloud platform" y menos marketplace.

- `Principal`: `Modal`
- `Secundario`: `Beam`

Por que:

- ambos tienen buen fit para contenedores custom, queues y storage
- ambos tienen creditos oficiales claros para pruebas
- reducen mucho la dependencia de `Runpod`

Riesgo:

- pierde continuidad directa con la `infra/runpod-*` ya armada

### Opcion C - principal portable + secundario barato

Recomendada si la prioridad es resiliencia + costo.

- `Principal`: `Beam` o `Modal`
- `Secundario`: `Vast`

Por que:

- el principal queda como plataforma estable y portable
- `Vast` queda para overflow, contingencia o cargas sensibles a costo

Riesgo:

- mayor complejidad operativa que la opcion con `Runpod`

## Recomendacion final

Recomendacion final para el estado actual del repo:

1. Mantener `Runpod` como baseline operativo inmediato.
2. Abrir piloto tecnico con `Modal` como principal candidato de diversificacion.
3. Mantener `Beam` como segundo candidato fuerte si `Modal` no convence en storage, cold start o ergonomia del runtime.
4. Evaluar `Vast` como proveedor secundario de costo / overflow, no como primer paso.
5. No usar `Salad` como runtime visual principal en esta etapa.
6. No incorporar `Meshive.ai` hasta tener evidencia oficial verificable.

Lectura ejecutiva:

- si hoy hubiera que elegir solo un proveedor nuevo para sumar, elegiria `Modal`
- si hoy hubiera que elegir dos proveedores para estrategia real, elegiria:
  - `Modal + Runpod`
- si el criterio fuera "dos proveedores con mas portabilidad y menos dependencia del baseline actual", elegiria:
  - `Modal + Beam`

## Piloto tecnico recomendado

### Piloto 1 - Modal

Objetivo:

- replicar `S1 image` en un runtime hermano minimo

Validacion minima:

- contenedor custom con `ComfyUI`
- carga de pesos `Flux`
- almacenamiento de modelos en `Volume`
- endpoint asincrono o job queue
- evidencia de cold start, tiempo de setup y costo de una corrida real

### Piloto 2 - Beam

Objetivo:

- mismo bundle de `S1 image` con `task_queue` y `Beam Volumes`

Validacion minima:

- deploy reproducible
- tiempos de arranque
- costo all-in real con `GPU + CPU + RAM`
- facilidad de debugging respecto al runtime actual

### Criterios de salida del piloto

- si `Modal` o `Beam` igualan el runtime actual con delta tecnico razonable, pasan a ser candidato principal
- si ninguno iguala continuidad/costo/ops, `Runpod` se mantiene como principal y se documenta un secundario para contingencia
- `Vast` solo deberia entrar a piloto despues de eso

## Decision sintetica

- `Tier 1`: `Modal`, `Beam`
- `Tier 2`: `Runpod`, `Vast`
- `Tier 3`: `Together`, `fal`
- `No recomendado por ahora`: `Salad`
- `Sin evidencia suficiente`: `Meshive.ai`

## Conclusion

La conclusion no es que haya que abandonar `Runpod` hoy. La conclusion es que ya hay suficiente evidencia para dejar de pensar la capa GPU como proveedor unico.

La estrategia mas sana para `VixenBliss` hoy es:

- operar `Runpod` como baseline existente
- validar `Modal` o `Beam` como plataforma principal de diversificacion
- reservar `Vast` como opcion de costo / contingencia
- tratar `Together` y `fal` como complementos de portfolio para servicios futuros mas que como reemplazo directo del runtime visual actual

Eso reduce riesgo de dependencia, mejora poder de negociacion, y deja al sistema mejor preparado para crecer a mas runtimes y servicios sin redisenar todo alrededor de un solo proveedor.
