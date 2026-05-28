import { act, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { useTranslation } from 'react-i18next';
import i18n from '../config';

function Probe() {
  const { t } = useTranslation();
  return (
    <div>
      <h1>{t('app.welcome.recentProjects')}</h1>
      <p>{t('missing.prototype.key')}</p>
    </div>
  );
}

describe('i18n', () => {
  it('renders English by default', () => {
    i18n.changeLanguage('en');
    render(<Probe />);
    expect(screen.getByText('Recent Projects')).toBeInTheDocument();
  });

  it('switches to Japanese and falls back for missing keys', async () => {
    render(<Probe />);
    await act(async () => {
      await i18n.changeLanguage('ja');
    });

    await waitFor(() => {
      expect(screen.getByText('最近のプロジェクト')).toBeInTheDocument();
    });
    expect(screen.getByText('missing.prototype.key')).toBeInTheDocument();
  });
});
