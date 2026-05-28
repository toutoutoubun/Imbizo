import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from './ui/Button';
import {
  FileText,
  Mic,
  FileEdit,
  FileSpreadsheet,
  BarChart3,
  Settings,
  Clock,
  Languages,
  Database,
  ChevronRight
} from 'lucide-react';

interface ProjectDashboardProps {
  projectName: string;
  onNavigateToEditor: () => void;
  onNavigateToSpreadsheet: () => void;
  onNavigateToTimeline: () => void;
  onNavigateToMetrics: () => void;
  onNavigateToSettings: () => void;
}

const recentActivity = [
  { id: '1', timestamp: '2026-05-26 14:32:15', action: 'Updated language label for token #2847 from auto-detected English to isiZulu', user: 'Manual override' },
  { id: '2', timestamp: '2026-05-26 14:28:03', action: 'Added concord link between tokens #2831 (umfana) and #2835 (wakhe)', user: 'Manual annotation' },
  { id: '3', timestamp: '2026-05-26 14:21:47', action: 'Set switch type for tokens #2820-2823 to intra-sentential', user: 'Manual annotation' },
  { id: '4', timestamp: '2026-05-26 13:58:12', action: 'Imported transcript segment 15 from ELAN file', user: 'Import operation' },
  { id: '5', timestamp: '2026-05-26 13:45:29', action: 'Auto-detection completed for segment 15 (342 tokens)', user: 'Auto-LID' },
];

