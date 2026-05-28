import { useCallback, useMemo, useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Token } from './ui/Token';
import type { FourMType, HighlightMode, SwitchType, TokenLanguage, TriggerRole } from './ui/Token';
import { Input } from './ui/Input';
import { Select } from './ui/Select';
import { Button } from './ui/Button';
import { ProvenanceLogStrip } from './ProvenanceLogStrip';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import {
  Blend,
  GitBranch,
  Languages,
  Pause,
  Play,
  SkipBack,
  SkipForward,
  Target,
  TrendingUp,
  Type,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface ConcordLink {
  id: string;
  labelKey: string;
  candidateTokenIds: string[];
}

interface IntegrationComponents {
  classPrefix: number;
  concordLink: number;
  inflection: number;
  frequency: number;
}

interface TokenData {
  id: string;
  text: string;
  language: TokenLanguage;
  glyph: string;
  isAuto: boolean;
  matrixLanguage: TokenLanguage | '';
  embeddedLanguage: TokenLanguage | '';
  switchType: SwitchType;
  fourMType: FourMType;
  triggerRole: TriggerRole;
  mixedCodeVariety: string | null;
  integrationScore: number | null;
  integrationComponents: IntegrationComponents;
  nounClass: string;
  concordLinks: ConcordLink[];
  userTags: string[];
  memo: string;
  confidence: number;
}

interface HighlightModeOption {
  id: HighlightMode;
  label: string;
  icon: LucideIcon;
}

const STORAGE_PANE_WIDTH = 'imbizoCS.annotationPaneWidth';

// Review fixture only: all linguistic content below is illustrative and fictional.
const initialTokens: TokenData[] = [
  {
    id: '1',
    text: 'Yebo',
    language: 'isizulu',
    glyph: '■',
    isAuto: false,
    matrixLanguage: 'isizulu',
    embeddedLanguage: '',
    switchType: 'none',
    fourMType: 'content',
    triggerRole: 'none',
    mixedCodeVariety: null,
    integrationScore: null,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0, frequency: 0 },
    nounClass: '',
    concordLinks: [],
    userTags: ['greeting'],
    memo: 'Fictional opening token for UI review.',
    confidence: 0.91,
  },
  {
    id: '2',
    text: 'I',
    language: 'english',
    glyph: '●',
    isAuto: true,
    matrixLanguage: 'isizulu',
    embeddedLanguage: 'english',
    switchType: 'intra',
    fourMType: 'content',
    triggerRole: 'triggered',
    mixedCodeVariety: null,
    integrationScore: 0.12,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0, frequency: 0.12 },
    nounClass: '',
    concordLinks: [],
    userTags: [],
    memo: '',
    confidence: 0.78,
  },
  {
    id: '3',
    text: 'need',
    language: 'english',
    glyph: '●',
    isAuto: true,
    matrixLanguage: 'isizulu',
    embeddedLanguage: 'english',
    switchType: 'none',
    fourMType: 'content',
    triggerRole: 'none',
    mixedCodeVariety: null,
    integrationScore: 0.18,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0.1, frequency: 0.08 },
    nounClass: '',
    concordLinks: [],
    userTags: [],
    memo: '',
    confidence: 0.82,
  },
  {
    id: '4',
    text: 'to',
    language: 'english',
    glyph: '●',
    isAuto: true,
    matrixLanguage: 'isizulu',
    embeddedLanguage: 'english',
    switchType: 'none',
    fourMType: 'early_system',
    triggerRole: 'none',
    mixedCodeVariety: null,
    integrationScore: 0.21,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0.09, frequency: 0.12 },
    nounClass: '',
    concordLinks: [],
    userTags: [],
    memo: '',
    confidence: 0.74,
  },
  {
    id: '5',
    text: 'buy',
    language: 'english',
    glyph: '●',
    isAuto: true,
    matrixLanguage: 'isizulu',
    embeddedLanguage: 'english',
    switchType: 'none',
    fourMType: 'content',
    triggerRole: 'none',
    mixedCodeVariety: null,
    integrationScore: 0.16,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0.06, frequency: 0.1 },
    nounClass: '',
    concordLinks: [],
    userTags: [],
    memo: '',
    confidence: 0.8,
  },
  {
    id: '6',
    text: 'i-laptop',
    language: 'isizulu',
    glyph: '■',
    isAuto: true,
    matrixLanguage: 'isizulu',
    embeddedLanguage: 'english',
    switchType: 'intra',
    fourMType: 'content',
    triggerRole: 'trigger',
    mixedCodeVariety: 'tsotsitaal',
    integrationScore: 0.742,
    integrationComponents: { classPrefix: 0.35, concordLink: 0.21, inflection: 0.12, frequency: 0.062 },
    nounClass: '9',
    concordLinks: [
      { id: 'c1', labelKey: 'annotation.concord.class9PrefixCandidate', candidateTokenIds: ['6', '9'] },
      { id: 'c2', labelKey: 'annotation.concord.embeddedEnglishStemCandidate', candidateTokenIds: ['2', '3', '4', '5', '6'] },
    ],
    userTags: ['loanword', 'device'],
    memo: 'Fictional example showing integration-score controls.',
    confidence: 0.87,
  },
  {
    id: '7',
    text: 'for',
    language: 'english',
    glyph: '●',
    isAuto: true,
    matrixLanguage: 'isizulu',
    embeddedLanguage: 'english',
    switchType: 'none',
    fourMType: 'bridge_late',
    triggerRole: 'none',
    mixedCodeVariety: null,
    integrationScore: 0.2,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0.08, frequency: 0.12 },
    nounClass: '',
    concordLinks: [],
    userTags: [],
    memo: '',
    confidence: 0.76,
  },
  {
    id: '8',
    text: 'my',
    language: 'english',
    glyph: '●',
    isAuto: true,
    matrixLanguage: 'isizulu',
    embeddedLanguage: 'english',
    switchType: 'none',
    fourMType: 'outsider_late',
    triggerRole: 'none',
    mixedCodeVariety: null,
    integrationScore: 0.25,
    integrationComponents: { classPrefix: 0, concordLink: 0.05, inflection: 0.08, frequency: 0.12 },
    nounClass: '',
    concordLinks: [],
    userTags: [],
    memo: '',
    confidence: 0.72,
  },
  {
    id: '9',
    text: 'umfana',
    language: 'isizulu',
    glyph: '■',
    isAuto: false,
    matrixLanguage: 'isizulu',
    embeddedLanguage: '',
    switchType: 'none',
    fourMType: 'content',
    triggerRole: 'none',
    mixedCodeVariety: null,
    integrationScore: null,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0, frequency: 0 },
    nounClass: '1',
    concordLinks: [{ id: 'c3', labelKey: 'annotation.concord.class1NounCandidate', candidateTokenIds: ['9'] }],
    userTags: ['kinship'],
    memo: '',
    confidence: 0.96,
  },
  {
    id: '10',
    text: '.',
    language: 'unknown',
    glyph: '◐',
    isAuto: true,
    matrixLanguage: '',
    embeddedLanguage: '',
    switchType: 'none',
    fourMType: 'unassigned',
    triggerRole: 'none',
    mixedCodeVariety: null,
    integrationScore: null,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0, frequency: 0 },
    nounClass: '',
    concordLinks: [],
    userTags: [],
    memo: '',
    confidence: 0.64,
  },
  {
    id: '11',
    text: 'He',
    language: 'english',
    glyph: '●',
    isAuto: true,
    matrixLanguage: 'english',
    embeddedLanguage: '',
    switchType: 'inter',
    fourMType: 'content',
    triggerRole: 'none',
    mixedCodeVariety: null,
    integrationScore: 0.11,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0.04, frequency: 0.07 },
    nounClass: '',
    concordLinks: [],
    userTags: [],
    memo: '',
    confidence: 0.84,
  },
  {
    id: '12',
    text: 'needs',
    language: 'english',
    glyph: '●',
    isAuto: true,
    matrixLanguage: 'english',
    embeddedLanguage: '',
    switchType: 'none',
    fourMType: 'content',
    triggerRole: 'none',
    mixedCodeVariety: null,
    integrationScore: 0.17,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0.09, frequency: 0.08 },
    nounClass: '',
    concordLinks: [],
    userTags: [],
    memo: '',
    confidence: 0.83,
  },
  {
    id: '13',
    text: 'it',
    language: 'english',
    glyph: '●',
    isAuto: true,
    matrixLanguage: 'english',
    embeddedLanguage: '',
    switchType: 'none',
    fourMType: 'content',
    triggerRole: 'none',
    mixedCodeVariety: null,
    integrationScore: 0.1,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0.03, frequency: 0.07 },
    nounClass: '',
    concordLinks: [],
    userTags: [],
    memo: '',
    confidence: 0.79,
  },
  {
    id: '14',
    text: 'for',
    language: 'english',
    glyph: '●',
    isAuto: true,
    matrixLanguage: 'english',
    embeddedLanguage: '',
    switchType: 'none',
    fourMType: 'bridge_late',
    triggerRole: 'none',
    mixedCodeVariety: null,
    integrationScore: 0.19,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0.08, frequency: 0.11 },
    nounClass: '',
    concordLinks: [],
    userTags: [],
    memo: '',
    confidence: 0.76,
  },
  {
    id: '15',
    text: 'school',
    language: 'english',
    glyph: '●',
    isAuto: true,
    matrixLanguage: 'english',
    embeddedLanguage: '',
    switchType: 'none',
    fourMType: 'content',
    triggerRole: 'trigger',
    mixedCodeVariety: null,
    integrationScore: 0.22,
    integrationComponents: { classPrefix: 0, concordLink: 0, inflection: 0.1, frequency: 0.12 },
    nounClass: '',
    concordLinks: [],
    userTags: ['domain:education'],
    memo: '',
    confidence: 0.82,
  },
];

