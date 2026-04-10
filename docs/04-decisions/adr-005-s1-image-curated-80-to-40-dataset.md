# ADR-005: `S1 image` genera 80 renders y entrega 40 muestras curadas para LoRA

## Estado

Aprobada

## Contexto

`ADR-004` fijo el salto desde placeholder documental a dataset LoRA real con `40` muestras renderizadas. Esa mejora resolvio trazabilidad y cobertura base, pero no alcanzo para el objetivo operativo actual:

- mas detalle e hiperrealismo
- mas cobertura efectiva de cuerpo completo
- mas diversidad util para entrenamiento
- menor riesgo de duplicados o subset sesgado

El problema ya no era solo "tener 40 muestras", sino producir suficientes candidatas para curar un subset final entrenable.

## Decision

Se cambia el contrato operativo de `S1 image` a un flujo curado:

- el runtime genera `80` renders reales por identidad
- el handoff oficial a `S1 lora train` sigue siendo de `40` muestras
- el subset final se selecciona mediante una politica determinista `score_curated_v1`
- el manifest final debe distinguir:
  - `render_sample_count`
  - `selected_sample_count`
  - `render_files`
  - `files` como subset final de training
  - `selection_policy`
  - `selection_reasons`
  - `rejected_sample_ids`
  - `coverage_summary`
- la cobertura objetivo del render set prioriza:
  - `48` full body
  - `20` medium
  - `12` close up face
  - balance `40/40` clothed-nude
  - presencia obligatoria de los `5` angulos canonicos
- el subset curado de `40` debe mantener:
  - balance `20/20` clothed-nude
  - minimo fuerte de `full_body`
  - presencia de todos los angulos
  - rechazo de duplicados dominantes
- `ComfyUI Copilot` sigue acotado al registry aprobado y el workflow canonico de dataset pasa a ser `lora-dataset-ipadapter-batch`, salvo override explicito aprobado

## Consecuencias

Positivas:

- mejora la probabilidad de obtener un LoRA mas robusto con el mismo handoff final
- el sistema separa generacion bruta de curacion de training
- QA y debugging quedan mejor trazados con staging del render set completo
- la validacion deja de aceptar subsets estructuralmente correctos pero pobres para entrenamiento

Costos:

- mas tiempo y costo de GPU en `S1 image`
- mas complejidad en runtime, manifest y validator
- mayor superficie de tests y mantenimiento del shot planner

## Revision futura

Revisar esta ADR si cambia:

- la politica de curacion
- el tamano del render set o del training subset
- el workflow canonico aprobado para dataset
- el criterio minimo de cobertura para LoRA
