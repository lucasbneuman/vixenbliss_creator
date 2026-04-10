# Guía de Implementación del Cerebro Agéntico de Sistema 1

## Audiencia

- developers
- agentes que extienden `Sistema 1`

## Vigencia

- `vivo`

## Objetivo

Explicar a developers cómo funciona la implementación actual del cerebro agéntico de `Sistema 1`, qué responsabilidad tiene cada nodo, qué contratos consume y produce, y cómo depurar o extender el flujo sin romper trazabilidad ni validación fail-fast.

## Resumen ejecutivo

La implementación actual ya no resuelve solo:

- `idea libre -> technical sheet -> Copilot -> validator`

Ahora resuelve:

- `intención conversacional -> detección de modo -> extracción de constraints -> normalización -> construcción de identidad estructurada -> validación de coherencia -> technical sheet -> recomendación técnica -> validación final -> GraphState final`

La motivación del cambio fue representar mejor el caso real de `Sistema 1`: creación de identidades digitales con personalidad estructurada, soporte para inputs parciales/manuales y trazabilidad entre lo que definió el operador y lo que completó el sistema.

## Archivos principales

- `src/vixenbliss_creator/contracts/identity.py`
  Contrato canónico de identidad y `TechnicalSheet`.
- `src/vixenbliss_creator/agentic/models.py`
  Tipos del grafo, draft de identidad, constraints, reportes y crítica.
- `src/vixenbliss_creator/agentic/graph.py`
  Wiring de `LangGraph` y routing del critique loop.
- `src/vixenbliss_creator/agentic/validator.py`
  Reglas fail-fast de identidad, negocio y compatibilidad técnica.
- `src/vixenbliss_creator/agentic/adapters.py`
  Adapters HTTP reales y fakes.
- `src/vixenbliss_creator/agentic/runner.py`
  Runner reproducible para evidencia mínima.
- `tests/test_agentic_brain.py`
  Cobertura del flujo principal de `Sistema 1`.

## Contrato de datos

### 1. `TechnicalSheet`

Se amplió para incluir:

- `identity_metadata`
  - `avatar_id`
  - `category`
  - `vertical`
  - `style`
  - `occupation_or_content_basis`
- `personality_profile`
  - `archetype`
  - `axes`
  - `communication_style`
  - `social_behavior`
- `narrative_profile.minimal_viable_profile`
- `traceability.field_traces`

Estos campos son importantes porque en esta versión `category`, `vertical`, `style` y `occupation_or_content_basis` ya no son metadata decorativa: condicionan el resultado de personalidad y la ficha final.

### 2. `IdentityDraft`

Es el modelo intermedio más importante del grafo. Representa la identidad estructurada antes de finalizar el payload técnico.

Contiene:

- `metadata`
- `name`
- `archetype`
- `personality_axes`
- `communication_style`
- `social_behavior`
- `narrative_minimal`
- `field_traces`

### 3. `FieldTrace`

Registra procedencia por campo:

- `manual`
- `inferred`
- `defaulted`
- `derived`

La decisión de diseño fue no envolver cada valor en un objeto complejo. El valor se mantiene limpio y la trazabilidad vive en paralelo, lo que hace el contrato más consumible para persistencia futura.

## Flujo del grafo

### 1. `detect_operator_intent`

Responsabilidad:

- detectar si el operador está pidiendo crear un avatar
- identificar pistas de atributos mencionados
- estimar nivel de especificidad

Produce:

- `operator_intent`

No llama servicios externos. Es un nodo de clasificación liviana.

### 2. `detect_creation_mode`

Responsabilidad:

- clasificar el pedido en:
  - `manual`
  - `semi_automatic`
  - `automatic`
  - `hybrid_by_attribute`

Reglas actuales:

- sin atributos claros -> `automatic`
- presencia de “el resto automático” -> `semi_automatic`
- selección parcial de atributos -> `hybrid_by_attribute`
- alta especificidad general -> `manual`

Produce:

- `creation_mode`

### 3. `extract_personality_constraints`

Responsabilidad:

- extraer constraints explícitos desde la frase del operador
- mapearlos a paths estructurados

Ejemplos:

- `lifestyle` -> `metadata.vertical`
- `casual` -> `communication_style.speech_style`
- `dominant queen` -> `archetype`
- `sarcástica` -> `personality_axes.sarcasm`

Produce:

- `explicit_constraints`
- `manually_defined_fields`

### 4. `normalize_constraints`

Responsabilidad:

- canonicalizar constraints explícitos
- aplicar defaults de taxonomía semi-cerrada

Ejemplos de normalización:

- vertical no informada -> `adult_entertainment`
- style no informado pero `lifestyle` -> `premium`
- arquetipo no informado y `lifestyle` -> `luxury_muse`

Produce:

- `normalized_constraints`
- `inferred_fields`

### 5. `complete_identity_profile`

Responsabilidad:

- invocar el `LLMClient`
- completar solo los campos faltantes
- devolver `IdentityDraft` completo y `TechnicalSheet` alineado

Produce dentro de `ExpansionResult`:

- `normalized_constraints`
- `identity_draft`
- `completion_report`
- `technical_sheet_payload`

Este nodo es el corazón creativo del sistema, pero está obligado por contrato a devolver JSON válido, con shape tipado y trazabilidad por campo.

### 6. `validate_profile_coherence`

Responsabilidad:

- bloquear incoherencias internas de la identidad antes de pasar a validación técnica final

Ejemplos de chequeos actuales:

- `lifestyle` + `dominant_queen` por default -> conflicto
- `lifestyle` + sarcasm extremo -> conflicto
- baja calidez + relación hiper cercana con fans -> conflicto
- premium + casual + sarcasm extremo -> conflicto