const highlightModes: HighlightModeOption[] = [
  { id: 'language', label: 'annotation.highlight.language', icon: Languages },
  { id: '4m', label: 'annotation.highlight.fourM', icon: Type },
  { id: 'switch', label: 'annotation.highlight.switch', icon: GitBranch },
  { id: 'trigger', label: 'annotation.highlight.trigger', icon: Target },
  { id: 'mixed', label: 'annotation.highlight.mixed', icon: Blend },
  { id: 'integration', label: 'annotation.highlight.integration', icon: TrendingUp },
];

const languageLegend = [
  { nameKey: 'app.languages.english', color: 'bg-lang-english', glyph: '●', code: 'eng' },
  { nameKey: 'app.languages.afrikaans', color: 'bg-lang-afrikaans', glyph: '▲', code: 'afr' },
  { nameKey: 'app.languages.isizulu', color: 'bg-lang-isizulu', glyph: '■', code: 'zul' },
  { nameKey: 'app.languages.isixhosa', color: 'bg-lang-isixhosa', glyph: '◆', code: 'xho' },
  { nameKey: 'app.languages.sesotho', color: 'bg-lang-sesotho', glyph: '★', code: 'sot' },
  { nameKey: 'app.languages.setswana', color: 'bg-lang-setswana', glyph: '✚', code: 'tsn' },
  { nameKey: 'app.languages.other', color: 'bg-lang-other', glyph: '✱', code: 'oth' },
  { nameKey: 'app.languages.unknown', color: 'bg-lang-unknown', glyph: '◐', code: 'unk' },
];

