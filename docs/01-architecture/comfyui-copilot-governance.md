# ComfyUI Copilot Governance

## Audiencia

- developers
- agentes que integran `ComfyUI Copilot`

## Vigencia

- `vivo`

## Objetivo

Definir como `ComfyUI Copilot` complementa la arquitectura de `ComfyUI` sin convertirse en dependencia hard del runtime productivo.

## Regla principal

- `ComfyUI Copilot` se usa como `dev assistant`
- no arma workflows dinamicamente dentro del runtime de render
- no bloquea `S1 image`, `S2 image` o `S2 video` si el servicio externo falla
- el runtime productivo solo consume workflows versionados y aprobados

## Uso permitido

- diseno y refactor de workflows
- debugging de grafos
- recomendacion de nodos, modelos y subgrafos
- comparacion entre variantes aprobadas por stage
- estandarizacion de plantillas para `S1 image`, `S2 image` y `S2 video`

## Workflow registry interno

La fuente de verdad tecnica para adopcion operativa no es Copilot sino un registry interno de workflows aprobados.

Cada entrada aprobada debe registrar como minimo:

- `stage`
- `workflow_id`
- `workflow_version`
- `workflow_family`
- `base_model_id`
- `required_nodes`
- `optional_nodes`
- `input_contract`
- `content_modes_supported`
- `risk_flags`
- `compatibility_notes`

Copilot solo puede recomendar sobre ese universo. Si sugiere nodos o modelos fuera del stack autorizado, la recomendacion no se adopta automaticamente.

## Politica de fallback

- si Copilot no responde, el grafo usa un workflow aprobado del registry
- ese fallback debe quedar trazable en el estado final del grafo
- la degradacion no debe marcar como fallido el flujo principal de identidad

## Stages canonicos

- `s1_identity_image`
- `s2_content_image`
- `s2_video`

## Scorecard minimo

La utilidad de Copilot debe medirse con un scorecard simple y comparable entre iteraciones:

- tiempo de diseno o refactor del workflow
- cantidad de iteraciones manuales hasta llegar a una variante aprobable
- cantidad de recomendaciones rechazadas por incompatibilidad
- cantidad de workflows rotos por nodos no compatibles
- reutilizacion efectiva entre `S1` y `S2`

## Restricciones

- no introducir nodos nuevos fuera del stack autorizado sin tarea asociada
- si la recomendacion cambia interfaces, contratos o direccion transversal, corresponde ADR
- `S1` y `S2` deben mantenerse en la familia `Flux` para preservar compatibilidad entre dataset, LoRA e inferencia
