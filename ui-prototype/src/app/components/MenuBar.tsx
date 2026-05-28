import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  FileText,
  FolderOpen,
  Save,
  Download,
  Settings,
  HelpCircle,
  X,
  Minimize,
  Square,
  ChevronDown
} from 'lucide-react';

interface MenuBarProps {
  currentProject?: string;
  onNewProject: () => void;
  onOpenProject: () => void;
  onSaveProject: () => void;
  onExportData: () => void;
  onSettings: () => void;
  onQuit: () => void;
}

export function MenuBar({
  currentProject,
  onNewProject,
  onOpenProject,
  onSaveProject,
  onExportData,
  onSettings,
  onQuit
}: MenuBarProps) {
  const { t } = useTranslation();
  const [activeMenu, setActiveMenu] = useState<string | null>(null);

  const menuItems = [
    {
      id: 'file',
      label: t('app.menu.file'),
      items: [
        { label: t('app.menu.newProject'), shortcut: 'Ctrl+N', action: onNewProject },
        { label: t('app.menu.openProject'), shortcut: 'Ctrl+O', action: onOpenProject },
        { type: 'separator' },
        { label: t('app.menu.save'), shortcut: 'Ctrl+S', action: onSaveProject, disabled: !currentProject },
        { label: t('app.menu.export'), shortcut: 'Ctrl+E', action: onExportData, disabled: !currentProject },
        { type: 'separator' },
        { label: t('app.menu.quit'), shortcut: 'Ctrl+Q', action: onQuit },
      ]
    },
    {
      id: 'edit',
      label: t('app.menu.edit'),
      items: [
        { label: t('app.menu.undo'), shortcut: 'Ctrl+Z', disabled: true },
        { label: t('app.menu.redo'), shortcut: 'Ctrl+Shift+Z', disabled: true },
        { type: 'separator' },
        { label: t('app.menu.find'), shortcut: 'Ctrl+F', disabled: !currentProject },
        { label: t('app.menu.replace'), shortcut: 'Ctrl+H', disabled: !currentProject },
      ]
    },
    {
      id: 'view',
      label: t('app.menu.view'),
      items: [
        { label: t('app.menu.zoomIn'), shortcut: 'Ctrl++' },
        { label: t('app.menu.zoomOut'), shortcut: 'Ctrl+-' },
        { label: t('app.menu.resetZoom'), shortcut: 'Ctrl+0' },
        { type: 'separator' },
        { label: t('app.menu.toggleSidebar'), shortcut: 'Ctrl+B' },
        { label: t('app.menu.toggleStatusBar'), shortcut: 'Ctrl+/' },
      ]
    },
    {
      id: 'window',
      label: t('app.menu.window'),
      items: [
        { label: t('app.menu.minimize'), shortcut: 'Ctrl+M' },
        { label: t('app.menu.zoom') },
        { type: 'separator' },
        { label: t('app.menu.bringAllToFront') },
      ]
    },
    {
      id: 'help',
      label: t('app.menu.help'),
      items: [
        { label: t('app.menu.documentation'), shortcut: 'F1' },
        { label: t('app.menu.principles') },
        { label: t('app.menu.releaseNotes') },
        { type: 'separator' },
        { label: t('app.menu.about'), action: onSettings },
      ]
    }
  ];

  return (
    <div className="h-9 bg-card border-b border-border flex items-center justify-between px-2 select-none">
      <div className="flex items-center">
        <div className="flex gap-0.5">
          {menuItems.map((menu) => (
            <div key={menu.id} className="relative">
              <button
                className={`px-3 py-1 text-[13px] hover:bg-subtle-bg rounded-sm transition-colors ${
                  activeMenu === menu.id ? 'bg-subtle-bg' : ''
                }`}
                onMouseEnter={() => activeMenu && setActiveMenu(menu.id)}
                onClick={() => setActiveMenu(activeMenu === menu.id ? null : menu.id)}
              >
                {menu.label}
              </button>

              {activeMenu === menu.id && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setActiveMenu(null)}
                  />
                  <div className="absolute top-full left-0 mt-1 w-56 bg-popover border border-border rounded-sm shadow-lg z-20 py-1">
                    {menu.items.map((item, index) => {
                      if (item.type === 'separator') {
                        return <div key={index} className="my-1 border-t border-border" />;
                      }
                      return (
                        <button
                          key={index}
                          className={`w-full px-3 py-1.5 text-[13px] text-left flex items-center justify-between ${
                            item.disabled
                              ? 'text-muted-foreground cursor-not-allowed'
                              : 'hover:bg-subtle-bg'
                          }`}
                          disabled={item.disabled}
                          onClick={() => {
                            if (!item.disabled && item.action) {
                              item.action();
                              setActiveMenu(null);
                            }
                          }}
                        >
                          <span>{item.label}</span>
                          {item.shortcut && (
                            <span className="text-[11px] text-secondary-text font-mono ml-4">
                              {item.shortcut}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-4">
        {currentProject && (
          <span className="text-[12px] text-secondary-text font-mono">
            {currentProject}
          </span>
        )}
        <div className="flex gap-2">
          <button className="p-1 hover:bg-subtle-bg rounded-sm transition-colors">
            <Minimize className="w-3.5 h-3.5 text-secondary-text" />
          </button>
          <button className="p-1 hover:bg-subtle-bg rounded-sm transition-colors">
            <Square className="w-3.5 h-3.5 text-secondary-text" />
          </button>
          <button className="p-1 hover:bg-destructive hover:text-destructive-foreground rounded-sm transition-colors">
            <X className="w-3.5 h-3.5 text-secondary-text" />
          </button>
        </div>
      </div>
    </div>
  );
}
