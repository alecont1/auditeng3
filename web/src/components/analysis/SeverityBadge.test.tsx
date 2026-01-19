import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { SeverityBadge } from './SeverityBadge'

describe('SeverityBadge', () => {
  it('renders "Critical" with red styling for severity="critical"', () => {
    render(<SeverityBadge severity="critical" />)

    const badge = screen.getByText('Critical')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('bg-red-100')
    expect(badge).toHaveClass('text-red-800')
    expect(badge).toHaveClass('border-red-200')
  })

  it('renders "Major" with orange styling for severity="major"', () => {
    render(<SeverityBadge severity="major" />)

    const badge = screen.getByText('Major')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('bg-orange-100')
    expect(badge).toHaveClass('text-orange-800')
  })

  it('renders "Minor" with yellow styling for severity="minor"', () => {
    render(<SeverityBadge severity="minor" />)

    const badge = screen.getByText('Minor')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('bg-yellow-100')
    expect(badge).toHaveClass('text-yellow-800')
  })

  it('renders "Info" with slate styling for severity="info"', () => {
    render(<SeverityBadge severity="info" />)

    const badge = screen.getByText('Info')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('bg-slate-100')
    expect(badge).toHaveClass('text-slate-800')
  })

  it('applies custom className prop', () => {
    render(<SeverityBadge severity="critical" className="custom-class" />)

    const badge = screen.getByText('Critical')
    expect(badge).toHaveClass('custom-class')
  })

  it('renders "Unknown" with gray styling when severity is undefined', () => {
    render(<SeverityBadge severity={undefined} />)

    const badge = screen.getByText('Unknown')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('bg-gray-100')
    expect(badge).toHaveClass('text-gray-800')
  })

  it('renders "Unknown" with gray styling when severity is null', () => {
    render(<SeverityBadge severity={null} />)

    const badge = screen.getByText('Unknown')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('bg-gray-100')
    expect(badge).toHaveClass('text-gray-800')
  })
})
