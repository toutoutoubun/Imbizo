import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useKeyboardShortcuts } from './useKeyboardShortcuts';

function Harness({ handlers }: { handlers: Parameters<typeof useKeyboardShortcuts>[0] }) {
  useKeyboardShortcuts(handlers);
  return <input aria-label="editable" />;
}

describe('useKeyboardShortcuts', () => {
  it('fires every mapped shortcut handler', () => {
    const handlers = {
      onArrowLeft: vi.fn(),
      onArrowRight: vi.fn(),
      onShiftArrowLeft: vi.fn(),
      onShiftArrowRight: vi.fn(),
      onAltArrowLeft: vi.fn(),
      onAltArrowRight: vi.fn(),
      onCtrlArrowLeft: vi.fn(),
      onCtrlArrowRight: vi.fn(),
      onLanguagePicker: vi.fn(),
      onFourMPicker: vi.fn(),
      onTogglePlayback: vi.fn(),
      onToggleTrigger: vi.fn(),
      onUndo: vi.fn(),
      onRedo: vi.fn(),
      onEscape: vi.fn(),
      onCycleHighlightMode: vi.fn(),
      onMode1: vi.fn(),
      onMode2: vi.fn(),
      onMode3: vi.fn(),
      onMode4: vi.fn(),
      onMode5: vi.fn(),
      onMode6: vi.fn(),
    };
    render(<Harness handlers={handlers} />);

    [
      new KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true }),
      new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }),
      new KeyboardEvent('keydown', { key: 'ArrowLeft', shiftKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: 'ArrowRight', shiftKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: 'ArrowLeft', altKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: 'ArrowRight', altKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: 'ArrowLeft', ctrlKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: 'ArrowRight', ctrlKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: 'l', bubbles: true }),
      new KeyboardEvent('keydown', { key: 'm', bubbles: true }),
      new KeyboardEvent('keydown', { key: ' ', bubbles: true }),
      new KeyboardEvent('keydown', { key: 't', bubbles: true }),
      new KeyboardEvent('keydown', { key: 'z', ctrlKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: 'z', metaKey: true, shiftKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }),
      new KeyboardEvent('keydown', { key: '/', ctrlKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: '1', ctrlKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: '2', ctrlKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: '3', ctrlKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: '4', ctrlKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: '5', ctrlKey: true, bubbles: true }),
      new KeyboardEvent('keydown', { key: '6', ctrlKey: true, bubbles: true }),
    ].forEach((event) => document.dispatchEvent(event));

    Object.values(handlers).forEach((handler) => {
      expect(handler).toHaveBeenCalledTimes(1);
    });
  });

  it('suppresses shortcuts inside editable controls', () => {
    const onTogglePlayback = vi.fn();
    const { getByLabelText } = render(<Harness handlers={{ onTogglePlayback }} />);
    const input = getByLabelText('editable');
    input.focus();

    input.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true }));

    expect(onTogglePlayback).not.toHaveBeenCalled();
  });
});
