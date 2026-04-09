# ADR-004: `S1 image` entrega dataset LoRA real con shot plan determinista

## Estado

Aprobada

## Contexto

El runtime de `S1 image` ya materializaba `dataset_manifest` y `dataset_package`, pero el handoff seguia pudiendo nacer de una sola `base_image` replicada en multiples rutas. Eso servia como contrato inicial de trazabilidad, pero no como dataset util para entrenar un `LoRA` consistente y realista.

El nuevo objetivo operativo exige un dataset de entrenamiento con cobertura real de:

- cuerpo completo
- rostro
- distintos angulos
- ropa y desnudo
- prompts por muestra
- semillas y metadata reutilizable para QA y retraining

## Decision

Se adopta este contrato para `S1 image`:

- el runtime expande el prompt tecnico del avatar a un `dataset shot plan` determinista
- el handoff por defecto genera `40` muestras reales
- la seleccion del workflow de `S1 image` puede venir de `ComfyUI Copilot`, pero solo si resuelve a una variante aprobada del registry interno
- el runtime de `Modal` debe consumir el template versionado indicado por `workflow_id` y `workflow_version` del job, no un unico workflow fijo embebido
- la composicion canonica es:
  - `20` clothed y `20` nude
  - `10` `close_up_face`, `10` `medium` y `20` `full_body`
  - `5` angulos con `8` muestras cada uno
- cada muestra debe registrar:
  - `sample_id`
  - `prompt`
  - `negative_prompt`
  - `caption`
  - `seed`
  - `wardrobe_state`
  - `framing`
  - `camera_angle`
  - `pose_family`
  - `realism_profile`
  - `source_strategy`
- el validador de dataset debe rechazar handoffs con:
  - metadata incompleta por muestra
  - cobertura insuficiente
  - composicion demasiado sesgada
  - paquetes dominados por payloads duplicados

## Consecuencias

Positivas:

- `S1 lora train` recibe un dataset realmente entrenable y no solo un placeholder documental
- mejora la trazabilidad para QA, retraining y auditoria de prompts
- el requisito de realismo deja de depender solo del prompt base y pasa a quedar fijado en el contrato del shot plan
- `Copilot` pasa de ser solo validador o metadata tecnica a selector gobernado de variantes aprobadas para `S1`

Costos:

- `S1 image` consume mas tiempo de GPU al renderizar multiples muestras reales
- el runtime y los tests quedan mas complejos
- la validacion del dataset se vuelve mas estricta y puede rechazar handoffs que antes pasaban
- el registry de workflows de `S1` debe mantenerse versionado y sincronizado con los templates realmente deployables

## Revision futura

Revisar esta ADR si cambia:

- la cantidad canonica de muestras por identidad
- la politica de cobertura para LoRA
- la familia de modelos base o la estrategia de captions por muestra
