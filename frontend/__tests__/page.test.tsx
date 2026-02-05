import { render, screen } from '@testing-library/react'
import Home from '@/app/page'

describe('Home Page', () => {
  it('renders the title', () => {
    render(<Home />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('Dashboard')
  })

  it('renders the description', () => {
    render(<Home />)
    const description = screen.getByText(/see money coming in/i)
    expect(description).toBeInTheDocument()
  })
})
