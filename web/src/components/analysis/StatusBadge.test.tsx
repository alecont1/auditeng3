import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { StatusBadge } from './StatusBadge'

describe('StatusBadge', () => {
  it('renders "Pending" with amber styling for status="pending"', () => {
    render(<StatusBadge status="pending" />)

    const badge = screen.getByText('Pending')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('bg-amber-100')
    expect(badge).toHaveClass('text-amber-800')
  })

  it('renders "Completed" with green styling for status="completed"', () => {
    render(<StatusBadge status="completed" />)

    const badge = screen.getByText('Completed')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('bg-green-100')
    expect(badge).toHaveClass('text-green-800')
  })

  it('renders "Failed" with red styling for status="failed"', () => {
    render(<StatusBadge status="failed" />)

    const badge = screen.getByText('Failed')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('bg-red-100')
    expect(badge).toHaveClass('text-red-800')
  })

  it('applies custom className prop', () => {
    render(<StatusBadge status="pending" className="custom-class" />)

    const badge = screen.getByText('Pending')
    expect(badge).toHaveClass('custom-class')
  })
})
