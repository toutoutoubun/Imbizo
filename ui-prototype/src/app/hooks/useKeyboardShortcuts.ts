import { useEffect, useLayoutEffect, useRef } from 'react';

export interface KeyboardShortcutHandlers {
  onArrowLeft?: () => void;
  onArrowRight?: () => void;
  onShiftArrowLeft?: () => void;
  onShiftArrowRight?: () => void;
  onAltArrowLeft?: () => void;
  onAltArrowRight?: () => void;
  onCtrlArrowLeft?: () => void;
  onCtrlArrowRight?: () => void;
  onLanguagePicker?: () => void;
  onFourMPicker?: () => void;
  onTogglePlayback?: () => void;
  onToggleTrigger?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onEscape?: () => void;
  onCycleHighlightMode?: () => void;
  onMode1?: () => void;
  onMode2?: () => void;
  onMode3?: () => void;
  onMode4?: () => void;
  onMode5?: () => void;
  onMode6?: () => void;
}

type HandlerKey = keyof KeyboardShortcutHandlers;

export const KEYBOARD_DEFAULTS: Record<string, HandlerKey> = {
  ArrowLeft: 'onArrowLeft',
  ArrowRight: 'onArrowRight',
  'Shift+ArrowLeft': 'onShiftArrowLeft',
  'Shift+ArrowRight': 'onShiftArrowRight',
  'Alt+ArrowLeft': 'onAltArrowLeft',
  'Alt+ArrowRight': 'onAltArrowRight',
  'Mod+ArrowLeft': 'onCtrlArrowLeft',
  'Mod+ArrowRight': 'onCtrlArrowRight',
  l: 'onLanguagePicker',
  m: 'onFourMPicker',
  ' ': 'onTogglePlayback',
  t: 'onToggleTrigger',
  'Mod+z': 'onUndo',
  'Mod+Shift+z': 'onRedo',
  Escape: 'onEscape',
  'Mod+/': 'onCycleHighlightMode',
  'Mod+1': 'onMode1',
  'Mod+2': 'onMode2',
  'Mod+3': 'onMode3',
  'Mod+4': 'onMode4',
  'Mod+5': 'onMode5',
  'Mod+6': 'onMode6',
};

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) {
    return false;
  }
  const tag = target.tagName.toLowerCase();
  return tag === 'input' || tag === 'textarea' || target.isContentEditable || target.closest('[contenteditable="true"]') !== null;
}

function keyForEvent(event: KeyboardEvent): string {
  const mod = event.ctrlKey || event.metaKey;
  const parts: string[] = [];
  if (mod) {
    parts.push('Mod');
  }
  if (event.shiftKey) {
    parts.push('Shift');
  }
  if (event.altKey) {
    parts.push('Alt');
  }
  parts.push(event.key.length === 1 ? event.key.toLowerCase() : event.key);
  return parts.join('+');
}

export function useKeyboardShortcuts(handlers: KeyboardShortcutHandlers): void {
  const handlersRef = useRef(handlers);

  useLayoutEffect(() => {
    handlersRef.current = handlers;
  }, [handlers]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (isEditableTarget(event.target)) {
        return;
      }
      const handlerKey = KEYBOARD_DEFAULTS[keyForEvent(event)] ?? KEYBOARD_DEFAULTS[event.key];
      if (!handlerKey) {
        return;
      }
      const handler = handlersRef.current[handlerKey];
      if (!handler) {
        return;
      }
      event.preventDefault();
      handler();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, []);
}
