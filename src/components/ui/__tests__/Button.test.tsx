import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import { Button } from '@/components/ui/button'

describe('Button Component', () => {
  describe('Basic Rendering', () => {
    it('should render button with default props', () => {
      render(<Button>Click me</Button>)
      
      const button = screen.getByRole('button', { name: 'Click me' })
      expect(button).toBeInTheDocument()
      expect(button).not.toBeDisabled()
    })

    it('should render button with custom type', () => {
      render(<Button type="submit">Submit</Button>)
      
      const button = screen.getByRole('button', { name: 'Submit' })
      expect(button).toHaveAttribute('type', 'submit')
    })

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLButtonElement>()
      
      render(
        <Button ref={ref}>
          Ref Button
        </Button>
      )
      
      expect(ref.current).toBeInstanceOf(HTMLButtonElement)
      expect(ref.current?.textContent).toBe('Ref Button')
    })
  })

  describe('Variants', () => {
    const variants = ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'] as const

    variants.forEach(variant => {
      it(`should render ${variant} variant correctly`, () => {
        render(<Button variant={variant}>Button</Button>)
        
        const button = screen.getByRole('button')
        expect(button).toBeInTheDocument()
        
        // Check that variant-specific classes are applied
        const classList = Array.from(button.classList)
        expect(classList.some(cls => cls.includes('bg-') || cls.includes('border') || cls.includes('text-'))).toBe(true)
      })
    })
  })

  describe('Sizes', () => {
    const sizes = ['default', 'sm', 'lg', 'icon'] as const

    sizes.forEach(size => {
      it(`should render ${size} size correctly`, () => {
        render(<Button size={size}>Button</Button>)
        
        const button = screen.getByRole('button')
        expect(button).toBeInTheDocument()
        
        // Check that size-specific classes are applied
        const classList = Array.from(button.classList)
        expect(classList.some(cls => cls.includes('h-') || cls.includes('px-') || cls.includes('py-'))).toBe(true)
      })
    })
  })

  describe('Loading State', () => {
    it('should show loading spinner when isLoading is true', () => {
      render(<Button isLoading>Save</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
      expect(button).toHaveAttribute('aria-busy', 'true')
      
      // Check for loading spinner
      const spinner = button.querySelector('svg')
      expect(spinner).toBeInTheDocument()
      expect(spinner).toHaveClass('animate-spin')
    })

    it('should show custom loading text', () => {
      render(
        <Button isLoading loadingText="Saving...">
          Save
        </Button>
      )
      
      const button = screen.getByRole('button', { name: 'Saving...' })
      expect(button).toBeInTheDocument()
    })

    it('should fallback to children when no loading text provided', () => {
      render(<Button isLoading>Save</Button>)
      
      const button = screen.getByRole('button', { name: 'Save' })
      expect(button).toBeInTheDocument()
    })
  })

  describe('Disabled State', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Button disabled>Disabled Button</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('should be disabled when loading', () => {
      render(<Button isLoading>Loading Button</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('should not respond to clicks when disabled', async () => {
      const user = userEvent.setup()
      const handleClick = vi.fn()
      
      render(
        <Button disabled onClick={handleClick}>
          Disabled Button
        </Button>
      )
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(handleClick).not.toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('should apply aria-label correctly', () => {
      render(<Button ariaLabel="Close dialog">×</Button>)
      
      const button = screen.getByRole('button', { name: 'Close dialog' })
      expect(button).toHaveAttribute('aria-label', 'Close dialog')
    })

    it('should apply aria-describedby correctly', () => {
      render(
        <>
          <Button ariaDescribedBy="help-text">Submit</Button>
          <div id="help-text">This button submits the form</div>
        </>
      )
      
      const button = screen.getByRole('button', { name: 'Submit' })
      expect(button).toHaveAttribute('aria-describedby', 'help-text')
    })

    it('should have proper focus indicators', () => {
      render(<Button>Focus me</Button>)
      
      const button = screen.getByRole('button')
      
      // Check for focus-visible classes
      expect(button).toHaveClass('focus-visible:ring-2')
      expect(button).toHaveClass('focus-visible:ring-ring')
      expect(button).toHaveClass('focus-visible:ring-offset-2')
    })

    it('should hide spinner from screen readers', () => {
      render(<Button isLoading>Loading</Button>)
      
      const spinner = document.querySelector('svg')
      expect(spinner).toHaveAttribute('aria-hidden', 'true')
    })
  })

  describe('User Interactions', () => {
    it('should handle click events', async () => {
      const user = userEvent.setup()
      const handleClick = vi.fn()
      
      render(<Button onClick={handleClick}>Click me</Button>)
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('should handle keyboard events', async () => {
      const user = userEvent.setup()
      const handleClick = vi.fn()
      
      render(<Button onClick={handleClick}>Press me</Button>)
      
      const button = screen.getByRole('button')
      button.focus()
      await user.keyboard('{Enter}')
      
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('should handle space key activation', async () => {
      const user = userEvent.setup()
      const handleClick = vi.fn()
      
      render(<Button onClick={handleClick}>Space me</Button>)
      
      const button = screen.getByRole('button')
      button.focus()
      await user.keyboard('{ }')
      
      expect(handleClick).toHaveBeenCalledTimes(1)
    })
  })

  describe('Custom Props', () => {
    it('should apply custom className', () => {
      render(<Button className="custom-class">Custom</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
    })

    it('should spread additional props', () => {
      render(
        <Button data-testid="custom-button" id="my-button">
          Custom Props
        </Button>
      )
      
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('data-testid', 'custom-button')
      expect(button).toHaveAttribute('id', 'my-button')
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty children', () => {
      render(<Button></Button>)
      
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
      expect(button).toHaveTextContent('')
    })

    it('should handle complex children', () => {
      render(
        <Button>
          <span>Icon</span>
          Button Text
        </Button>
      )
      
      const button = screen.getByRole('button')
      expect(button).toHaveTextContent('IconButton Text')
    })

    it('should maintain accessibility when both disabled and loading', () => {
      render(<Button disabled isLoading>Both States</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
      expect(button).toHaveAttribute('aria-busy', 'true')
    })
  })
})
