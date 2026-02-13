# DOCS_POLICY.md - Doc Integrity Guard v1

Estado: activo
Ultima actualizacion: 2026-02-12
Scope: toda documentacion del repositorio (`docs/` + archivos de gobernanza)

## 1) Fuentes unicas activas (obligatorio)

- Arquitectura + mapeo de sistemas: `docs/SYSTEM_MAP.md`
- Contrato API v1: `docs/api-contracts/v1_endpoints.md`

Estas dos rutas son fuentes canonicas. No crear duplicados activos de estas materias.

## 2) Ubicacion obligatoria por tipo de documento

- External systems (providers externos, workers serverless, contratos externos): `docs/external-systems/`
- Governance / context / reglas operativas: `docs/context/`
- Planes grandes (roadmaps, exec plans, runbooks extensos): `.codex/plans/` o `docs/plans/`
- Legacy o reemplazado: `docs/_archive/` (con nota `ARCHIVED` y fecha)

## 3) Antiduplicacion explicita

Queda prohibido recrear como activos:
- `docs/ARCHITECTURE.md`
- `docs/API_DOCUMENTATION.md`

Si se detecta necesidad similar:
1. Redirigir a `docs/SYSTEM_MAP.md` (arquitectura)
2. Redirigir a `docs/api-contracts/v1_endpoints.md` (API)
3. Si falta contenido, complementar la fuente activa en lugar de crear archivo paralelo

## 4) Regla de indexado y descubribilidad

Todo documento nuevo debe quedar descubierto de una de estas formas:
- Link en `docs/DOCS_INDEX.md`, o
- Link desde el router correspondiente (`AGENTS.md`, `docs/context/README.md`, `docs/external-systems/README.md`)

Documento no indexado = documento incompleto.

## 5) Regla de archivado

Antes de reemplazar o eliminar un doc:
1. Copiar a `docs/_archive/<NOMBRE>.<YYYY-MM-DD>.md`
2. Prefijar con bloque `ARCHIVED` indicando fuente y motivo
3. Luego remover/reducir el archivo activo anterior

## 6) Control de cambios

Al cambiar estructura de docs:
- Actualizar `docs/TASK.md` (2 lineas)
- Verificar links de AGENTS/context/index
- Confirmar que no hubo cambios runtime no solicitados
