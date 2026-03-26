Documento — Contexto YouTrack VixenBliss
1. Contexto general

VixenBliss es un holding tecnológico enfocado en productos digitales, inteligencia artificial generativa y monetización de contenido.

El holding tiene varias unidades de negocio activas:

VixenBliss School → plataforma de cursos

VixenBliss TV → plataforma tipo OnlyFans con avatares IA

VixenBliss Agency → gestión de modelos virtuales

VixenBliss Create → SaaS para creación de avatares

Todas las unidades comparten el mismo equipo técnico y operativo.

El equipo es pequeño (5 personas actualmente, máximo esperado 10), por lo que la organización se hace por área de trabajo y no por unidad de negocio.

2. Filosofía de organización

Reglas principales:

No separar proyectos por unidad de negocio

Usar pocos proyectos

Usar campos personalizados para clasificar

Usar filtros y paneles para visualizar

Mantener estructura simple y escalable

YouTrack se usa como centro de organización de todo el holding.

3. Proyectos actuales en YouTrack

Los proyectos representan áreas de trabajo, no productos.

Develop

Todo lo relacionado con desarrollo técnico.

Incluye:

backend

frontend

APIs

automatizaciones

IA

SaaS

infraestructura

integraciones

plugins

scripts

Usado por:

CTO

desarrolladores

Product

Todo lo relacionado con lo que se vende.

Incluye:

cursos

contenido

packs

features pagas

modelos

materiales

funnels de producto

Usado por:

operaciones

marketing

desarrollo

contenido

Marketing

Todo lo relacionado con tráfico y ventas.

Incluye:

campañas

ads

landings

copy

funnels

tracking

analytics

Usado por:

media buyers

marketing

operaciones

General

Tareas generales y operativas.

Incluye:

accesos

cuentas

organización

configuraciones

proveedores

pagos

tareas internas

Ideas

Backlog de ideas.

Incluye:

nuevas features

nuevos negocios

mejoras

automatizaciones futuras

experimentos

No todo lo que está en Ideas se ejecuta.

4. Campos personalizados

Todos los proyectos usan los mismos campos.

Unidad de negocio

Valores:

Create

School

TV

Agencia

Global

Este campo indica a qué unidad pertenece la tarea.

No se crean proyectos por unidad.

Tipo

Valores:

Error

Tarea

Épica

Brief

Significado:

Error → bug o problema
Tarea → trabajo concreto
Brief → objetivo grande o feature
Épica → conjunto grande de tareas

Jerarquía recomendada:

Idea → Brief → Tarea → Subtarea → Error

Estado

Valores típicos:

Pendiente

En progreso

En espera

Bloqueado

Terminado

Cancelado

Usuario asignado

Persona responsable.

Propiedad

Indica quién es dueño funcional de la tarea.

Puede ser distinto del asignado.

Ejemplo:

Max propietario
Dev asignado

Fecha de vencimiento

Fecha límite.

Se usa para paneles y seguimiento.

5. Reglas de uso

Reglas importantes:

No crear nuevos proyectos sin necesidad

Usar Unidad de negocio para clasificar

Usar Brief para features grandes

Usar Tarea para trabajo concreto

Usar Error para bugs

Usar Ideas para backlog

No duplicar tickets

No usar estructura rígida tipo Scrum

Mantener el sistema simple

6. Paneles

Se usan paneles para visualizar.

Paneles recomendados:

Personal

General

Develop

Marketing / Product

Los paneles usan filtros por:

Estado

Asignado

Unidad de negocio

Tipo

Fecha de vencimiento

7. Objetivo del sistema

El sistema debe permitir:

trabajar con pocas personas

manejar varias unidades de negocio

escalar sin romper estructura

automatizar tareas

integrarse con IA

integrarse con Codex

integrarse con APIs

No se busca estructura corporativa.
Se busca flexibilidad.

8. Uso con Codex

Codex debe asumir que:

los proyectos existentes son válidos

no debe crear nuevos proyectos sin motivo

debe usar Unidad de negocio para clasificar

debe respetar Tipo

debe respetar Estado

debe usar Develop para código

debe usar Product para contenido/producto

debe usar Marketing para campañas

debe usar General para tareas varias

debe usar Ideas para backlog

9. Fin del documento

Este documento define el contexto actual de YouTrack en VixenBliss.

Debe usarse como referencia para automatizaciones, scripts, MCP, Codex y herramientas internas.