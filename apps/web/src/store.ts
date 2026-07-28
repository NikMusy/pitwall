import { create } from 'zustand';

import { DEFAULT_LANGUAGE, type Language } from './i18n';
import type { SampleRow } from './telemetry';

/**
 * Connection state is deliberately explicit about not knowing anything yet.
 * `disconnected` is a real state the UI renders, not a placeholder to fill with
 * plausible-looking numbers.
 */
export type ConnectionState = 'disconnected' | 'connecting' | 'live';

/** Enough history for a live strip chart without unbounded growth. The full
 * record lives in the session file on the driver's machine, not in this tab. */
const MAX_ROWS = 3000;

interface AppState {
  language: Language;
  connection: ConnectionState;
  /** Why we are not connected, when we know. Shown to the user verbatim. */
  problem: string | null;
  channels: string[];
  rows: SampleRow[];
  latest: SampleRow | null;
  setLanguage: (language: Language) => void;
  setConnection: (connection: ConnectionState, problem?: string | null) => void;
  setChannels: (channels: string[]) => void;
  pushSamples: (rows: SampleRow[]) => void;
}

export const useAppStore = create<AppState>((set) => ({
  language: DEFAULT_LANGUAGE,
  connection: 'disconnected',
  problem: null,
  channels: [],
  rows: [],
  latest: null,
  setLanguage: (language) => set({ language }),
  setConnection: (connection, problem = null) => set({ connection, problem }),
  setChannels: (channels) => set({ channels }),
  pushSamples: (incoming) =>
    set((state) => {
      const rows = [...state.rows, ...incoming];
      return {
        rows: rows.length > MAX_ROWS ? rows.slice(rows.length - MAX_ROWS) : rows,
        latest: incoming.at(-1) ?? state.latest,
      };
    }),
}));
