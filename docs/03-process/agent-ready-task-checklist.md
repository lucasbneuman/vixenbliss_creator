# Agent-Ready Task Checklist

## Objetivo

Definir el minimo que debe traer una tarea para que un agente la pueda planificar o ejecutar sin reinterpretacion peligrosa.

## Inputs minimos

La tarea debe explicitar:

- `ID` y titulo
- objetivo concreto
- alcance y limites
- criterio de done verificable
- owner o responsable funcional
- dependencias explicitas si existen

## Contexto minimo

La tarea debe enlazar o nombrar, segun corresponda:

- documentos del repo relevantes
- modulo o superficie afectada
- contrato o interfaz que toca
- riesgos conocidos
- evidencia previa reutilizable

## Si la tarea usa tooling externo

Tambien debe indicar:

- proveedor o MCP involucrado
- si usa credenciales personales o compartidas
- entorno esperado
- output esperado de la integracion

## Checklist para plan

- existe objetivo verificable
- existe criterio de done
- no mezcla multiples objetivos no relacionados
- no requiere decisiones de arquitectura aun no resueltas
- tiene fuentes de verdad identificables

## Checklist para implementacion

- ya tiene `PLAN OK`
- la superficie de cambio es acotada
- las validaciones minimas son conocidas
- la documentacion impactada es identificable
- el handoff esperado esta claro si la tarea no cierra en un ciclo

## Evidencia extra esperada de un agente

Ademas de la evidencia normal de PR o tarea, un agente debe dejar:

- que documentos uso como fuente de verdad
- que supuestos tomo
- que validaciones corrio o no pudo correr
- que limites de tooling o credenciales encontro

## Senales de que la tarea no esta agent-ready

- falta criterio de done
- depende de accesos no documentados
- mezcla backend, infra, datos y proceso sin separacion
- requiere elegir stack o arquitectura nueva
- necesita contexto oral para entenderse
