# External Systems

Esta carpeta centraliza dependencias externas (AI providers, workers, APIs third-party).

## Archivos activos

- `docs/external-systems/modal-sdxl-lora.md`: contrato y flujo del worker Modal SDXL + LoRA.

## Regla para nuevos sistemas externos

1. Crear un archivo por sistema en esta carpeta.
2. Documentar contrato de entrada/salida, auth, errores y fallback.
3. Enlazar su impacto en sistemas S1..S5 (`docs/SYSTEM_MAP.md`).
4. Si se reemplaza un doc previo, archivarlo primero en `docs/_archive/`.
