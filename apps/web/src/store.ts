import { create } from 'zustand';

import { DEFAULT_LANGUAGE, type Language } from './i18n';

/**
 * Connection state is deliberately explicit about not knowing anything yet.
 * `disconnected` is a real state the UI renders, not a placeholder to fill with
 * plausible-looking numbers.
 */
export type ConnectionState = 'disconnected' | 'connecting' | 'live';

interface AppState {
  language: Language;
  connection: ConnectionState;
  /** Why we are not connected, when we know. Shown to the user verbatim. */
  problem: string | null;
  setLanguage: (language: Language) => void;
  setConnection: (connection: ConnectionState, problem?: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  language: DEFAULT_LANGUAGE,
  connection: 'disconnected',
  problem: null,
  setLanguage: (language) => set({ language }),
  setConnection: (connection, problem = null) => set({ connection, problem }),
}));
