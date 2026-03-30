# Prompt Base - Plan

Usar esta plantilla para pedir a Codex el plan de una tarea:

```text
Quiero que trabajes esta tarea en modo plan.

Tarea: <ID y titulo>
Objetivo: <resultado esperado>
Contexto: <documentos o modulos relevantes>
Restricciones: <limites tecnicos u operativos>
Criterio de done: <como sabremos que esta lista>

Instrucciones:
- explora primero el repo y la documentacion relevante
- propone un plan decision-complete
- si la tarea es demasiado grande, dividila
- identifica riesgos, dependencias y validaciones
- no implementes nada hasta recibir `IMPLEMENTAR PLAN` o `PLAN OK`
```
