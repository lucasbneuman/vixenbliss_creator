# VixenBliss Creator

Base operativa y tecnica para `VixenBliss Creator`, enfocada en documentacion viva, contratos reutilizables y una implementacion Python alineada al estado real de `src/` e `infra/`.

## Audiencia

- developers
- agentes

## Vigencia

- `vivo`

## Que contiene este repositorio

- proceso compartido para trabajar con `YouTrack`, `GitHub` y `develop`
- arquitectura tecnica vigente del codigo actual
- contratos de identidad, trazabilidad y pipeline visual
- onboarding tecnico para developers
- contratos, prompts y checklists para agentes
- plantillas de entorno, `MCPs` y skills compartidas

## Mapa rapido

```text
.
|-- AGENTS.md
|-- README.md
|-- docs/
|   |-- 00-product/
|   |-- 01-architecture/
|   |-- 02-roadmap/
|   |-- 03-process/
|   |-- 04-decisions/
|   |-- 05-qa/
|   |-- 07-agents/
|   |-- 08-developers/
|   `-- 99-archive/
|-- src/
|-- infra/
|-- tests/
`-- templates/
```

## Fuentes de verdad

- Backlog, prioridad, estado y evidencia enlazada: `YouTrack`
- Codigo, PRs, checks y releases: `GitHub`
- Proceso, arquitectura, contratos y documentacion durable: repo `docs/`

No duplicar tracking transaccional dentro del repo.

## Documentos de entrada

- Vision y foco de producto: `docs/00-product/vision.md`
- Proceso compartido: `docs/03-process/README.md`
- Contrato para agentes: `docs/07-agents/agent-ops-contract.md`
- Onboarding de developers: `docs/08-developers/developer-tooling-onboarding.md`
- Base tecnica vigente: `docs/01-architecture/technical-base.md`
- QA minima: `docs/05-qa/test-strategy.md`

## Estructura documental

### `docs/03-process/`

Carril compartido para developers y agentes:

- `working-agreement.md`
- `task-lifecycle.md`
- `branching-and-commits.md`
- `technical-documentation-policy.md`
- `secrets-and-access.md`
- `youtrack-structure.md`

### `docs/07-agents/`

Carril especifico para agentes:

- `agent-ops-contract.md`
- `agent-ready-task-checklist.md`
- `plan-prompt.md`
- `implement-prompt.md`
- `review-prompt.md`

### `docs/08-developers/`

Carril especifico para developers:

- `developer-tooling-onboarding.md`

### `docs/01-architecture/`

Arquitectura y contratos tecnicos vigentes, alineados al codigo actual:

- `technical-base.md`
- `agentic-brain.md`
- `agentic-brain-system1-implementation-guide.md`
- `identity-master-schema.md`
- `traceability-contracts.md`
- `visual-generation-engine.md`
- `comfyui-copilot-governance.md`
- `directus-s1-control-plane.md`

### `docs/99-archive/`

Archivo historico. No es fuente de verdad activa.

## Flujo operativo por tarea

1. Tomar tarea en `YouTrack`.
2. Pasarla a `In Progress`.
3. Pedir plan.
4. Aprobar con `IMPLEMENTAR PLAN` o `PLAN OK`.
5. Implementar sobre `develop`, salvo pedido explicito de rama nueva.
6. Ejecutar validaciones relevantes.
7. Actualizar documentacion impactada.
8. Dejar evidencia en tarea y PR.
9. Integrar solo con `MERGE OK`.

## Codigo actual

La implementacion viva hoy se concentra en:

- `src/vixenbliss_creator/agentic/`: grafo y adapters del cerebro agentico
- `src/vixenbliss_creator/contracts/`: contratos persistibles y tipos compartidos
- `src/vixenbliss_creator/s1_control/`: servicios y puentes operativos de `Sistema 1`
- `src/vixenbliss_creator/visual_pipeline/`: contrato y servicio del motor visual
- `src/vixenbliss_creator/runtime_providers/`: abstraccion de proveedores de runtime
- `infra/`: runtimes y bundles de despliegue por servicio
- `tests/`: cobertura de contratos, servicios y runtimes

## Baseline compartido de tooling

- Entorno base: `env.example`
- Dependencias Python: `requirements.txt`
- MCPs versionables: `templates/agent-tooling/mcp.servers.example.json`
- Skills compartidas: `templates/agent-tooling/skills.manifest.example.yaml`
- Secretos y accesos: `docs/03-process/secrets-and-access.md`
- Contrato de agentes: `docs/07-agents/agent-ops-contract.md`
- Onboarding de developer: `docs/08-developers/developer-tooling-onboarding.md`

## Bootstrap local de Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
```

`requirements.txt` es la unica fuente de verdad de dependencias Python del repo.
