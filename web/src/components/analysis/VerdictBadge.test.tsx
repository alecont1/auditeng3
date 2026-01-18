import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { VerdictBadge } from './VerdictBadge'

describe('VerdictBadge', () => {
  it('renders "Approved" with green styling for verdict="APPROVED"', () => {
    render(<VerdictBadge verdict="APPROVED" />)

    const badge = screen.getByText('Approved')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('border-green-500')
    expect(badge).toHaveClass('text-green-700')
  })

  it('renders "Rejected" with red styling for verdict="REJECTED"', () => {
    render(<VerdictBadge verdict="REJECTED" />)

    const badge = screen.getByText('Rejected')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('border-red-500')
    expect(badge).toHaveClass('text-red-700')
  })

  it('renders "Needs Review" with amber outline styling for verdict="NEEDS_REVIEW"', () => {
    render(<VerdictBadge verdict="NEEDS_REVIEW" />)

    const badge = screen.getByText('Needs Review')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('border-amber-500')
    expect(badge).toHaveClass('text-amber-700')
    expect(badge).toHaveClass('bg-transparent')
  })

  it('applies custom className prop', () => {
    render(<VerdictBadge verdict="APPROVED" className="custom-class" />)

    const badge = screen.getByText('Approved')
    expect(badge).toHaveClass('custom-class')
  })
})
