export type NavRoute = {
  label: string
  href: string
}

export const navRoutes: NavRoute[] = [
  { label: "Panel", href: "/" },
  { label: "Avatares", href: "/avatars" },
  { label: "Fabrica de Contenido", href: "/factory" },
  { label: "Distribucion", href: "/distribution" },
  { label: "Monetizacion", href: "/revenue" },
]

const routeLabels: Record<string, string> = {
  "/": "Panel",
  "/avatars": "Avatares",
  "/models": "Modelos",
  "/factory": "Fabrica de Contenido",
  "/content": "Contenido",
  "/distribution": "Distribucion",
  "/revenue": "Monetizacion",
  "/settings": "Configuracion",
}

export function getRouteLabel(pathname: string): string {
  if (routeLabels[pathname]) return routeLabels[pathname]

  const segments = pathname.split("/").filter(Boolean)
  if (segments.length === 0) return "Panel"

  const built = `/${segments[0]}`
  return routeLabels[built] ?? segments[0].replace(/-/g, " ")
}