const languageOptionValues: Array<{ value: TokenLanguage | ''; labelKey: string }> = [
  { value: '', labelKey: 'annotation.notSet' },
  { value: 'english', labelKey: 'app.languages.english' },
  { value: 'afrikaans', labelKey: 'app.languages.afrikaans' },
  { value: 'isizulu', labelKey: 'app.languages.isizulu' },
  { value: 'isixhosa', labelKey: 'app.languages.isixhosa' },
  { value: 'sesotho', labelKey: 'app.languages.sesotho' },
  { value: 'setswana', labelKey: 'app.languages.setswana' },
  { value: 'other', labelKey: 'app.languages.other' },
  { value: 'unknown', labelKey: 'app.languages.unknown' },
];

const projectSettings = {
  mixedCodeEnabled: true,
  enabledMixedCodeVarieties: ['tsotsitaal', 'iscamtho', 'kaaps', 'sabela'],
};

const bantuNounClassLanguages: TokenLanguage[] = ['isizulu', 'isixhosa', 'sesotho', 'setswana'];
const waveformHeights = [24, 35, 18, 42, 30, 12, 48, 28, 20, 39, 44, 16, 33, 27, 22, 40, 14, 31, 46, 25];

function readPaneWidth(): number {
  const stored = Number.parseFloat(localStorage.getItem(STORAGE_PANE_WIDTH) ?? '');
  if (Number.isFinite(stored) && stored >= 24 && stored <= 55) {
    return stored;
  }
  return 36;
}

