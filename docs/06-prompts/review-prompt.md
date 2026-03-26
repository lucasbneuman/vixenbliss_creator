# Prompt Base - Review

Usar esta plantilla para pedir una revision de calidad:

```text
Hace una review de este cambio con foco en bugs, regresiones, riesgos y pruebas faltantes.

Tarea: <ID y titulo>
Cambio a revisar: <PR, diff o archivos>
Contexto: <contratos y docs relevantes>

Instrucciones:
- prioriza findings reales por severidad
- senala regresiones funcionales y riesgos operativos
- marca pruebas faltantes o insuficientes
- si no encontrás findings, decilo explicitamente junto con riesgos residuales
```
