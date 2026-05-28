import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { AnnotationEditor } from '../AnnotationEditor';

describe('AnnotationEditor', () => {
  it('changes highlight mode and propagates it to tokens', () => {
    render(<AnnotationEditor />);

    fireEvent.click(screen.getByRole('button', { name: /by trigger/i }));

    const token = screen.getByRole('button', { name: /i-laptop, language isizulu/i });
    expect(token).toHaveAttribute('data-highlight-mode', 'trigger');
    expect(token).toHaveAttribute('data-trigger-role', 'trigger');
    expect(screen.getByText(/Current mode:/i)).toBeInTheDocument();
  });

  it('selecting a token populates the annotation pane and shows Bantu noun class fields', () => {
    render(<AnnotationEditor />);
    fireEvent.click(screen.getByRole('button', { name: /umfana, language isizulu/i }));

    expect(screen.getByText(/Token ID: 9/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Noun class/i)).toBeInTheDocument();
    expect(screen.getByText(/Concord links/i)).toBeInTheDocument();
  });

  it('expands the integration score explanation', () => {
    render(<AnnotationEditor />);
    fireEvent.click(screen.getByRole('button', { name: /How is this computed/i }));

    expect(screen.getByText(/0\.35 × class_prefix/i)).toBeInTheDocument();
    expect(screen.getAllByText(/concord_link/i).length).toBeGreaterThan(0);
  });

  it('shows concord candidates in the transcript', () => {
    render(<AnnotationEditor />);
    fireEvent.click(screen.getAllByRole('button', { name: /Show candidates in utterance/i })[0]);

    const transcript = screen.getByLabelText('Transcript tokens');
    expect(within(transcript).getByRole('button', { name: /i-laptop/i })).toHaveClass('ring-2');
  });

  it('supports undo and redo keyboard shortcuts for token edits', async () => {
    render(<AnnotationEditor />);
    const language = screen.getByLabelText('Language');

    fireEvent.change(language, { target: { value: 'english' } });
    expect(screen.getByRole('button', { name: /i-laptop, language english/i })).toBeInTheDocument();

    await act(async () => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'z', ctrlKey: true, bubbles: true }));
    });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /i-laptop, language isizulu/i })).toBeInTheDocument();
    });

    await act(async () => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'z', ctrlKey: true, shiftKey: true, bubbles: true }));
    });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /i-laptop, language english/i })).toBeInTheDocument();
    });
  });
});
