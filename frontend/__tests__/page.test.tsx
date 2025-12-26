import { render, screen } from '@testing-library/react'
import Home from '@/app/page'

describe('Home Page', () => {
  it('renders the title', () => {
    render(<Home />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('VixenBliss Creator')
  })

  it('renders the description', () => {
    render(<Home />)
    const description = screen.getByText(/AI Avatar Management Platform/i)
    expect(description).toBeInTheDocument()
  })
})
