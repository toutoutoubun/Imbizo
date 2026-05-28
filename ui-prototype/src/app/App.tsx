import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { MenuBar } from './components/MenuBar';
import { Sidebar } from './components/Sidebar';
import { StatusBar } from './components/StatusBar';
import { AnnotationEditor } from './components/AnnotationEditor';
import { Button } from './components/ui/Button';
import {
  FolderOpen,
  FilePlus,
  Archive,
  FileEdit,
  BarChart3,
  FileSpreadsheet,
  Database,
  ChevronRight,
  Clock,
  Mic,
  FileText
} from 'lucide-react';

type View = 'home' | 'editor' | 'spreadsheet' | 'timeline' | 'metrics' | 'reports' | 'settings';

interface Project {
  id: string;
  name: string;
  languagePair: string;
  tokenCount: number;
  lastOpened: string;
  location: string;
}

const mockProjects: Project[] = [
  {
    id: '1',
    name: 'Township Family Conversations',
    languagePair: 'isiZulu–English',
    tokenCount: 2847,
    lastOpened: '2026-05-26 14:32',
    location: '/Users/researcher/Documents/imbizo-projects/township-family'
  },
  {
    id: '2',
    name: 'Code-Switching in Education',
    languagePair: 'isiXhosa–English',
    tokenCount: 1523,
    lastOpened: '2026-05-20 09:15',
    location: '/Users/researcher/Documents/imbizo-projects/education-study'
  },
  {
    id: '3',
    name: 'Multilingual Market Interactions',
    languagePair: 'Sesotho–Afrikaans–English',
    tokenCount: 3912,
    lastOpened: '2026-05-18 16:48',
    location: '/Users/researcher/Documents/imbizo-projects/market-study'
  }
];

const recentActivity = [
  { id: '1', timestamp: '2026-05-26 14:32:15', action: 'Updated language label for token #2847', user: 'Manual override' },
  { id: '2', timestamp: '2026-05-26 14:28:03', action: 'Added concord link between tokens #2831-#2835', user: 'Manual annotation' },
  { id: '3', timestamp: '2026-05-26 14:21:47', action: 'Set switch type for tokens #2820-2823', user: 'Manual annotation' },
  { id: '4', timestamp: '2026-05-26 13:58:12', action: 'Imported transcript segment 15 from ELAN', user: 'Import' },
  { id: '5', timestamp: '2026-05-26 13:45:29', action: 'Auto-detection completed for segment 15', user: 'Auto-LID' },
];

