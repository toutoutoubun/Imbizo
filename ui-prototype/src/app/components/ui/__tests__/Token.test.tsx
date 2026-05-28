import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Token } from '../Token';
import type { HighlightMode } from '../Token';

const modes: HighlightMode[] = ['language', '4m', 'switch', 'trigger', 'mixed', 'integration'];

describe('Token', () => {
  it.each(modes)('renders accessible visual encoding for %s mode', (highlightMode) => {
    render(
      <Token
        id="t1"
        text="i-laptop"
        language="isizulu"
        glyph="■"
        highlightMode={highlightMode}
        isAuto
        isSelected
        matrixLanguage="isizulu"
        switchType="intra"
        fourMType="bridge_late"
        triggerRole="trigger"
        mixedCodeVariety="tsotsitaal"
        integrationScore={0.76}
      />
    );

    const token = screen.getByRole('button', { name: /i-laptop, language isizulu/i });
    expect(token).toHaveAttribute('aria-pressed', 'true');
    expect(token).toHaveAttribute('data-highlight-mode', highlightMode);
    expect(screen.getByText('■')).toBeInTheDocument();
  });

  it('computes a comprehensive aria-label', () => {
    render(
      <Token
        text="ndiya"
        language="isixhosa"
        glyph="◆"
        highlightMode="switch"
        switchType="inter"
        fourMType="early_system"
        triggerRole="triggered"
        isAuto={false}
        hasConflict
      />
    );

    expect(screen.getByRole('button')).toHaveAccessibleName(
      'ndiya, language isixhosa, 4-M early_system, switch inter, triggered, manually set, has conflict'
    );
  });

  it('activates with Enter and Space', () => {
    const onClick = vi.fn();
    render(<Token text="Yebo" language="isizulu" glyph="■" highlightMode="language" onClick={onClick} />);
    const token = screen.getByRole('button');

    fireEvent.keyDown(token, { key: 'Enter' });
    fireEvent.keyDown(token, { key: ' ' });

    expect(onClick).toHaveBeenCalledTimes(2);
  });
});
