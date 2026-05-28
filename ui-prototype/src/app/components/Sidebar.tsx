import {
  Home,
  FileEdit,
  Table2,
  Clock,
  BarChart3,
  FileText,
  Settings
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface SidebarProps {
  currentView: string;
  onNavigate: (view: string) => void;
  hasProject: boolean;
}

const navItems = [
  { id: 'home', labelKey: 'app.nav.home', icon: Home, requiresProject: false },
  { id: 'editor', labelKey: 'app.nav.editor', icon: FileEdit, requiresProject: true },
  { id: 'spreadsheet', labelKey: 'app.nav.spreadsheet', icon: Table2, requiresProject: true },
  { id: 'timeline', labelKey: 'app.nav.timeline', icon: Clock, requiresProject: true },
  { id: 'metrics', labelKey: 'app.nav.metrics', icon: BarChart3, requiresProject: true },
  { id: 'reports', labelKey: 'app.nav.reports', icon: FileText, requiresProject: true },
  { id: 'settings', labelKey: 'app.nav.settings', icon: Settings, requiresProject: true },
];

export function Sidebar({ currentView, onNavigate, hasProject }: SidebarProps) {
  const { t } = useTranslation();
  return (
    <div className="w-16 bg-sidebar border-r border-sidebar-border flex flex-col items-center py-3 gap-1">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isDisabled = item.requiresProject && !hasProject;
        const isActive = currentView === item.id;

        return (
          <button
            key={item.id}
            onClick={() => !isDisabled && onNavigate(item.id)}
            disabled={isDisabled}
            className={`w-12 h-12 flex flex-col items-center justify-center gap-0.5 rounded-sm transition-colors group ${
              isActive
                ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                : isDisabled
                ? 'text-muted-foreground cursor-not-allowed opacity-40'
                : 'hover:bg-sidebar-accent text-sidebar-foreground'
            }`}
            title={t(item.labelKey)}
          >
            <Icon className="w-5 h-5" />
            <span className="text-[9px] uppercase tracking-wide">{t(item.labelKey)}</span>
          </button>
        );
      })}
    </div>
  );
}