Produce:

- `coherence_report`

### 7. `generate_technical_sheet`

Responsabilidad:

- mantener explícita la fase de traducción al payload técnico final

Hoy este nodo no recompone el payload porque el `ExpansionResult` ya lo trae armado desde el LLM, pero existe para preservar la separación conceptual entre:

- construcción de identidad
- traducción a ficha técnica

Eso deja el grafo listo para una futura refactorización donde la traducción se haga localmente o en otro servicio.

### 8. `request_copilot_recommendation`

Responsabilidad:

- consultar `ComfyUI Copilot`
- obtener workflow técnico consumible

`Copilot` no resuelve personalidad. Solo elige configuración técnica a partir de una identidad ya estructurada.

Produce:

- `copilot_recommendation`

### 9. `validate_final_payload`

Responsabilidad:

- validar estado final completo del grafo

Chequea:

- existencia de `expanded_context`
- existencia de `identity_draft`
- existencia de `copilot_recommendation`
- hard limits y escalation triggers
- compatibilidad de content modes con Copilot
- consistencia entre `IdentityDraft` y `TechnicalSheet`
- trazabilidad manual preservada
- estabilidad serializable del payload
- compatibilidad mínima de negocio entre vertical y personalidad

Produce:

- `validation_result`

### 10. `critique_and_retry`

Responsabilidad:

- consolidar issues de coherencia y validación final
- decidir si reintenta o falla en terminal

Si el error es retryable, enruta al nodo correcto según `target_node`:

- `detect_operator_intent`
- `normalize_constraints`
- `complete_identity_profile`
- `generate_technical_sheet`
- `request_copilot_recommendation`

Si se agotaron intentos o hay un issue `retryable=False`, falla fast.

### 11. `finalize_graph_state`

Responsabilidad:

- emitir el estado terminal

Condición de éxito:

- `identity_draft` presente
- `missing_fields == []`
- `validation_result.valid == True`
- `final_technical_sheet_payload` presente

## Cómo funciona el critique loop

Antes, cualquier error devolvía al inicio conceptual del flujo.

Ahora, el loop es más fino:

- errores semánticos o de defaults -> `normalize_constraints`
- errores de completado de identidad -> `complete_identity_profile`
- errores de recomendación técnica -> `request_copilot_recommendation`

Esto reduce re-trabajo innecesario y deja la depuración mucho más clara.

## Compatibilidad hacia atrás

El contrato nuevo introdujo campos adicionales en `TechnicalSheet`, pero se agregó una capa de migración para payloads legacy.

Eso permite que:

- tests previos del contrato sigan pasando
- fixtures viejos se normalicen al shape actual
- la transición sea evolutiva y no disruptiva

La migración legacy completa automáticamente:

- `identity_metadata`
- `personality_profile.archetype`
- `communication_style`
- `social_behavior`
- `minimal_viable_profile`
- mapeo de axes viejos a axes nuevos

## Casos cubiertos por tests

La suite de `tests/test_agentic_brain.py` cubre al menos:

- runner feliz con `GraphState` exitoso
- rechazo por falta de hard limits
- retry y recuperación luego de crítica
- falla terminal al agotarse retries
- límite de `critique_history`
- parsing de adapters HTTP
- modo automático por vertical
- preservación de trazabilidad manual vs inferred
- caso de arquetipo manual con autocompletado del resto
- caso category/style manuales con narrativa generada
- bloqueo de combinaciones inválidas vertical/personality

## Cómo depurar

### Si falla el grafo

Revisar en este orden:

1. `completion_status`
2. `terminal_error_message`
3. `coherence_report`
4. `validation_result`
5. `critique_history`
6. `identity_draft.field_traces`

### Si la personalidad no coincide con lo pedido

Revisar:

- `explicit_constraints`
- `normalized_constraints`
- `manually_defined_fields`
- `inferred_fields`
- `identity_draft.field_traces`

### Si Copilot sugiere algo incompatible

Revisar:

- `operational_limits.allowed_content_modes`
- `copilot_recommendation.content_modes_supported`
- `copilot_recommendation.node_ids`

## Cómo extender esta implementación

Si se quiere sumar más inteligencia, las extensiones más seguras son:

### Nuevos catálogos

Agregar:

- nuevos `ArchetypeCode`
- nuevas `CreationCategory`
- nuevos `IdentityStyle`

Impacto esperado:

- `contracts/identity.py`
- defaults en `graph.py`
- tests de coherencia

### Nuevas reglas de negocio

Agregar reglas en:

- `validate_profile_coherence`
- `TechnicalSheetGraphValidator.validate`

Recomendación:

- mantener las reglas explícitas y legibles
- no esconder reglas centrales solo en prompts

### Nueva traducción técnica

Si en el futuro la ficha técnica se arma fuera del LLM:

- mantener `IdentityDraft` como contrato intermedio
- reemplazar la lógica de `generate_technical_sheet`
- dejar `complete_identity_profile` concentrado solo en identidad

## Smoke local

```powershell
.venv\Scripts\python.exe -m vixenbliss_creator.agentic.runner --idea "Quiero alguien sarcástica y casual, el resto automático"
```

## Validación

La implementación fue validada con:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

Resultado al cerrar la tarea:

- `70 passed`

## Recomendación para developers

Si tocás este módulo:

- no rompas `IdentityDraft` como contrato intermedio
- no muevas lógica de coherencia fuerte a prompts libres
- no elimines la trazabilidad por campo
- mantené `Copilot` como capa técnica, no semántica
- actualizá tests y docs en el mismo cambio si cambiás shape o invariantes
