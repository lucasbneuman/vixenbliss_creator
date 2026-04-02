# Infra neutral por servicio

La infraestructura nueva deja de organizarse por proveedor y pasa a organizarse por servicio.

Servicios objetivo:

- `s1-image`
- `s1-lora-train`
- `s1-llm`
- `s2-image`
- `s2-video`

Cada servicio separa:

- `runtime/`: contenedor y bootstrap compartido del servicio
- `providers/beam/`: wrapper de deploy para Beam
- `providers/modal/`: wrapper de deploy para Modal

Los bundles `infra/runpod-*` quedan como referencia historica mientras se completa la migracion, pero no deben crecer como baseline nuevo.
