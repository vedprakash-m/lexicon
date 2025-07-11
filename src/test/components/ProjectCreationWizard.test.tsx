import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ProjectCreationWizard } from '../../components/project/ProjectCreationWizard';
import { TestProviders } from '../setup/test-providers';

describe('ProjectCreationWizard', () => {
  const mockOnComplete = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderWizard = () => {
    return render(
      <TestProviders>
        <ProjectCreationWizard
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />
      </TestProviders>
    );
  };

  describe('Step 1: Project Type Selection', () => {
    it('should render step 1 with project type options', () => {
      renderWizard();

      expect(screen.getByText('Choose Project Type')).toBeInTheDocument();
      expect(screen.getByText('What kind of project would you like to create?')).toBeInTheDocument();
      
      // Check that all project types are rendered
      expect(screen.getByText('Book Collection')).toBeInTheDocument();
      expect(screen.getByText('Processing Workflow')).toBeInTheDocument();
      expect(screen.getByText('Export Configuration')).toBeInTheDocument();
    });

    it('should show step 1 as active in progress indicator', () => {
      renderWizard();

      // First step should be active (showing "1")
      const stepIndicators = screen.getAllByText('1');
      expect(stepIndicators).toHaveLength(1);
      
      // Other steps should show numbers
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('should allow selecting different project types', () => {
      renderWizard();

      // Click on Processing Workflow
      fireEvent.click(screen.getByText('Processing Workflow'));
      
      // The card should be selected (visual indication tested through className)
      const processingCard = screen.getByText('Processing Workflow').closest('.cursor-pointer');
      expect(processingCard).toHaveClass('border-primary');
    });

    it('should proceed to step 2 when Next is clicked', () => {
      renderWizard();

      // Click Next button
      fireEvent.click(screen.getByText('Next'));

      // Should now be on step 2
      expect(screen.getByText('Choose Template')).toBeInTheDocument();
    });

    it('should call onCancel when Cancel is clicked', () => {
      renderWizard();

      fireEvent.click(screen.getByText('Cancel'));

      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });
  });

  describe('Step 2: Template Selection', () => {
    const navigateToStep2 = () => {
      renderWizard();
      fireEvent.click(screen.getByText('Next'));
    };

    it('should render step 2 with template options', () => {
      navigateToStep2();

      expect(screen.getByText('Choose Template')).toBeInTheDocument();
      expect(screen.getByText('Select a template to get started quickly')).toBeInTheDocument();
      
      // Should show templates for default type (collection)
      expect(screen.getByText('Structured Scriptures')).toBeInTheDocument();
      expect(screen.getByText('Philosophy')).toBeInTheDocument();
      expect(screen.getByText('Technical Books')).toBeInTheDocument();
    });

    it('should show different templates based on selected project type', () => {
      renderWizard();
      
      // Select Processing Workflow type
      fireEvent.click(screen.getByText('Processing Workflow'));
      fireEvent.click(screen.getByText('Next'));

      // Should show processing templates
      expect(screen.getByText('RAG Optimized')).toBeInTheDocument();
      expect(screen.getByText('Research Notes')).toBeInTheDocument();
      expect(screen.getByText('Study Materials')).toBeInTheDocument();
    });

    it('should allow selecting a template', () => {
      navigateToStep2();

      fireEvent.click(screen.getByText('Structured Scriptures'));
      
      // Template should be selected
      const templateCard = screen.getByText('Structured Scriptures').closest('.cursor-pointer');
      expect(templateCard).toHaveClass('border-primary');
    });

    it('should disable Next button when no template is selected', () => {
      navigateToStep2();

      const nextButton = screen.getByText('Next');
      expect(nextButton).toBeDisabled();
    });

    it('should enable Next button when template is selected', () => {
      navigateToStep2();

      fireEvent.click(screen.getByText('Structured Scriptures'));
      
      const nextButton = screen.getByText('Next');
      expect(nextButton).toBeEnabled();
    });

    it('should go back to step 1 when Back is clicked', () => {
      navigateToStep2();

      fireEvent.click(screen.getByText('Back'));

      expect(screen.getByText('Choose Project Type')).toBeInTheDocument();
    });
  });

  describe('Step 3: Project Details', () => {
    const navigateToStep3 = () => {
      renderWizard();
      fireEvent.click(screen.getByText('Next')); // Go to step 2
      fireEvent.click(screen.getByText('Structured Scriptures')); // Select template
      fireEvent.click(screen.getByText('Next')); // Go to step 3
    };

    it('should render step 3 with project details form', () => {
      navigateToStep3();

      expect(screen.getByText('Project Details')).toBeInTheDocument();
      expect(screen.getByText('Give your project a name and description')).toBeInTheDocument();
      
      expect(screen.getByLabelText('Project Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Description')).toBeInTheDocument();
    });

    it('should show project summary', () => {
      navigateToStep3();

      expect(screen.getByText('Project Summary')).toBeInTheDocument();
      expect(screen.getByText('Type:')).toBeInTheDocument();
      expect(screen.getByText('Template:')).toBeInTheDocument();
      expect(screen.getByText('collection')).toBeInTheDocument();
      expect(screen.getByText('Structured Scriptures')).toBeInTheDocument();
    });

    it('should disable Create Project button when required fields are empty', () => {
      navigateToStep3();

      const createButton = screen.getByText('Create Project');
      expect(createButton).toBeDisabled();
    });

    it('should enable Create Project button when all fields are filled', () => {
      navigateToStep3();

      const nameInput = screen.getByLabelText('Project Name');
      const descriptionInput = screen.getByLabelText('Description');

      fireEvent.change(nameInput, { target: { value: 'Test Project' } });
      fireEvent.change(descriptionInput, { target: { value: 'Test Description' } });

      const createButton = screen.getByText('Create Project');
      expect(createButton).toBeEnabled();
    });

    it('should call onComplete with correct project data when Create Project is clicked', async () => {
      navigateToStep3();

      const nameInput = screen.getByLabelText('Project Name');
      const descriptionInput = screen.getByLabelText('Description');

      fireEvent.change(nameInput, { target: { value: 'Test Project' } });
      fireEvent.change(descriptionInput, { target: { value: 'Test Description' } });

      fireEvent.click(screen.getByText('Create Project'));

      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalledWith({
          name: 'Test Project',
          description: 'Test Description',
          type: 'collection',
          status: 'active',
          booksCount: 0,
          createdAt: expect.any(Date),
          lastModified: expect.any(Date)
        });
      });
    });

    it('should go back to step 2 when Back is clicked', () => {
      navigateToStep3();

      fireEvent.click(screen.getByText('Back'));

      expect(screen.getByText('Choose Template')).toBeInTheDocument();
    });
  });

  describe('Progress Indicator', () => {
    it('should show correct progress at each step', () => {
      renderWizard();

      // Step 1: First step active
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();

      // Go to step 2
      fireEvent.click(screen.getByText('Next'));
      
      // Step 2: First step completed (check icon), second step active
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();

      // Go to step 3
      fireEvent.click(screen.getByText('Structured Scriptures'));
      fireEvent.click(screen.getByText('Next'));
      
      // Step 3: First two steps completed, third step active
      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should validate name field is not empty', () => {
      renderWizard();
      
      // Navigate to step 3
      fireEvent.click(screen.getByText('Next'));
      fireEvent.click(screen.getByText('Structured Scriptures'));
      fireEvent.click(screen.getByText('Next'));

      const nameInput = screen.getByLabelText('Project Name');
      const descriptionInput = screen.getByLabelText('Description');

      // Fill description but leave name empty
      fireEvent.change(descriptionInput, { target: { value: 'Test Description' } });
      
      const createButton = screen.getByText('Create Project');
      expect(createButton).toBeDisabled();

      // Fill name with whitespace only
      fireEvent.change(nameInput, { target: { value: '   ' } });
      expect(createButton).toBeDisabled();

      // Fill name with actual content
      fireEvent.change(nameInput, { target: { value: 'Test Project' } });
      expect(createButton).toBeEnabled();
    });

    it('should validate description field is not empty', () => {
      renderWizard();
      
      // Navigate to step 3
      fireEvent.click(screen.getByText('Next'));
      fireEvent.click(screen.getByText('Structured Scriptures'));
      fireEvent.click(screen.getByText('Next'));

      const nameInput = screen.getByLabelText('Project Name');
      const descriptionInput = screen.getByLabelText('Description');

      // Fill name but leave description empty
      fireEvent.change(nameInput, { target: { value: 'Test Project' } });
      
      const createButton = screen.getByText('Create Project');
      expect(createButton).toBeDisabled();

      // Fill description with whitespace only
      fireEvent.change(descriptionInput, { target: { value: '   ' } });
      expect(createButton).toBeDisabled();

      // Fill description with actual content
      fireEvent.change(descriptionInput, { target: { value: 'Test Description' } });
      expect(createButton).toBeEnabled();
    });
  });
});
