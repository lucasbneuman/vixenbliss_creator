import { render, screen } from "@testing-library/react"
import Home from "@/app/page"

describe("Home Page", () => {
  it("renders the main heading", () => {
    render(<Home />)
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Panel")
  })

  it("renders the systems description", () => {
    render(<Home />)
    expect(screen.getByText(/Sistemas 1 y 2/i)).toBeInTheDocument()
  })
})