export default function App() {
  const { t, i18n } = useTranslation();
  const [currentView, setCurrentView] = useState<View>('home');
  const [currentProject, setCurrentProject] = useState<Project | null>(null);

  const handleOpenProject = (projectId: string) => {
    const project = mockProjects.find(p => p.id === projectId);
    if (project) {
      setCurrentProject(project);
      setCurrentView('home');
    }
  };

  const handleNewProject = () => {
    setCurrentView('home');
  };

  const handleOpenProjectDialog = () => {
    setCurrentView('home');
  };

  const handleSaveProject = () => undefined;

  const handleExportData = () => undefined;

  const handleSettings = () => {
    setCurrentView('settings');
  };

  const handleQuit = () => undefined;

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Application Menu Bar */}
      <MenuBar
        currentProject={currentProject?.name}
        onNewProject={handleNewProject}
        onOpenProject={handleOpenProjectDialog}
        onSaveProject={handleSaveProject}
        onExportData={handleExportData}
        onSettings={handleSettings}
        onQuit={handleQuit}
      />

      {/* Main Application Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          currentView={currentView}
          onNavigate={(view) => setCurrentView(view as View)}
          hasProject={!!currentProject}
        />

        {/* Main Content */}
        <div className="flex-1 overflow-hidden">
          {currentView === 'home' && !currentProject && (
            <div className="h-full flex flex-col">
              <div className="flex-1 flex items-center justify-center p-8">
                <div className="max-w-4xl w-full">
                  <div className="mb-8">
                    <h1 className="text-[24px] leading-[1.2] mb-2">{t('app.title')}</h1>
                    <p className="text-[14px] text-secondary-text leading-[1.5]">
                      {t('app.tagline')}
                    </p>
                  </div>

                  <div className="flex gap-3 mb-8">
                    <Button onClick={handleNewProject} size="lg">
                      <FilePlus className="w-4 h-4" />
                      {t('app.actions.newProject')}
                    </Button>
                    <Button onClick={handleOpenProjectDialog} variant="outline" size="lg">
                      <FolderOpen className="w-4 h-4" />
                      {t('app.actions.openProject')}
                    </Button>
                    <Button variant="outline" size="lg">
                      <Archive className="w-4 h-4" />
                      {t('app.actions.importZip')}
                    </Button>
                  </div>

                  <div>
                    <h2 className="text-[14px] mb-3 uppercase tracking-wide text-secondary-text">{t('app.welcome.recentProjects')}</h2>
                    <div className="space-y-1">
                      {mockProjects.map((project) => (
                        <button
                          key={project.id}
                          onClick={() => handleOpenProject(project.id)}
                          className="w-full text-left p-3 border border-border rounded-sm hover:bg-subtle-bg transition-colors duration-100 focus:outline focus:outline-2 focus:outline-primary"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h3 className="text-[14px] mb-1">{project.name}</h3>
                              <div className="flex gap-4 text-[11px] text-secondary-text font-mono">
                                <span>{project.languagePair}</span>
                                <span>{t('app.status.tokens', { count: project.tokenCount.toLocaleString() })}</span>
                                <span>{project.lastOpened}</span>
                              </div>
                            </div>
                            <FolderOpen className="w-4 h-4 text-secondary-text" />
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {currentView === 'home' && currentProject && (
            <div className="h-full flex">
              <div className="flex-1 overflow-auto p-6">
                <h1 className="text-[20px] mb-6">{currentProject.name}</h1>

                <div className="grid grid-cols-2 gap-6 mb-6">
                  <div className="space-y-3">
                    <h2 className="text-[14px] uppercase tracking-wide text-secondary-text mb-3">{t('app.dashboard.projectMetrics')}</h2>

                    <div className="p-4 border border-border rounded-sm bg-card">
                      <div className="text-[11px] text-secondary-text mb-1 uppercase tracking-wide">{t('app.dashboard.totalTokens')}</div>
                      <div className="text-[32px] font-mono leading-none">{currentProject.tokenCount.toLocaleString()}</div>
                    </div>

                    <div className="p-4 border border-border rounded-sm bg-card">
                      <div className="text-[11px] text-secondary-text mb-2 uppercase tracking-wide">{t('app.dashboard.languages')}</div>
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-[12px]">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-lang-english rounded-full"></div>
                            <span>English</span>
                          </div>
                          <span className="font-mono">62.3%</span>
                        </div>
                        <div className="flex items-center justify-between text-[12px]">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-lang-isizulu rounded-full"></div>
                            <span>isiZulu</span>
                          </div>
                          <span className="font-mono">34.1%</span>
                        </div>
                        <div className="flex items-center justify-between text-[12px]">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-lang-afrikaans rounded-full"></div>
                            <span>Afrikaans</span>
                          </div>
                          <span className="font-mono">3.6%</span>
                        </div>
                      </div>
                    </div>

                    <div className="p-3 border border-border rounded-sm bg-card">
                      <div className="text-[11px] text-secondary-text mb-1 uppercase tracking-wide">{t('app.dashboard.dictionaries')}</div>
                      <div className="space-y-0.5 text-[11px] font-mono text-secondary-text">
                        <div>eng: v2023.1</div>
                        <div>zul: v2024.2</div>
                        <div>afr: v2023.4</div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h2 className="text-[14px] uppercase tracking-wide text-secondary-text mb-3">{t('app.dashboard.quickActions')}</h2>
                    <div className="space-y-2">
                      <button
                        onClick={() => setCurrentView('editor')}
                        className="w-full p-3 border border-border rounded-sm bg-card hover:bg-subtle-bg transition-colors text-left flex items-center justify-between group"
                      >
                        <div className="flex items-center gap-2.5">
                          <FileEdit className="w-4 h-4 text-secondary-text" />
                          <div>
                            <div className="text-[13px]">{t('app.dashboard.annotationEditor')}</div>
                            <div className="text-[11px] text-secondary-text">{t('app.dashboard.continueAnnotating')}</div>
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-secondary-text" />
                      </button>

                      <button
                        onClick={() => setCurrentView('spreadsheet')}
                        className="w-full p-3 border border-border rounded-sm bg-card hover:bg-subtle-bg transition-colors text-left flex items-center justify-between group"
                      >
                        <div className="flex items-center gap-2.5">
                          <FileSpreadsheet className="w-4 h-4 text-secondary-text" />
                          <div>
                            <div className="text-[13px]">{t('app.dashboard.spreadsheetView')}</div>
                            <div className="text-[11px] text-secondary-text">{t('app.dashboard.tabularDataView')}</div>
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-secondary-text" />
                      </button>

                      <button
                        onClick={() => setCurrentView('metrics')}
                        className="w-full p-3 border border-border rounded-sm bg-card hover:bg-subtle-bg transition-colors text-left flex items-center justify-between group"
                      >
                        <div className="flex items-center gap-2.5">
                          <BarChart3 className="w-4 h-4 text-secondary-text" />
                          <div>
                            <div className="text-[13px]">{t('app.dashboard.metricsDashboard')}</div>
                            <div className="text-[11px] text-secondary-text">{t('app.dashboard.viewStatistics')}</div>
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-secondary-text" />
                      </button>

                      <button
                        onClick={handleExportData}
                        className="w-full p-3 border border-border rounded-sm bg-card hover:bg-subtle-bg transition-colors text-left flex items-center justify-between group"
                      >
                        <div className="flex items-center gap-2.5">
                          <Database className="w-4 h-4 text-secondary-text" />
                          <div>
                            <div className="text-[13px]">{t('app.actions.exportData')}</div>
                            <div className="text-[11px] text-secondary-text">CSV, XLSX, ELAN, Praat</div>
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-secondary-text" />
                      </button>
                    </div>
                  </div>
                </div>

                <div className="mb-6">
                  <h2 className="text-[14px] uppercase tracking-wide text-secondary-text mb-3">{t('app.dashboard.projectFiles')}</h2>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 border border-border rounded-sm bg-card">
                      <div className="flex items-center gap-2 mb-2">
                        <Mic className="w-3.5 h-3.5 text-secondary-text" />
                        <span className="text-[11px] uppercase tracking-wide text-secondary-text">{t('app.dashboard.audio')}</span>
                      </div>
                      <div className="text-[20px] font-mono">3</div>
                      <div className="text-[11px] text-secondary-text">{t('app.dashboard.files')}</div>
                    </div>
                    <div className="p-3 border border-border rounded-sm bg-card">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="w-3.5 h-3.5 text-secondary-text" />
                        <span className="text-[11px] uppercase tracking-wide text-secondary-text">{t('app.dashboard.transcripts')}</span>
                      </div>
                      <div className="text-[20px] font-mono">3</div>
                      <div className="text-[11px] text-secondary-text">{t('app.dashboard.files')}</div>
                    </div>
                    <div className="p-3 border border-border rounded-sm bg-card">
                      <div className="flex items-center gap-2 mb-2">
                        <FileEdit className="w-3.5 h-3.5 text-secondary-text" />
                        <span className="text-[11px] uppercase tracking-wide text-secondary-text">{t('app.dashboard.annotations')}</span>
                      </div>
                      <div className="text-[20px] font-mono">3</div>
                      <div className="text-[11px] text-secondary-text">{t('app.dashboard.files')}</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="w-80 border-l border-border bg-card overflow-auto">
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Clock className="w-3.5 h-3.5 text-secondary-text" />
                    <h3 className="text-[11px] uppercase tracking-wide text-secondary-text">{t('app.dashboard.recentActivity')}</h3>
                  </div>
                  <div className="space-y-3">
                    {recentActivity.map((activity) => (
                      <div key={activity.id} className="pb-2.5 border-b border-border last:border-0">
                        <div className="text-[10px] text-secondary-text font-mono mb-1">
                          {activity.timestamp}
                        </div>
                        <div className="text-[11px] leading-tight mb-1">{activity.action}</div>
                        <div className="text-[10px] text-secondary-text">{activity.user}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {currentView === 'editor' && currentProject && (
            <AnnotationEditor />
          )}

          {currentView === 'spreadsheet' && currentProject && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-[20px] mb-2">{t('app.views.spreadsheet')}</h1>
                <p className="text-[12px] text-secondary-text">{t('app.views.spreadsheetDescription')}</p>
              </div>
            </div>
          )}

          {currentView === 'timeline' && currentProject && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-[20px] mb-2">{t('app.views.timeline')}</h1>
                <p className="text-[12px] text-secondary-text">{t('app.views.timelineDescription')}</p>
              </div>
            </div>
          )}

          {currentView === 'metrics' && currentProject && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-[20px] mb-2">{t('app.views.metrics')}</h1>
                <p className="text-[12px] text-secondary-text">{t('app.views.metricsDescription')}</p>
              </div>
            </div>
          )}

          {currentView === 'reports' && currentProject && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-[20px] mb-2">{t('app.views.reports')}</h1>
                <p className="text-[12px] text-secondary-text">{t('app.views.reportsDescription')}</p>
              </div>
            </div>
          )}

          {currentView === 'settings' && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-[20px] mb-2">{t('app.views.settings')}</h1>
                <p className="text-[12px] text-secondary-text mb-4">{t('app.views.settingsDescription')}</p>
                <label className="block text-[12px] text-secondary-text mb-1" htmlFor="interface-language">
                  {t('app.settings.language')}
                </label>
                <select
                  id="interface-language"
                  className="px-3 py-2 bg-input-background border border-input rounded-sm text-[14px]"
                  value={i18n.language}
                  onChange={(event) => i18n.changeLanguage(event.target.value)}
                >
                  <option value="en">English</option>
                  <option value="ja">日本語</option>
                  <option value="af">Afrikaans</option>
                  <option value="zul">isiZulu</option>
                  <option value="xho">isiXhosa</option>
                  <option value="sot">Sesotho</option>
                  <option value="tsn">Setswana</option>
                </select>
                <p className="text-[11px] text-secondary-text mt-2">{t('app.settings.languageHelp')}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Status Bar */}
      <StatusBar
        projectName={currentProject?.name}
        totalTokens={currentProject?.tokenCount}
        offlineMode={true}
      />
    </div>
  );
}
