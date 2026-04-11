# Web App

Espacio dedicado del front dentro del monorepo.

Objetivo actual:

- actuar como puerta de entrada web de `VixenBliss Creator`
- alojar la experiencia conversacional multi-turno con `LangGraph`
- convivir con el backend orquestador actual sin quedar pegado al runtime de `S1 Image`
- proteger el workspace con login interno via `Directus`

Estructura inicial:

- `public/index.html`: shell principal de la app web
- `public/assets/styles.css`: estilos compartidos
- `public/assets/app.js`: comportamiento del front y consumo de endpoints

Capacidades actuales del front:

- pantalla de login para usuarios internos autenticados contra `Directus`
- workspace minimo en dos columnas: chat e inspeccion
- chat multi-turno que mantiene un draft conversacional incremental por `session_id`
- overwrite manual de atributos ya inferidos en turnos previos
- gate de readiness antes del handoff a `S1 Image`
- handoff explicito a `S1 Image`
- referencia facial opcional via URL o archivo temporal

En esta etapa el backend Python sigue sirviendo estos archivos para simplificar deploy en `Coolify`.
La separacion en `apps/web/` deja el camino listo para desacoplar front y back mas adelante sin rearmar la superficie de la aplicacion.
