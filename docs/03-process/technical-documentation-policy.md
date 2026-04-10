# Technical Documentation Policy

## Audiencia

- developers
- agentes

## Vigencia

- `vivo`

## Objetivo

Definir como documentar tecnicamente el camino recorrido para que el repo no solo explique a donde quiere llegar el proyecto, sino tambien que se hizo, como quedo y que decisiones o aprendizajes lo explican.

## Principio central

- `YouTrack` gobierna backlog, prioridad, alcance vivo y estado
- el repo documenta proceso, arquitectura, contratos, decisiones, validacion y conocimiento tecnico durable
- la documentacion tecnica no compite con `YouTrack`; la complementa

## Que debe registrar la documentacion tecnica

- estado tecnico actual de la solucion
- contratos, interfaces o flujos relevantes
- decisiones estables y su razon
- aprendizajes que cambiaron el rumbo de implementacion
- limitaciones, riesgos o deuda visible cuando sea importante para continuar

## Cuando actualizarla

Actualizar documentacion tecnica en el mismo cambio cuando se modifique alguno de estos frentes:

- arquitectura o integraciones
- contratos, schemas o interfaces
- decisiones operativas estables
- estrategia de validacion o criterios de cierre
- comportamientos criticos que otros deban entender para seguir trabajando

## Donde registrar cada cosa

- `docs/01-architecture/`: como funciona o queda disenada la solucion
- `docs/03-process/`: como se trabaja, aprueba, valida y entrega
- `docs/04-decisions/`: decisiones estables que seria costoso reinterpretar
- `docs/05-qa/`: como se valida, que evidencia se exige y que condiciones bloquean cierre
- `docs/07-agents/`: contratos, prompts y checklists especificos para agentes
- `docs/08-developers/`: onboarding tecnico y baseline de tooling para developers
- `docs/99-archive/`: contexto historico que no gobierna decisiones actuales

## Lo que no hay que hacer

- duplicar el estado transaccional de tareas en archivos `.md`
- usar el roadmap como tablero rigido de ejecucion
- dejar cambios tecnicos importantes solo en commits o comentarios de PR sin reflejo documental durable
- registrar texto cosmetico sin aportar entendimiento tecnico real

## Regla de cierre

Un cambio tecnico no esta realmente cerrado si deja codigo nuevo o comportamiento nuevo sin el nivel de documentacion tecnica necesario para que otro developer o agente pueda continuar sin contexto oral.
