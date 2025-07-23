/**
 * Accessibility Testing Utilities
 * 
 * Helper functions for testing accessibility features during development
 */

// Keyboard navigation test
export function testKeyboardNavigation() {
  console.group('🔍 Accessibility Testing: Keyboard Navigation');
  
  // Test focusable elements
  const focusableElements = document.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  console.log(`Found ${focusableElements.length} focusable elements`);
  
  // Test tab order
  const elementsWithTabIndex = Array.from(focusableElements).map((el, index) => ({
    element: el,
    tagName: el.tagName,
    tabIndex: (el as HTMLElement).tabIndex,
    ariaLabel: el.getAttribute('aria-label'),
    id: el.id,
    visualOrder: index
  }));
  
  console.table(elementsWithTabIndex);
  console.groupEnd();
  
  return elementsWithTabIndex;
}

// ARIA attributes test
export function testAriaAttributes() {
  console.group('🔍 Accessibility Testing: ARIA Attributes');
  
  // Find elements with ARIA attributes
  const ariaElements = document.querySelectorAll('[aria-label], [aria-labelledby], [aria-describedby], [role], [aria-expanded], [aria-hidden]');
  
  const ariaReport = Array.from(ariaElements).map(el => ({
    element: el.tagName,
    id: el.id || 'no-id',
    role: el.getAttribute('role'),
    ariaLabel: el.getAttribute('aria-label'),
    ariaLabelledBy: el.getAttribute('aria-labelledby'),
    ariaDescribedBy: el.getAttribute('aria-describedby'),
    ariaExpanded: el.getAttribute('aria-expanded'),
    ariaHidden: el.getAttribute('aria-hidden')
  }));
  
  console.table(ariaReport);
  console.groupEnd();
  
  return ariaReport;
}

// Screen reader content test
export function testScreenReaderContent() {
  console.group('🔍 Accessibility Testing: Screen Reader Content');
  
  // Find screen reader only content
  const srOnlyElements = document.querySelectorAll('.sr-only');
  console.log(`Found ${srOnlyElements.length} screen reader only elements`);
  
  srOnlyElements.forEach((el, index) => {
    console.log(`SR-Only ${index + 1}:`, el.textContent);
  });
  
  // Find alt text
  const images = document.querySelectorAll('img');
  const imageReport = Array.from(images).map(img => ({
    src: img.src,
    alt: img.alt || 'MISSING ALT TEXT',
    hasAlt: !!img.alt
  }));
  
  console.table(imageReport);
  console.groupEnd();
  
  return { srOnlyElements, imageReport };
}

// Color contrast test (basic)
export function testColorContrast() {
  console.group('🔍 Accessibility Testing: Color Contrast');
  
  // This is a basic implementation - in production you'd use a proper contrast checker
  const textElements = document.querySelectorAll('p, span, a, button, label, h1, h2, h3, h4, h5, h6');
  
  console.log(`Checking contrast for ${textElements.length} text elements`);
  console.log('Note: Use browser dev tools accessibility panel for detailed contrast analysis');
  
  console.groupEnd();
}

// Focus management test
export function testFocusManagement() {
  console.group('🔍 Accessibility Testing: Focus Management');
  
  // Test if focus is properly managed in modals
  const modals = document.querySelectorAll('[role="dialog"], [aria-modal="true"]');
  console.log(`Found ${modals.length} modal dialogs`);
  
  modals.forEach((modal, index) => {
    const focusableInModal = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    console.log(`Modal ${index + 1} has ${focusableInModal.length} focusable elements`);
  });
  
  console.groupEnd();
}

// Run all accessibility tests
export function runAccessibilityTests() {
  console.log('🚀 Running Accessibility Tests...');
  
  testKeyboardNavigation();
  testAriaAttributes();
  testScreenReaderContent();
  testColorContrast();
  testFocusManagement();
  
  console.log('✅ Accessibility tests completed. Check console for details.');
}

// Add to window for easy dev console access
if (typeof window !== 'undefined') {
  (window as any).accessibilityTests = {
    runAll: runAccessibilityTests,
    keyboard: testKeyboardNavigation,
    aria: testAriaAttributes,
    screenReader: testScreenReaderContent,
    contrast: testColorContrast,
    focus: testFocusManagement
  };
}
