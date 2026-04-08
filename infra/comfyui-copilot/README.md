# ComfyUI Copilot Service

Servicio HTTP orientado a recomendacion tecnica de workflows para `ComfyUI`.

## Objetivo

- operar como complemento de desarrollo
- usar `OPENAI_API_KEY` o `OPEN_AI_TOKEN` del entorno para resolver recomendaciones
- responder con `CopilotRecommendation` compatible con el contrato agentic del repo
- degradar a workflows aprobados del registry interno si OpenAI falla o devuelve algo invalido

## Endpoints

- `POST /recommend`
- `GET /healthcheck`

## Reglas

- no participa del runtime de render
- no reemplaza el workflow registry interno
- solo recomienda sobre workflows aprobados por stage

## Deploy actual

- wrapper activo: `providers/modal/`
- backend: `OpenAI API`
- secreto esperado en `Modal`: `vixenbliss-s1-llm-openai`
