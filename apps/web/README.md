# Web App

Espacio dedicado del front dentro del monorepo.

Objetivo actual:

- actuar como puerta de entrada web de `VixenBliss Creator`
- alojar la experiencia inicial de chat con `LangGraph`
- convivir con el backend orquestador actual sin quedar pegado al runtime de `S1 Image`

Estructura inicial:

- `public/index.html`: shell principal de la app web
- `public/assets/styles.css`: estilos compartidos
- `public/assets/app.js`: comportamiento del front y consumo de endpoints

En esta etapa el backend Python sigue sirviendo estos archivos para simplificar deploy en `Coolify`.
La separacion en `apps/web/` deja el camino listo para desacoplar front y back mas adelante sin rearmar la superficie de la aplicacion.
