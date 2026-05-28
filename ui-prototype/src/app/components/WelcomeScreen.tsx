import { Button } from './ui/Button';
import { FolderOpen, FilePlus, Archive } from 'lucide-react';
import { useTranslation } from 'react-i18next';

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

interface WelcomeScreenProps {
  onOpenProject: (projectId: string) => void;
  onCreateProject: () => void;
  onImportProject: () => void;
}

export function WelcomeScreen({ onOpenProject, onCreateProject, onImportProject }: WelcomeScreenProps) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <header className="px-8 py-6 border-b border-border">
        <h1 className="text-[24px] leading-[1.2] mb-2">{t('app.title')}</h1>
        <p className="text-[14px] text-secondary-text leading-[1.5]">
          {t('app.tagline')}
        </p>
      </header>

      <main className="flex-1 px-8 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-[16px]">{t('app.welcome.recentProjects')}</h2>
            <div className="flex gap-2">
              <Button onClick={onImportProject} variant="outline" size="sm">
                <Archive className="w-4 h-4" />
                {t('app.actions.importFromZip')}
              </Button>
              <Button onClick={onCreateProject} size="sm">
                <FilePlus className="w-4 h-4" />
                {t('app.actions.createNewProject')}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            {mockProjects.map((project) => (
              <button
                key={project.id}
                onClick={() => onOpenProject(project.id)}
                className="w-full text-left p-4 border border-border rounded-sm hover:bg-subtle-bg transition-colors duration-100 focus:outline focus:outline-2 focus:outline-primary"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-[14px] mb-1">{project.name}</h3>
                    <div className="flex gap-4 text-[12px] text-secondary-text">
                      <span>{project.languagePair}</span>
                      <span>{t('app.status.tokens', { count: project.tokenCount.toLocaleString() })}</span>
                      <span>{t('app.welcome.lastOpened', { date: project.lastOpened })}</span>
                    </div>
                    <div className="mt-2 text-[11px] text-secondary-text font-mono">
                      {project.location}
                    </div>
                  </div>
                  <FolderOpen className="w-5 h-5 text-secondary-text" />
                </div>
              </button>
            ))}
          </div>

          {mockProjects.length === 0 && (
            <div className="text-center py-16">
              <p className="text-secondary-text mb-4">{t('app.welcome.noRecentProjects')}</p>
              <Button onClick={onCreateProject}>
                <FilePlus className="w-4 h-4" />
                {t('app.welcome.createFirstProject')}
              </Button>
            </div>
          )}
        </div>
      </main>

      <footer className="px-8 py-4 border-t border-border">
        <div className="max-w-4xl mx-auto flex items-center justify-between text-[12px] text-secondary-text">
          <div className="flex gap-4">
            <span>{t('app.title')} v1.0.0</span>
            <a href="#" className="hover:text-foreground transition-colors">AGPLv3</a>
            <a href="#" className="hover:text-foreground transition-colors">PRINCIPLES.md</a>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-success rounded-full"></div>
            <span>{t('app.status.offlineReady')}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
