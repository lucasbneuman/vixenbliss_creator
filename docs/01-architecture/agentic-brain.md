# Cerebro Agentico

## Objetivo

Definir el modulo que transforma una instruccion conversacional del operador en un `GraphState` final, con:

- intencion detectada
- modo de creacion
- constraints manuales y normalizados
- perfil de identidad estructurado y trazable
- `TechnicalSheet` final compatible con `Sistema 1`
- recomendacion tecnica de `ComfyUI Copilot`
- validacion fail-fast y critique loop

## Flujo del grafo

1. `detect_operator_intent`
   Deriva la accion pedida y el nivel de especificidad del input.
2. `detect_creation_mode`
   Clasifica `manual`, `semi_automatic`, `automatic` o `hybrid_by_attribute`.
3. `extract_personality_constraints`
   Extrae atributos explicitamente fijados por el operador.
4. `normalize_constraints`
   Canonicaliza vertical, category, style, arquetipo y defaults operativos.
5. `complete_identity_profile`
   Usa `LLM serverless` para completar solo los campos faltantes y devolver un `IdentityDraft` trazable.
6. `validate_profile_coherence`
   Bloquea incoherencias entre vertical, personalidad, estilo, narrativa y comportamiento social.
7. `generate_technical_sheet`
   Conserva la traduccion del draft hacia `TechnicalSheet` dentro del contexto expandido.
8. `request_copilot_recommendation`
   Consulta `ComfyUI Copilot` con la ficha tecnica ya enriquecida.
9. `validate_final_payload`
   Verifica completitud, trazabilidad, estabilidad del payload, limites operacionales y compatibilidad con Copilot.
10. `critique_and_retry`
   Reinyecta issues estructurados al nodo correcto segun dominio y target.
11. `finalize_graph_state`
   Produce el estado terminal final.

## Modelos principales

- `GraphState`
  Estado del grafo con intent, modo, constraints, draft, validacion, critique history y payload final.
- `IdentityConstraints`
  Restricciones detectadas o normalizadas desde el input conversacional.
- `IdentityDraft`
  Perfil estructurado de identidad con metadata, personalidad, comportamiento social, narrativa minima y `field_traces`.
- `ExpansionResult`
  Resultado del LLM con draft, completion report y `TechnicalSheet`.
- `ValidationOutcome`
  Reporte final de validacion consumible por el critique loop.

## Responsabilidades por componente

- `agentic/models.py`
  Tipos del grafo y reportes de trazabilidad.
- `agentic/graph.py`
  Wiring de `LangGraph` y routing de retries por dominio.
- `agentic/validator.py`
  Reglas fail-fast de identidad, negocio y payload tecnico.
- `agentic/adapters.py`
  Adapters HTTP reales y fakes deterministas.
- `agentic/runner.py`
  Runner reproducible para evidencia minima con casos de `Sistema 1`.

## Invariantes claves

- un `GraphState` exitoso debe tener `identity_draft`, `final_technical_sheet_payload`, `validation_result.valid == true` y `missing_fields == []`
- un campo manual no puede perder su traza manual
- `TechnicalSheet.identity_metadata` debe conservar `vertical`, `category`, `style` y `occupation_or_content_basis`
- `ComfyUI Copilot` sigue resolviendo recomendacion tecnica, no construccion de personalidad

## Smoke local

```powershell
.venv\Scripts\python.exe -m vixenbliss_creator.agentic.runner --idea "Quiero alguien sarcástica y casual, el resto automático"
```

El runner usa fakes deterministas y deja un flujo completo reproducible sin depender de credenciales ni red.