export function ProjectDashboard({
  projectName,
  onNavigateToEditor,
  onNavigateToSpreadsheet,
  onNavigateToTimeline,
  onNavigateToMetrics,
  onNavigateToSettings
}: ProjectDashboardProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'overview' | 'editor' | 'spreadsheet' | 'timeline' | 'metrics' | 'reports' | 'settings'>('overview');

  return (
    <div className="flex h-screen bg-background">
      {/* Left sidebar - File tree */}
      <div className="w-64 border-r border-border bg-sidebar overflow-auto">
        <div className="p-4">
          <h2 className="text-[12px] uppercase text-secondary-text mb-3">{t('app.dashboard.projectFiles')}</h2>
          <div className="space-y-1">
            <div className="flex items-center gap-2 px-2 py-1.5 hover:bg-subtle-bg rounded-sm cursor-pointer">
              <Mic className="w-4 h-4 text-secondary-text" />
              <span className="text-[13px]">{t('app.dashboard.audio')}</span>
              <span className="ml-auto text-[11px] text-secondary-text">3</span>
            </div>
            <div className="pl-4 space-y-1">
              <div className="px-2 py-1 text-[12px] text-secondary-text hover:bg-subtle-bg rounded-sm cursor-pointer">
                segment-01.wav
              </div>
              <div className="px-2 py-1 text-[12px] text-secondary-text hover:bg-subtle-bg rounded-sm cursor-pointer">
                segment-02.wav
              </div>
              <div className="px-2 py-1 text-[12px] text-secondary-text hover:bg-subtle-bg rounded-sm cursor-pointer">
                segment-15.wav
              </div>
            </div>

            <div className="flex items-center gap-2 px-2 py-1.5 hover:bg-subtle-bg rounded-sm cursor-pointer">
              <FileText className="w-4 h-4 text-secondary-text" />
              <span className="text-[13px]">{t('app.dashboard.transcripts')}</span>
              <span className="ml-auto text-[11px] text-secondary-text">3</span>
            </div>

            <div className="flex items-center gap-2 px-2 py-1.5 hover:bg-subtle-bg rounded-sm cursor-pointer">
              <FileEdit className="w-4 h-4 text-secondary-text" />
              <span className="text-[13px]">{t('app.dashboard.annotations')}</span>
              <span className="ml-auto text-[11px] text-secondary-text">3</span>
            </div>

            <div className="flex items-center gap-2 px-2 py-1.5 hover:bg-subtle-bg rounded-sm cursor-pointer">
              <FileSpreadsheet className="w-4 h-4 text-secondary-text" />
              <span className="text-[13px]">Exports</span>
              <span className="ml-auto text-[11px] text-secondary-text">7</span>
            </div>

            <div className="flex items-center gap-2 px-2 py-1.5 hover:bg-subtle-bg rounded-sm cursor-pointer">
              <BarChart3 className="w-4 h-4 text-secondary-text" />
              <span className="text-[13px]">Reports</span>
              <span className="ml-auto text-[11px] text-secondary-text">2</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <div className="border-b border-border bg-card">
          <div className="px-6 py-4">
            <h1 className="text-[20px] mb-3">{projectName}</h1>
            <div className="flex gap-1">
              <button
                onClick={() => setActiveTab('overview')}
                className={`px-3 py-1.5 text-[12px] uppercase tracking-wide rounded-sm transition-colors ${
                  activeTab === 'overview' ? 'bg-primary text-primary-foreground' : 'hover:bg-subtle-bg'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => { setActiveTab('editor'); onNavigateToEditor(); }}
                className={`px-3 py-1.5 text-[12px] uppercase tracking-wide rounded-sm transition-colors ${
                  activeTab === 'editor' ? 'bg-primary text-primary-foreground' : 'hover:bg-subtle-bg'
                }`}
              >
                {t('app.nav.editor')}
              </button>
              <button
                onClick={() => { setActiveTab('spreadsheet'); onNavigateToSpreadsheet(); }}
                className={`px-3 py-1.5 text-[12px] uppercase tracking-wide rounded-sm transition-colors ${
                  activeTab === 'spreadsheet' ? 'bg-primary text-primary-foreground' : 'hover:bg-subtle-bg'
                }`}
              >
                {t('app.nav.spreadsheet')}
              </button>
              <button
                onClick={() => { setActiveTab('timeline'); onNavigateToTimeline(); }}
                className={`px-3 py-1.5 text-[12px] uppercase tracking-wide rounded-sm transition-colors ${
                  activeTab === 'timeline' ? 'bg-primary text-primary-foreground' : 'hover:bg-subtle-bg'
                }`}
              >
                {t('app.nav.timeline')}
              </button>
              <button
                onClick={() => { setActiveTab('metrics'); onNavigateToMetrics(); }}
                className={`px-3 py-1.5 text-[12px] uppercase tracking-wide rounded-sm transition-colors ${
                  activeTab === 'metrics' ? 'bg-primary text-primary-foreground' : 'hover:bg-subtle-bg'
                }`}
              >
                {t('app.nav.metrics')}
              </button>
              <button
                onClick={() => setActiveTab('reports')}
                className={`px-3 py-1.5 text-[12px] uppercase tracking-wide rounded-sm transition-colors ${
                  activeTab === 'reports' ? 'bg-primary text-primary-foreground' : 'hover:bg-subtle-bg'
                }`}
              >
                {t('app.nav.reports')}
              </button>
              <button
                onClick={() => { setActiveTab('settings'); onNavigateToSettings(); }}
                className={`px-3 py-1.5 text-[12px] uppercase tracking-wide rounded-sm transition-colors ${
                  activeTab === 'settings' ? 'bg-primary text-primary-foreground' : 'hover:bg-subtle-bg'
                }`}
              >
                {t('app.nav.settings')}
              </button>
            </div>
          </div>
        </div>

        {/* Main pane - Project overview */}
        <div className="flex-1 overflow-auto">
          <div className="p-6">
            <div className="grid grid-cols-2 gap-6 mb-8">
              {/* Key metrics */}
              <div className="space-y-4">
                <h2 className="text-[16px] mb-4">{t('app.dashboard.projectMetrics')}</h2>

                <div className="p-4 border border-border rounded-sm bg-card">
                  <div className="text-[12px] text-secondary-text mb-1">{t('app.dashboard.totalTokens')}</div>
                  <div className="text-[32px] font-mono">2,847</div>
                </div>

                <div className="p-4 border border-border rounded-sm bg-card">
                  <div className="text-[12px] text-secondary-text mb-2">{t('app.dashboard.languages')}</div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-lang-english rounded-full"></div>
                        <span className="text-[13px]">English</span>
                      </div>
                      <span className="text-[13px] font-mono">62.3%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-lang-isizulu rounded-full"></div>
                        <span className="text-[13px]">isiZulu</span>
                      </div>
                      <span className="text-[13px] font-mono">34.1%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-lang-afrikaans rounded-full"></div>
                        <span className="text-[13px]">Afrikaans</span>
                      </div>
                      <span className="text-[13px] font-mono">3.6%</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 border border-border rounded-sm bg-card">
                  <div className="text-[12px] text-secondary-text mb-1">Last Modified</div>
                  <div className="text-[14px]">2026-05-26 14:32:15</div>
                </div>

                <div className="p-4 border border-border rounded-sm bg-card">
                  <div className="text-[12px] text-secondary-text mb-2">{t('app.dashboard.dictionaries')}</div>
                  <div className="space-y-1 text-[12px] font-mono text-secondary-text">
                    <div>eng: v2023.1</div>
                    <div>zul: v2024.2</div>
                    <div>afr: v2023.4</div>
                  </div>
                </div>
              </div>

              {/* Quick actions */}
              <div>
                <h2 className="text-[16px] mb-4">{t('app.dashboard.quickActions')}</h2>
                <div className="space-y-2">
                  <button
                    onClick={onNavigateToEditor}
                    className="w-full p-4 border border-border rounded-sm bg-card hover:bg-subtle-bg transition-colors text-left flex items-center justify-between group"
                  >
                    <div className="flex items-center gap-3">
                      <FileEdit className="w-5 h-5 text-secondary-text" />
                      <div>
                        <div className="text-[14px]">{t('app.dashboard.annotationEditor')}</div>
                        <div className="text-[12px] text-secondary-text">{t('app.dashboard.continueAnnotating')}</div>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-secondary-text group-hover:text-foreground transition-colors" />
                  </button>

                  <button
                    onClick={onNavigateToMetrics}
                    className="w-full p-4 border border-border rounded-sm bg-card hover:bg-subtle-bg transition-colors text-left flex items-center justify-between group"
                  >
                    <div className="flex items-center gap-3">
                      <BarChart3 className="w-5 h-5 text-secondary-text" />
                      <div>
                        <div className="text-[14px]">View Metrics Dashboard</div>
                        <div className="text-[12px] text-secondary-text">Explore visualizations and statistics</div>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-secondary-text group-hover:text-foreground transition-colors" />
                  </button>

                  <button className="w-full p-4 border border-border rounded-sm bg-card hover:bg-subtle-bg transition-colors text-left flex items-center justify-between group">
                    <div className="flex items-center gap-3">
                      <FileSpreadsheet className="w-5 h-5 text-secondary-text" />
                      <div>
                        <div className="text-[14px]">Export Data</div>
                        <div className="text-[12px] text-secondary-text">CSV, XLSX, ELAN, or Praat format</div>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-secondary-text group-hover:text-foreground transition-colors" />
                  </button>

                  <button className="w-full p-4 border border-border rounded-sm bg-card hover:bg-subtle-bg transition-colors text-left flex items-center justify-between group">
                    <div className="flex items-center gap-3">
                      <Database className="w-5 h-5 text-secondary-text" />
                      <div>
                        <div className="text-[14px]">Backup Project</div>
                        <div className="text-[12px] text-secondary-text">Create a portable zip archive</div>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-secondary-text group-hover:text-foreground transition-colors" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right sidebar - Recent activity */}
        <div className="absolute right-0 top-[85px] bottom-0 w-80 border-l border-border bg-card overflow-auto">
          <div className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Clock className="w-4 h-4 text-secondary-text" />
              <h3 className="text-[12px] uppercase text-secondary-text">Recent Activity</h3>
            </div>
            <div className="space-y-3">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="pb-3 border-b border-border last:border-0">
                  <div className="text-[11px] text-secondary-text font-mono mb-1">
                    {activity.timestamp}
                  </div>
                  <div className="text-[12px] mb-1">{activity.action}</div>
                  <div className="text-[11px] text-secondary-text">{activity.user}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
