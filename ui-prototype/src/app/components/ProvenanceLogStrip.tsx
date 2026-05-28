import { useEffect, useMemo, useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useProvenanceLog } from '../hooks/useProvenanceLog';

const STORAGE_KEY = 'imbizoCS.provenanceLog.expanded';

export function ProvenanceLogStrip() {
  const { t } = useTranslation();
  const events = useProvenanceLog();
  const [expanded, setExpanded] = useState(() => localStorage.getItem(STORAGE_KEY) === 'true');
  const latest = useMemo(() => events[0], [events]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(expanded));
  }, [expanded]);

  return (
    <section
      aria-label={t('annotation.provenance.label')}
      className={`border-t border-border bg-card transition-all duration-100 ease-out ${expanded ? 'max-h-[240px]' : 'h-4'}`}
    >
      <div className="flex items-start h-full">
        <div className="flex-1 overflow-auto px-3 py-0.5">
          {!expanded && latest && (
            <div className="text-[11px] leading-[14px] truncate">
              <span className="font-mono text-secondary-text mr-2">{latest.timestamp}</span>
              <span className="mr-2">{latest.description}</span>
              <span className="text-secondary-text">[{latest.source}]</span>
            </div>
          )}
          {expanded && (
            <div className="max-h-[232px] overflow-auto py-2 space-y-1">
              {events.slice(0, 100).map((event) => (
                <div key={event.id} className="grid grid-cols-[140px_1fr_110px] gap-3 text-[11px] border-b border-border/60 pb-1">
                  <span className="font-mono text-[10px] text-secondary-text">{event.timestamp}</span>
                  <span>{event.description}</span>
                  <span className="text-secondary-text">{event.source}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        <button
          type="button"
          aria-label={expanded ? t('annotation.provenance.collapse') : t('annotation.provenance.expand')}
          aria-expanded={expanded}
          className="w-8 h-4 flex items-center justify-center hover:bg-subtle-bg focus:outline focus:outline-2 focus:outline-primary"
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
        </button>
      </div>
    </section>
  );
}
