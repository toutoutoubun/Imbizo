import { useTranslation } from 'react-i18next';

export interface ProvenanceEvent {
  id: string;
  timestamp: string;
  description: string;
  source: string;
}

interface ProvenanceEventFixture {
  id: string;
  timestamp: string;
  descriptionKey: string;
  sourceKey: string;
}

const MOCK_EVENTS: ProvenanceEventFixture[] = [
  { id: 'p1', timestamp: '2026-05-26 14:32:15', descriptionKey: 'annotation.provenance.events.changedTokenLanguage', sourceKey: 'app.activity.source.manualOverride' },
  { id: 'p2', timestamp: '2026-05-26 14:28:03', descriptionKey: 'annotation.provenance.events.addedConcordCandidate', sourceKey: 'app.activity.source.manualAnnotation' },
  { id: 'p3', timestamp: '2026-05-26 14:21:47', descriptionKey: 'annotation.provenance.events.confirmedProperNounTrigger', sourceKey: 'app.activity.source.manualAnnotation' },
  { id: 'p4', timestamp: '2026-05-26 13:58:12', descriptionKey: 'annotation.provenance.events.importedTranscriptSegment', sourceKey: 'app.activity.source.import' },
  { id: 'p5', timestamp: '2026-05-26 13:45:29', descriptionKey: 'annotation.provenance.events.autoLidCompleted', sourceKey: 'app.activity.source.autoLid' },
];

export function useProvenanceLog(): ProvenanceEvent[] {
  const { t } = useTranslation();
  return MOCK_EVENTS.map((event) => ({
    id: event.id,
    timestamp: event.timestamp,
    description: t(event.descriptionKey),
    source: t(event.sourceKey),
  }));
}
