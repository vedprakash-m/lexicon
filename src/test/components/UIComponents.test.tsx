import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button, Card, Badge, Input, Progress } from '../../components/ui';

describe('UI Component Tests', () => {
  describe('Button Component', () => {
    it('renders button with correct text', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
    });

    it('handles click events', async () => {
      const user = userEvent.setup();
      const handleClick = vi.fn();
      
      render(<Button onClick={handleClick}>Click me</Button>);
      
      await user.click(screen.getByRole('button'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('applies variant styles correctly', () => {
      const { rerender } = render(<Button variant="default">Default</Button>);
      expect(screen.getByRole('button')).toHaveClass('bg-primary');
      
      rerender(<Button variant="destructive">Destructive</Button>);
      expect(screen.getByRole('button')).toHaveClass('bg-destructive');
      
      rerender(<Button variant="outline">Outline</Button>);
      expect(screen.getByRole('button')).toHaveClass('border');
    });

    it('applies size styles correctly', () => {
      const { rerender } = render(<Button size="default">Default</Button>);
      expect(screen.getByRole('button')).toHaveClass('h-10');
      
      rerender(<Button size="sm">Small</Button>);
      expect(screen.getByRole('button')).toHaveClass('h-9');
      
      rerender(<Button size="lg">Large</Button>);
      expect(screen.getByRole('button')).toHaveClass('h-11');
    });

    it('handles disabled state correctly', () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole('button');
      
      expect(button).toBeDisabled();
      expect(button).toHaveClass('disabled:opacity-50');
    });

    it('forwards ref correctly', () => {
      const ref = vi.fn();
      render(<Button ref={ref}>Button</Button>);
      expect(ref).toHaveBeenCalled();
    });
  });

  describe('Card Component', () => {
    it('renders card with children', () => {
      render(
        <Card>
          <div>Card content</div>
        </Card>
      );
      
      expect(screen.getByText('Card content')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      render(<Card className="custom-class">Content</Card>);
      const card = screen.getByText('Content').closest('div');
      expect(card).toHaveClass('custom-class');
    });

    it('applies default card styles', () => {
      render(<Card>Content</Card>);
      const card = screen.getByText('Content').closest('div');
      expect(card).toHaveClass('rounded-lg', 'border', 'bg-card');
    });

    it('forwards ref correctly', () => {
      const ref = vi.fn();
      render(<Card ref={ref}>Content</Card>);
      expect(ref).toHaveBeenCalled();
    });
  });

  describe('Badge Component', () => {
    it('renders badge with text', () => {
      render(<Badge>Status</Badge>);
      expect(screen.getByText('Status')).toBeInTheDocument();
    });

    it('applies variant styles correctly', () => {
      const { rerender } = render(<Badge variant="default">Default</Badge>);
      expect(screen.getByText('Default')).toHaveClass('bg-primary');
      
      rerender(<Badge variant="secondary">Secondary</Badge>);
      expect(screen.getByText('Secondary')).toHaveClass('bg-secondary');
      
      rerender(<Badge variant="destructive">Destructive</Badge>);
      expect(screen.getByText('Destructive')).toHaveClass('bg-destructive');
    });

    it('applies custom className', () => {
      render(<Badge className="custom-badge">Badge</Badge>);
      expect(screen.getByText('Badge')).toHaveClass('custom-badge');
    });
  });

  describe('Input Component', () => {
    it('renders input with placeholder', () => {
      render(<Input placeholder="Enter text" />);
      expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
    });

    it('handles value changes', async () => {
      const user = userEvent.setup();
      const handleChange = vi.fn();
      
      render(<Input onChange={handleChange} />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, 'test input');
      
      expect(handleChange).toHaveBeenCalled();
    });

    it('applies disabled state correctly', () => {
      render(<Input disabled />);
      const input = screen.getByRole('textbox');
      
      expect(input).toBeDisabled();
      expect(input).toHaveClass('disabled:cursor-not-allowed');
    });

    it('forwards ref correctly', () => {
      const ref = vi.fn();
      render(<Input ref={ref} />);
      expect(ref).toHaveBeenCalled();
    });

    it('applies error state correctly', () => {
      render(<Input className="border-red-500" />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('border-red-500');
    });
  });

  describe('Progress Component', () => {
    it('renders with correct value', () => {
      render(<Progress value={50} />);
      const progressBar = screen.getByRole('progressbar');
      
      expect(progressBar).toHaveAttribute('aria-valuenow', '50');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });

    it('displays visual progress correctly', () => {
      render(<Progress value={75} />);
      const progressBar = screen.getByRole('progressbar');
      const progressIndicator = progressBar.querySelector('div');
      
      // The progress indicator should have transform set to 25% (100 - 75)
      expect(progressIndicator).toHaveStyle('transform: translateX(-25%)');
    });

    it('handles edge values correctly', () => {
      const { rerender } = render(<Progress value={0} />);
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
      
      rerender(<Progress value={100} />);
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
    });

    it('applies custom className', () => {
      render(<Progress value={50} className="custom-progress" />);
      expect(screen.getByRole('progressbar')).toHaveClass('custom-progress');
    });
  });
});
