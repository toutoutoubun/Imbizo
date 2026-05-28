export interface ProvenanceEvent {
  id: string;
  timestamp: string;
  description: string;
  source: 'Manual override' | 'Auto-LID' | 'Import' | 'Bulk edit' | 'Manual annotation';
}

const MOCK_EVENTS: ProvenanceEvent[] = [
  { id: 'p1', timestamp: '2026-05-26 14:32:15', description: 'Changed token #6 language from English to isiZulu', source: 'Manual override' },
  { id: 'p2', timestamp: '2026-05-26 14:28:03', description: 'Added concord link candidate for i-laptop', source: 'Manual annotation' },
  { id: 'p3', timestamp: '2026-05-26 14:21:47', description: 'Confirmed English proper noun trigger', source: 'Manual annotation' },
  { id: 'p4', timestamp: '2026-05-26 13:58:12', description: 'Imported transcript segment 15 from ELAN', source: 'Import' },
  { id: 'p5', timestamp: '2026-05-26 13:45:29', description: 'Auto-LID completed for segment 15', source: 'Auto-LID' },
];

export function useProvenanceLog(): ProvenanceEvent[] {
  return MOCK_EVENTS;
}