function highlightLabelKey(mode: HighlightMode): string {
  const keys: Record<HighlightMode, string> = {
    language: 'annotation.highlight.language',
    '4m': 'annotation.highlight.fourM',
    switch: 'annotation.highlight.switch',
    trigger: 'annotation.highlight.trigger',
    mixed: 'annotation.highlight.mixed',
    integration: 'annotation.highlight.integration',
  };
  return keys[mode];
}

export function AnnotationEditor() {
  const { t } = useTranslation();
  const [tokens, setTokens] = useState<TokenData[]>(initialTokens);
  const [selectedTokenId, setSelectedTokenId] = useState<string>('6');
  const [selectionAnchorIndex, setSelectionAnchorIndex] = useState<number>(5);
  const [selectionEndIndex, setSelectionEndIndex] = useState<number>(5);
  const [highlightMode, setHighlightMode] = useState<HighlightMode>('language');
  const [isPlaying, setIsPlaying] = useState(false);
  const [candidateTokenIds, setCandidateTokenIds] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');
  const [showIntegrationDetails, setShowIntegrationDetails] = useState(false);
  const [paneWidth, setPaneWidth] = useState(readPaneWidth);
  const languageSelectRef = useRef<HTMLSelectElement | null>(null);
  const fourMSelectRef = useRef<HTMLSelectElement | null>(null);
  const undoStackRef = useRef<TokenData[][]>([]);
  const redoStackRef = useRef<TokenData[][]>([]);
  const languageOptions = useMemo(
    () => languageOptionValues.map((option) => ({ value: option.value, label: t(option.labelKey) })),
    [t]
  );
  const fourMOptions = useMemo(
    () =>
      (['unassigned', 'content', 'early_system', 'bridge_late', 'outsider_late'] as FourMType[]).map((value) => ({
        value,
        label: t(`annotation.fourMTypes.${value}`),
      })),
    [t]
  );

  const selectedToken = tokens.find((token) => token.id === selectedTokenId) ?? tokens[0];
  const selectedIndex = Math.max(tokens.findIndex((token) => token.id === selectedTokenId), 0);
  const selectedIds = useMemo(() => {
    const min = Math.min(selectionAnchorIndex, selectionEndIndex);
    const max = Math.max(selectionAnchorIndex, selectionEndIndex);
    return new Set(tokens.slice(min, max + 1).map((token) => token.id));
  }, [selectionAnchorIndex, selectionEndIndex, tokens]);

  const focusTokenAt = useCallback(
    (index: number, extendSelection = false) => {
      const bounded = Math.max(0, Math.min(tokens.length - 1, index));
      const token = tokens[bounded];
      setSelectedTokenId(token.id);
      if (extendSelection) {
        setSelectionEndIndex(bounded);
      } else {
        setSelectionAnchorIndex(bounded);
        setSelectionEndIndex(bounded);
      }
      requestAnimationFrame(() => {
        document.querySelector<HTMLButtonElement>(`[data-token-id="${token.id}"]`)?.focus();
      });
    },
    [tokens]
  );

  const updateSelectedToken = useCallback(
    (patch: Partial<TokenData>) => {
      undoStackRef.current = [...undoStackRef.current.slice(-49), tokens];
      redoStackRef.current = [];
      setTokens(tokens.map((token) => (selectedIds.has(token.id) ? { ...token, ...patch } : token)));
    },
    [selectedIds, tokens]
  );

  const undo = useCallback(() => {
    const previous = undoStackRef.current.pop();
    if (!previous) {
      return;
    }
    redoStackRef.current = [tokens, ...redoStackRef.current].slice(0, 50);
    setTokens(previous);
  }, [tokens]);

  const redo = useCallback(() => {
    const next = redoStackRef.current.shift();
    if (!next) {
      return;
    }
    undoStackRef.current = [...undoStackRef.current.slice(-49), tokens];
    setTokens(next);
  }, [tokens]);

  const jumpToBoundary = useCallback(
    (direction: -1 | 1, kind: 'language' | 'switch') => {
      for (let index = selectedIndex + direction; index >= 0 && index < tokens.length; index += direction) {
        const previous = tokens[index - 1];
        const current = tokens[index];
        const isBoundary =
          kind === 'language'
            ? previous !== undefined && previous.language !== current.language
            : current.switchType !== 'none';
        if (isBoundary) {
          focusTokenAt(index);
          return;
        }
      }
    },
    [focusTokenAt, selectedIndex, tokens]
  );

  const toggleTriggerRole = useCallback(() => {
    const next: TriggerRole = selectedToken.triggerRole === 'trigger' ? 'none' : 'trigger';
    updateSelectedToken({ triggerRole: next });
  }, [selectedToken.triggerRole, updateSelectedToken]);

  useKeyboardShortcuts({
    onArrowLeft: () => focusTokenAt(selectedIndex - 1),
    onArrowRight: () => focusTokenAt(selectedIndex + 1),
    onShiftArrowLeft: () => focusTokenAt(selectedIndex - 1, true),
    onShiftArrowRight: () => focusTokenAt(selectedIndex + 1, true),
    onAltArrowLeft: () => jumpToBoundary(-1, 'language'),
    onAltArrowRight: () => jumpToBoundary(1, 'language'),
    onCtrlArrowLeft: () => jumpToBoundary(-1, 'switch'),
    onCtrlArrowRight: () => jumpToBoundary(1, 'switch'),
    onLanguagePicker: () => languageSelectRef.current?.focus(),
    onFourMPicker: () => fourMSelectRef.current?.focus(),
    onTogglePlayback: () => setIsPlaying((value) => !value),
    onToggleTrigger: toggleTriggerRole,
    onUndo: undo,
    onRedo: redo,
    onEscape: () => {
      setCandidateTokenIds([]);
      setSelectionAnchorIndex(selectedIndex);
      setSelectionEndIndex(selectedIndex);
    },
    onCycleHighlightMode: () => {
      const current = highlightModes.findIndex((mode) => mode.id === highlightMode);
      setHighlightMode(highlightModes[(current + 1) % highlightModes.length].id);
    },
    onMode1: () => setHighlightMode('language'),
    onMode2: () => setHighlightMode('4m'),
    onMode3: () => setHighlightMode('switch'),
    onMode4: () => setHighlightMode('trigger'),
    onMode5: () => setHighlightMode('mixed'),
    onMode6: () => setHighlightMode('integration'),
  });

  const addTag = () => {
    const trimmed = newTag.trim();
    if (!trimmed || selectedToken.userTags.includes(trimmed)) {
      setNewTag('');
      return;
    }
    updateSelectedToken({ userTags: [...selectedToken.userTags, trimmed] });
    setNewTag('');
  };

  const removeTag = (tag: string) => {
    updateSelectedToken({ userTags: selectedToken.userTags.filter((existing) => existing !== tag) });
  };

  const handleTagKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      addTag();
      return;
    }
    if (event.key === 'Backspace' && newTag === '' && selectedToken.userTags.length > 0) {
      event.preventDefault();
      removeTag(selectedToken.userTags[selectedToken.userTags.length - 1]);
    }
  };

  return (
    <div className="flex flex-col h-full bg-background">
      <div className="h-[120px] border-b border-border bg-card px-4 py-3">
        <div className="flex items-center gap-3 mb-2">
          <Button size="sm" variant="ghost" onClick={() => setIsPlaying((value) => !value)}>
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </Button>
          <Button size="sm" variant="ghost">
            <SkipBack className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="ghost">
            <SkipForward className="w-4 h-4" />
          </Button>
          <div className="flex-1 h-1 bg-subtle-bg rounded-full">
            <div className="h-full w-1/3 bg-primary rounded-full" />
          </div>
          <span className="text-[12px] text-secondary-text font-mono">00:12 / 02:34</span>
          <Button size="sm" variant="ghost">
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="ghost">
            <ZoomOut className="w-4 h-4" />
          </Button>
        </div>
        <div className="h-16 bg-subtle-bg rounded-sm border border-border flex items-center justify-center">
          <svg className="w-full h-full" viewBox="0 0 800 64" role="img" aria-label={t('annotation.waveformPreview')}>
            {Array.from({ length: 100 }).map((_, index) => {
              const height = waveformHeights[index % waveformHeights.length];
              return (
                <rect
                  key={index}
                  x={index * 8}
                  y={(64 - height) / 2}
                  width="6"
                  height={height}
                  fill="var(--secondary-text)"
                  opacity="0.5"
                />
              );
            })}
            <line x1="266" y1="0" x2="266" y2="64" stroke="var(--primary)" strokeWidth="2" />
          </svg>
        </div>
      </div>

      <PanelGroup direction="horizontal" className="flex-1 overflow-hidden">
        <Panel defaultSize={100 - paneWidth} minSize={45}>
          <main className="h-full overflow-auto p-6" aria-label={t('annotation.transcriptTokens')}>
            <div className="max-w-3xl">
              <div className="flex flex-wrap gap-1.5 leading-loose">
                {tokens.map((token, index) => (
                  <Token
                    key={token.id}
                    id={token.id}
                    text={token.text}
                    language={token.language}
                    glyph={token.glyph}
                    highlightMode={highlightMode}
                    isAuto={token.isAuto}
                    isSelected={selectedIds.has(token.id)}
                    isFocused={selectedTokenId === token.id}
                    matrixLanguage={token.matrixLanguage || null}
                    embeddedLanguage={token.embeddedLanguage || null}
                    switchType={token.switchType}
                    fourMType={token.fourMType}
                    triggerRole={token.triggerRole}
                    mixedCodeVariety={token.mixedCodeVariety}
                    integrationScore={token.integrationScore}
                    isCandidate={candidateTokenIds.includes(token.id)}
                    onClick={() => {
                      setSelectedTokenId(token.id);
                      setSelectionAnchorIndex(index);
                      setSelectionEndIndex(index);
                    }}
                  />
                ))}
              </div>
            </div>
          </main>
        </Panel>

        <PanelResizeHandle
          className="w-1 border-l border-r border-border bg-subtle-bg hover:bg-primary/20 focus:outline focus:outline-2 focus:outline-primary"
          aria-label={t('annotation.resizePane')}
        />

        <Panel
          defaultSize={paneWidth}
          minSize={24}
          maxSize={55}
          onResize={(size) => {
            setPaneWidth(size);
            localStorage.setItem(STORAGE_PANE_WIDTH, String(size));
          }}
        >
          <aside className="h-full border-l border-border overflow-auto bg-card" aria-label={t('annotation.paneLabel')}>
            {selectedToken ? (
              <div className="p-6 space-y-4">
                <div>
                  <h3 className="text-[16px] mb-4">{t('annotation.title')}</h3>
                  <div className="text-[12px] text-secondary-text mb-4">
                    {t('annotation.tokenId', { id: selectedToken.id })}
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="text-[12px] text-secondary-text mb-1">{t('annotation.surfaceForm')}</div>
                    <div className="text-[14px] font-mono">{selectedToken.text}</div>
                  </div>

                  <Select
                    ref={languageSelectRef}
                    label={t('annotation.fields.language')}
                    options={languageOptions.filter((option) => option.value !== '')}
                    value={selectedToken.language}
                    onChange={(event) => updateSelectedToken({ language: event.target.value as TokenLanguage })}
                  />

                  {selectedToken.isAuto && (
                    <div className="flex items-center gap-2 text-[12px] text-secondary-text">
                      <span className="px-2 py-0.5 bg-muted rounded-sm">{t('annotation.badges.auto')}</span>
                      <Button size="sm" variant="ghost" onClick={() => updateSelectedToken({ isAuto: false })}>
                        {t('annotation.actions.override')}
                      </Button>
                    </div>
                  )}

                  <Select
                    label={t('annotation.fields.matrixLanguage')}
                    options={languageOptions}
                    value={selectedToken.matrixLanguage}
                    onChange={(event) => updateSelectedToken({ matrixLanguage: event.target.value as TokenLanguage | '' })}
                  />

                  <Select
                    label={t('annotation.fields.embeddedLanguage')}
                    options={languageOptions}
                    value={selectedToken.embeddedLanguage}
                    onChange={(event) => updateSelectedToken({ embeddedLanguage: event.target.value as TokenLanguage | '' })}
                  />

                  <fieldset>
                    <legend className="text-[12px] text-secondary-text mb-1 block">{t('annotation.fields.switchType')}</legend>
                    <div className="space-y-2">
                      {[
                        ['intra', 'annotation.switchTypes.intra'],
                        ['inter', 'annotation.switchTypes.inter'],
                        ['extra', 'annotation.switchTypes.extra'],
                        ['none', 'annotation.switchTypes.none'],
                      ].map(([value, label]) => (
                        <label key={value} className="flex items-center gap-2">
                          <input
                            type="radio"
                            name="switchType"
                            value={value}
                            checked={selectedToken.switchType === value}
                            onChange={() => updateSelectedToken({ switchType: value as SwitchType })}
                            className="w-4 h-4"
                          />
                          <span className="text-[14px]">{t(label)}</span>
                        </label>
                      ))}
                    </div>
                  </fieldset>

                  <Select
                    ref={fourMSelectRef}
                    label={t('annotation.fields.fourMType')}
                    options={fourMOptions}
                    value={selectedToken.fourMType}
                    onChange={(event) => updateSelectedToken({ fourMType: event.target.value as FourMType })}
                  />

                  {bantuNounClassLanguages.includes(selectedToken.language) && (
                    <Input
                      label={t('annotation.fields.nounClass')}
                      type="number"
                      placeholder={t('annotation.nounClassExample')}
                      value={selectedToken.nounClass}
                      onChange={(event) => updateSelectedToken({ nounClass: event.target.value })}
                    />
                  )}

                  <section className="space-y-2">
                    <div className="text-[12px] text-secondary-text">{t('annotation.fields.concordLinks')}</div>
                    {selectedToken.concordLinks.length > 0 ? (
                      <div className="space-y-2">
                        {selectedToken.concordLinks.map((link) => (
                          <div key={link.id} className="border border-border rounded-sm p-2">
                            <div className="text-[12px] mb-2">{t(link.labelKey)}</div>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setCandidateTokenIds(link.candidateTokenIds)}
                            >
                              {t('annotation.actions.showCandidates')}
                            </Button>
                          </div>
                        ))}
                        <Button size="sm" variant="ghost" onClick={() => setCandidateTokenIds([])}>
                          {t('annotation.actions.clearCandidates')}
                        </Button>
                      </div>
                    ) : (
                      <p className="text-[12px] text-secondary-text">{t('annotation.empty.noConcordLinks')}</p>
                    )}
                  </section>

                  <fieldset>
                    <legend className="text-[12px] text-secondary-text mb-1 block">{t('annotation.fields.triggerRole')}</legend>
                    <div className="grid grid-cols-3 gap-2">
                      {(['trigger', 'triggered', 'none'] as TriggerRole[]).map((role) => (
                        <label key={role} className="flex items-center gap-2 text-[13px]">
                          <input
                            type="radio"
                            name="triggerRole"
                            value={role}
                            checked={selectedToken.triggerRole === role}
                            onChange={() => updateSelectedToken({ triggerRole: role })}
                          />
                          {t(`annotation.triggerRoles.${role}`)}
                        </label>
                      ))}
                    </div>
                  </fieldset>

                  {projectSettings.mixedCodeEnabled && (
                    <section className="space-y-2">
                      <div className="border border-warning bg-warning/10 rounded-sm p-2 text-[12px] leading-snug">
                        {t('annotation.mixedCodeAdvisory')}
                      </div>
                      <Select
                        label={t('annotation.fields.mixedCodeVariety')}
                        options={[
                          { value: '', label: t('annotation.notSet') },
                          ...projectSettings.enabledMixedCodeVarieties.map((variety) => ({
                            value: variety,
                            label: t(`annotation.mixedVarieties.${variety}`),
                          })),
                        ]}
                        value={selectedToken.mixedCodeVariety ?? ''}
                        onChange={(event) =>
                          updateSelectedToken({ mixedCodeVariety: event.target.value === '' ? null : event.target.value })
                        }
                      />
                    </section>
                  )}

                  <section className="space-y-2">
                    <div className="text-[12px] text-secondary-text">{t('annotation.fields.integrationScore')}</div>
                    <div className="text-[18px] font-mono">
                      {selectedToken.integrationScore === null ? t('annotation.scoreNotComputed') : selectedToken.integrationScore.toFixed(3)}
                    </div>
                    <button
                      type="button"
                      className="text-[12px] text-primary hover:underline focus:outline focus:outline-2 focus:outline-primary"
                      aria-expanded={showIntegrationDetails}
                      onClick={() => setShowIntegrationDetails((value) => !value)}
                    >
                      {t('annotation.actions.howComputed')}
                    </button>
                    {showIntegrationDetails && (
                      <div className="border border-border rounded-sm p-3 text-[12px] space-y-1 bg-background">
                        <div className="font-mono">{t('annotation.integration.formula')}</div>
                        <div>{t('annotation.integration.classPrefix')}: {selectedToken.integrationComponents.classPrefix.toFixed(3)}</div>
                        <div>{t('annotation.integration.concordLink')}: {selectedToken.integrationComponents.concordLink.toFixed(3)}</div>
                        <div>{t('annotation.integration.inflection')}: {selectedToken.integrationComponents.inflection.toFixed(3)}</div>
                        <div>{t('annotation.integration.frequency')}: {selectedToken.integrationComponents.frequency.toFixed(3)}</div>
                      </div>
                    )}
                  </section>

                  <section className="space-y-2">
                    <div className="text-[12px] text-secondary-text">{t('annotation.fields.userTags')}</div>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedToken.userTags.map((tag) => (
                        <button
                          key={tag}
                          type="button"
                          className="px-2 py-0.5 bg-muted rounded-sm text-[11px] hover:bg-subtle-bg"
                          aria-label={t('annotation.removeTag', { tag })}
                          onClick={() => removeTag(tag)}
                        >
                          {tag} ×
                        </button>
                      ))}
                    </div>
                    <Input
                      aria-label={t('annotation.addUserTag')}
                      placeholder={t('annotation.tagPlaceholder')}
                      value={newTag}
                      onChange={(event) => setNewTag(event.target.value)}
                      onKeyDown={handleTagKeyDown}
                    />
                  </section>

                  <div>
                    <label className="text-[12px] text-secondary-text mb-2 block" htmlFor="researcher-memo">
                      {t('annotation.fields.researcherMemo')}
                    </label>
                    <textarea
                      id="researcher-memo"
                      className="w-full px-3 py-2 bg-input-background border border-input rounded-sm text-[14px] min-h-[80px] focus:outline focus:outline-2 focus:outline-primary"
                      placeholder={t('annotation.memoPlaceholder')}
                      value={selectedToken.memo}
                      onChange={(event) => updateSelectedToken({ memo: event.target.value })}
                    />
                  </div>

                  <div>
                    <label className="text-[12px] text-secondary-text mb-1 block">{t('annotation.fields.confidence')}</label>
                    <div className="flex gap-1" aria-label={`${t('annotation.fields.confidence')} ${selectedToken.confidence.toFixed(2)}`}>
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          className={`text-[20px] transition-colors ${
                            star <= Math.round(selectedToken.confidence * 5) ? 'text-primary' : 'text-muted'
                          }`}
                          onClick={() => updateSelectedToken({ confidence: star / 5 })}
                        >
                          ★
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center text-secondary-text">{t('annotation.selectPrompt')}</div>
            )}
          </aside>
        </Panel>
      </PanelGroup>

      <ProvenanceLogStrip />

      <div className="h-24 border-t border-border bg-card px-6 py-3">
        <div className="flex items-center justify-between mb-3">
          <div className="flex gap-1">
            {highlightModes.map((mode) => {
              const Icon = mode.icon;
              return (
                <button
                  key={mode.id}
                  type="button"
                  onClick={() => setHighlightMode(mode.id)}
                  aria-pressed={highlightMode === mode.id}
                  className={`px-3 py-1.5 flex items-center gap-2 text-[12px] rounded-sm border-b-2 transition-colors focus:outline focus:outline-2 focus:outline-primary ${
                    highlightMode === mode.id ? 'border-primary bg-primary/10 text-foreground' : 'border-transparent hover:bg-subtle-bg'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {t(highlightLabelKey(mode.id))}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex flex-wrap gap-4 text-[11px]">
            {languageLegend.map((lang) => (
              <div key={lang.code} className="flex items-center gap-1.5">
                <div className={`w-3 h-3 ${lang.color} rounded-sm`} />
                <span className="font-mono">{lang.glyph}</span>
                <span className="text-secondary-text">{t(lang.nameKey)}</span>
                <span className="font-mono text-secondary-text">{lang.code}</span>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-4 text-[11px] text-secondary-text">
            <span>{t('annotation.currentMode')}: {t(highlightLabelKey(highlightMode))}</span>
            <span>{t('app.status.tokens', { count: tokens.length })}</span>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 bg-success rounded-full" />
              <span>{t('app.status.offline')}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
