# Cerebro Agentico

## Objetivo

Definir el modulo que traduce una idea en lenguaje natural hacia una salida tecnica estructurada y validada, lista para ser consumida por las tareas de generador estructurado y persistencia.

## Entradas y salidas

- Entrada principal: una idea libre del usuario.
- Salida principal: `GraphState` final.
- Payload estructurado de salida: `TechnicalSheet` compatible con [`src/vixenbliss_creator/contracts/identity.py`](C:\Users\AVALITH\Desktop\Proyectos\vixenbliss_creator\src\vixenbliss_creator\contracts\identity.py).

## Flujo del grafo

1. `Expansion`
   Usa un `LLM serverless` para producir un `TechnicalSheet` inicial y el contexto narrativo de expansion.
2. `CopilotConsultor`
   Consulta un adapter HTTP de `ComfyUI Copilot` y obtiene una recomendacion de workflow consumible.
3. `Validator`
   Verifica completitud, estabilidad del payload, limites operacionales y compatibilidad basica entre `TechnicalSheet` y recomendacion tecnica.
4. `CritiqueRouter`
   Reinyecta feedback estructurado al nodo `Expansion` o corta fail-fast cuando se agotan intentos o aparece un error no recuperable.
5. `Finalize`
   Produce el `GraphState` final con estado terminal claro.

## Modulos

- `src/vixenbliss_creator/agentic/models.py`
  Modelos Pydantic para `GraphState`, expansion, recomendacion y validacion.
- `src/vixenbliss_creator/agentic/ports.py`
  Puertos reemplazables para LLM, Copilot y validator.
- `src/vixenbliss_creator/agentic/adapters.py`
  Adapters HTTP reales y fakes deterministas para test.
- `src/vixenbliss_creator/agentic/graph.py`
  Wiring de `LangGraph`.
- `src/vixenbliss_creator/agentic/runner.py`
  Runner demo reproducible para evidencia minima.

## Variables de entorno

- `LLM_SERVERLESS_BASE_URL`
- `LLM_SERVERLESS_API_KEY`
- `LLM_SERVERLESS_MODEL`
- `COMFYUI_COPILOT_BASE_URL`
- `COMFYUI_COPILOT_API_KEY`
- `COMFYUI_COPILOT_PATH`
- `AGENTIC_BRAIN_MAX_ATTEMPTS`
- `AGENTIC_BRAIN_SOURCE_ISSUE_ID`
- `AGENTIC_BRAIN_SOURCE_EPIC_ID`
- `AGENTIC_BRAIN_CONTRACT_OWNER`

## Smoke local

```powershell
python -m vixenbliss_creator.agentic.runner --idea "performer glam nocturna con tono seguro y premium"
```

El runner usa fakes deterministas para demostrar el flujo completo sin depender de credenciales ni red.
