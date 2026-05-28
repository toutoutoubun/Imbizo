import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { ProvenanceLogStrip } from '../ProvenanceLogStrip';

describe('ProvenanceLogStrip', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('shows the most recent event when collapsed', () => {
    render(<ProvenanceLogStrip />);
    expect(screen.getByText(/Changed token #6 language/i)).toBeInTheDocument();
  });

  it('toggles expanded state and persists it', () => {
    render(<ProvenanceLogStrip />);
    const toggle = screen.getByRole('button', { name: /expand provenance log/i });
    fireEvent.click(toggle);

    expect(localStorage.getItem('imbizoCS.provenanceLog.expanded')).toBe('true');
    expect(screen.getByRole('button', { name: /collapse provenance log/i })).toBeInTheDocument();
  });
});
