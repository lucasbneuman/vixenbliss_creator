# Infra neutral por servicio

La infraestructura nueva deja de organizarse por proveedor y pasa a organizarse por servicio.

Servicios objetivo:

- `comfyui-copilot`
- `s1-image`
- `s1-lora-train`
- `s1-llm`
- `s2-image`
- `s2-video`

Cada servicio separa:

- `runtime/`: contenedor y bootstrap compartido del servicio
- `providers/modal/`: wrapper de deploy activo para Modal
- `providers/beam/`: placeholder futuro para Beam

Contrato recomendado por servicio:

- `POST /jobs`
- `GET /jobs/{id}`
- `GET /jobs/{id}/result`
- `GET /healthcheck`
- `GET /ws/jobs/{id}` o equivalente para progreso opcional por `WebSocket`

Persistencia temporal mientras la DB no este lista:

- manifests JSON y artefactos tecnicos fuera del repo
- `S1 llm`: manifiesto de generacion
- `S1 image`: manifiesto y paquete de dataset
- `S1 lora train`: manifiesto de training y metadata del LoRA

Los bundles `infra/runpod-*` quedan como referencia historica mientras se completa la migracion, pero no deben crecer como baseline nuevo.

En el estado actual del proyecto, la estrategia operativa es `Modal-only`.
