import { Database, HardDrive } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface StatusBarProps {
  projectName?: string;
  totalTokens?: number;
  currentFile?: string;
  offlineMode?: boolean;
}

export function StatusBar({
  projectName,
  totalTokens,
  currentFile,
  offlineMode = true
}: StatusBarProps) {
  const { t } = useTranslation();
  return (
    <div className="h-6 bg-card border-t border-border flex items-center justify-between px-3 text-[11px] text-secondary-text select-none">
      <div className="flex items-center gap-4">
        {projectName && (
          <div className="flex items-center gap-1.5">
            <Database className="w-3 h-3" />
            <span className="font-mono">{projectName}</span>
          </div>
        )}
        {totalTokens !== undefined && (
          <div className="flex items-center gap-1.5">
            <span>{t('app.status.tokens', { count: totalTokens.toLocaleString() })}</span>
          </div>
        )}
        {currentFile && (
          <div className="flex items-center gap-1.5">
            <HardDrive className="w-3 h-3" />
            <span className="font-mono">{currentFile}</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <div className={`w-1.5 h-1.5 rounded-full ${offlineMode ? 'bg-success' : 'bg-warning'}`}></div>
          <span>{offlineMode ? t('app.status.offlineReady') : t('app.status.online')}</span>
        </div>
        <span className="font-mono">Imbizo-CS v1.0.0</span>
        <span>AGPLv3</span>
      </div>
    </div>
  );
}
