import type { KeyboardEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { clsx } from 'clsx';

export type TokenLanguage =
  | 'english'
  | 'afrikaans'
  | 'isizulu'
  | 'isixhosa'
  | 'sesotho'
  | 'setswana'
  | 'other'
  | 'unknown';

export type HighlightMode = 'language' | '4m' | 'switch' | 'trigger' | 'mixed' | 'integration';
export type SwitchType = 'intra' | 'inter' | 'extra' | 'none';
export type FourMType = 'content' | 'early_system' | 'bridge_late' | 'outsider_late' | 'unassigned';
export type TriggerRole = 'trigger' | 'triggered' | 'none';

interface TokenProps {
  id?: string;
  text: string;
  language: TokenLanguage;
  glyph: string;
  highlightMode: HighlightMode;
  isSelected?: boolean;
  isFocused?: boolean;
  isAuto?: boolean;
  hasConflict?: boolean;
  matrixLanguage?: string | null;
  embeddedLanguage?: string | null;
  switchType?: SwitchType;
  fourMType?: FourMType;
  triggerRole?: TriggerRole;
  mixedCodeVariety?: string | null;
  integrationScore?: number | null;
  isCandidate?: boolean;
  onClick?: () => void;
  onDoubleClick?: () => void;
}

const languageColors: Record<TokenLanguage, { background: string; border: string; text: string }> = {
  english: { background: 'bg-lang-english/10', border: 'border-lang-english', text: 'text-lang-english' },
  afrikaans: { background: 'bg-lang-afrikaans/10', border: 'border-lang-afrikaans', text: 'text-lang-afrikaans' },
  isizulu: { background: 'bg-lang-isizulu/10', border: 'border-lang-isizulu', text: 'text-lang-isizulu' },
  isixhosa: { background: 'bg-lang-isixhosa/10', border: 'border-lang-isixhosa', text: 'text-lang-isixhosa' },
  sesotho: { background: 'bg-lang-sesotho/10', border: 'border-lang-sesotho', text: 'text-lang-sesotho' },
  setswana: { background: 'bg-lang-setswana/10', border: 'border-lang-setswana', text: 'text-lang-setswana' },
  other: { background: 'bg-lang-other/10', border: 'border-lang-other', text: 'text-lang-other' },
  unknown: { background: 'bg-lang-unknown/10', border: 'border-lang-unknown', text: 'text-lang-unknown' },
};

function fourMDecoration(fourMType: FourMType): string {
  switch (fourMType) {
    case 'early_system':
      return 'underline decoration-solid underline-offset-4';
    case 'bridge_late':
      return 'underline decoration-double underline-offset-4';
    case 'outsider_late':
      return 'underline decoration-wavy underline-offset-4';
    default:
      return '';
  }
}

function switchBorder(switchType: SwitchType): string {
  switch (switchType) {
    case 'inter':
      return 'border-dashed';
    case 'extra':
      return 'border-dotted';
    default:
      return 'border-solid';
  }
}

function integrationOpacity(score: number | null | undefined): string {
  if (score === null || score === undefined) {
    return 'opacity-100';
  }
  if (score >= 0.7) {
    return 'opacity-100';
  }
  if (score >= 0.3) {
    return 'opacity-70';
  }
  return 'opacity-40';
}

function buildAriaLabel(props: TokenProps, t: (key: string, options?: Record<string, string>) => string): string {
  return [
    `${props.text}, ${t('annotation.tokenAria.language', { language: props.language })}`,
    props.matrixLanguage ? t('annotation.tokenAria.matrix', { language: props.matrixLanguage }) : null,
    props.fourMType && props.fourMType !== 'unassigned' ? t('annotation.tokenAria.fourM', { type: props.fourMType }) : null,
    props.switchType && props.switchType !== 'none' ? t('annotation.tokenAria.switch', { type: props.switchType }) : null,
    props.triggerRole && props.triggerRole !== 'none' ? t(`annotation.triggerRoles.${props.triggerRole}`) : null,
    props.isAuto ? t('annotation.tokenAria.autoDetected') : t('annotation.tokenAria.manuallySet'),
    props.hasConflict ? t('annotation.tokenAria.hasConflict') : null,
  ]
    .filter(Boolean)
    .join(', ');
}

export function Token(props: TokenProps) {
  const { t } = useTranslation();
  const {
    text,
    language,
    glyph,
    highlightMode,
    isSelected = false,
    isFocused = false,
    isAuto = false,
    hasConflict = false,
    switchType = 'none',
    fourMType = 'unassigned',
    triggerRole = 'none',
    mixedCodeVariety = null,
    integrationScore = null,
    isCandidate = false,
    onClick,
    onDoubleClick,
  } = props;
  const color = languageColors[language];
  const showMixedHatching = highlightMode === 'mixed' && mixedCodeVariety;
  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onClick?.();
    }
  };

  return (
    <button
      type="button"
      data-token-id={props.id}
      data-highlight-mode={highlightMode}
      data-trigger-role={triggerRole}
      data-mixed-code-variety={mixedCodeVariety ?? undefined}
      aria-label={buildAriaLabel(props, t)}
      aria-pressed={isSelected}
      className={clsx(
        'inline-flex items-center relative px-1.5 h-7 border rounded-sm',
        'text-[14px] text-foreground select-none cursor-pointer',
        'transition-colors duration-100 text-left',
        'hover:bg-subtle-bg',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2',
        color.background,
        color.border,
        highlightMode === '4m' && fourMDecoration(fourMType),
        highlightMode === 'switch' && switchBorder(switchType),
        highlightMode === 'integration' && integrationOpacity(integrationScore),
        isFocused && 'outline outline-2 outline-primary outline-offset-2',
        isSelected && 'bg-primary/10',
        hasConflict && 'border-warning',
        isCandidate && 'ring-2 ring-secondary ring-offset-1 ring-offset-background',
        showMixedHatching &&
          'bg-[repeating-linear-gradient(135deg,transparent_0,transparent_4px,var(--muted)_4px,var(--muted)_6px)]'
      )}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
      onKeyDown={handleKeyDown}
    >
      {highlightMode === 'trigger' && triggerRole === 'triggered' && (
        <span className="mr-1 text-[10px]" aria-hidden="true">←</span>
      )}
      <span>{text}</span>
      {highlightMode === 'trigger' && triggerRole === 'trigger' && (
        <span className="ml-1 text-[10px]" aria-hidden="true">↦</span>
      )}
      <span className={clsx('absolute top-0.5 right-0.5 text-[10px] leading-none', color.text)} aria-hidden="true">
        {glyph}
      </span>
      {isAuto && !hasConflict && (
        <span className="absolute bottom-0.5 left-0.5 text-[9px] leading-none text-secondary-text" aria-hidden="true">
          {t('annotation.badges.auto')}
        </span>
      )}
      {hasConflict && (
        <span className="absolute bottom-0.5 left-0.5 text-[10px] leading-none" aria-hidden="true">
          ⚠
        </span>
      )}
    </button>
  );
}
