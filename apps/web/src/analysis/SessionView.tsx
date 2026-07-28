import { useCallback, useEffect, useMemo, useState } from 'react';

import { type ChannelResponse, type Lap, type LogDetail, type LogSummary } from './api';
import { fetchChannels, fetchLog, fetchLogs } from './api';
import { type Pane, TraceChart } from './TraceChart';

/** Grouped the way an engineer reads them: inputs together, then the car. */
const PANE_LAYOUT: { title: string; unit: string; keys: [string, string][]; range?: [number, number] }[] =
  [
    { title: 'Скорость', unit: 'км/ч', keys: [['speed', '#7dd3fc']] },
    {
      title: 'Педали',
      unit: '%',
      keys: [
        ['throttle', '#4ade80'],
        ['brake', '#f87171'],
      ],
      range: [0, 100],
    },
    { title: 'Обороты', unit: 'об/мин', keys: [['rpm', '#fbbf24']] },
    { title: 'Руль', unit: '%', keys: [['steering', '#c084fc']], range: [-100, 100] },
    {
      title: 'Темп. шин',
      unit: '°C',
      keys: [
        ['tyre_temp_fl_m', '#60a5fa'],
        ['tyre_temp_fr_m', '#f472b6'],
        ['tyre_temp_rl_m', '#34d399'],
        ['tyre_temp_rr_m', '#fbbf24'],
      ],
    },
  ];

const ALL_KEYS = PANE_LAYOUT.flatMap((pane) => pane.keys.map(([key]) => key));

/** Storage units are SI; these are the display conversions. */
const DISPLAY: Record<string, (value: number) => number> = {
  speed: (v) => v * 3.6,
  throttle: (v) => v * 100,
  brake: (v) => v * 100,
  steering: (v) => v * 100,
  tyre_temp_fl_m: (v) => v - 273.15,
  tyre_temp_fr_m: (v) => v - 273.15,
  tyre_temp_rl_m: (v) => v - 273.15,
  tyre_temp_rr_m: (v) => v - 273.15,
};

const LABELS: Record<string, string> = {
  speed: 'Скорость',
  throttle: 'Газ',
  brake: 'Тормоз',
  rpm: 'Обороты',
  steering: 'Руль',
  tyre_temp_fl_m: 'FL',
  tyre_temp_fr_m: 'FR',
  tyre_temp_rl_m: 'RL',
  tyre_temp_rr_m: 'RR',
};

function convert(key: string, response: ChannelResponse): Pane['series'][number]['trace'] {
  const trace = response[key];
  if (!trace) return null;
  const map = DISPLAY[key];
  if (!map) return trace;
  return { t: trace.t, min: trace.min.map(map), max: trace.max.map(map) };
}

export function SessionView() {
  const [logs, setLogs] = useState<LogSummary[]>([]);
  const [detail, setDetail] = useState<LogDetail | null>(null);
  const [lap, setLap] = useState<Lap | null>(null);
  const [window_, setWindow] = useState<[number, number] | null>(null);
  const [data, setData] = useState<ChannelResponse>({});
  const [cursor, setCursor] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const open = useCallback(async (id: string) => {
    setError(null);
    setLoading(true);
    try {
      const loaded = await fetchLog(id);
      setDetail(loaded);
      const first = loaded.laps[0] ?? null;
      setLap(first);
      setWindow(first ? [first.start_s, first.end_s] : [0, loaded.duration_s]);
    } catch (cause) {
      setError((cause as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs()
      .then((found) => {
        setLogs(found);
        // Open the newest session straight away: an empty screen with a list
        // is a worse first impression than data.
        if (found.length > 0) {
          void open(found[0]!.id);
        }
      })
      .catch((cause: Error) => setError(cause.message));
  }, [open]);

  useEffect(() => {
    if (!detail || !window_) return;
    let cancelled = false;
    setLoading(true);
    fetchChannels(detail.id, ALL_KEYS, window_[0], window_[1], 1500)
      .then((response) => {
        if (!cancelled) setData(response);
      })
      .catch((cause: Error) => !cancelled && setError(cause.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [detail, window_]);

  const panes = useMemo<Pane[]>(
    () =>
      PANE_LAYOUT.map((layout) => ({
        title: layout.title,
        unit: layout.unit,
        range: layout.range,
        series: layout.keys.map(([key, colour]) => ({
          key,
          label: LABELS[key] ?? key,
          colour,
          trace: convert(key, data),
        })),
      })),
    [data],
  );

  const selectLap = (next: Lap) => {
    setLap(next);
    setWindow([next.start_s, next.end_s]);
  };

  const zoom = (from: number, to: number) => {
    if (Number.isNaN(from) || Number.isNaN(to)) {
      if (lap) setWindow([lap.start_s, lap.end_s]);
      else if (detail) setWindow([0, detail.duration_s]);
      return;
    }
    if (to - from < 0.2) return;
    setWindow([from, to]);
  };

  return (
    <div className="flex h-screen bg-neutral-950 text-neutral-200">
      <aside className="flex w-72 shrink-0 flex-col border-r border-neutral-800">
        <div className="border-b border-neutral-800 px-3 py-2 text-xs uppercase tracking-wide text-neutral-500">
          Заезды ({logs.length})
        </div>
        <div className="max-h-64 overflow-y-auto">
          {logs.map((entry) => (
            <button
              key={entry.id}
              type="button"
              onClick={() => void open(entry.id)}
              className={`block w-full truncate px-3 py-1.5 text-left text-xs ${
                detail?.id === entry.id
                  ? 'bg-neutral-800 text-neutral-100'
                  : 'text-neutral-400 hover:bg-neutral-900'
              }`}
              title={entry.id}
            >
              {entry.id}
            </button>
          ))}
        </div>

        <div className="border-y border-neutral-800 px-3 py-2 text-xs uppercase tracking-wide text-neutral-500">
          Круги ({detail?.laps.length ?? 0})
        </div>
        <div className="flex-1 overflow-y-auto">
          {detail?.laps.map((entry) => (
            <button
              key={`${entry.number}-${entry.start_s}`}
              type="button"
              onClick={() => selectLap(entry)}
              className={`flex w-full justify-between px-3 py-1.5 text-left text-xs tabular-nums ${
                lap?.start_s === entry.start_s
                  ? 'bg-neutral-800 text-neutral-100'
                  : 'text-neutral-400 hover:bg-neutral-900'
              }`}
            >
              <span>Круг {entry.number}</span>
              <span className="text-neutral-500">{(entry.end_s - entry.start_s).toFixed(2)}s</span>
            </button>
          ))}
          {detail && detail.laps.length === 0 && (
            <p className="px-3 py-2 text-xs text-neutral-500">
              В этом логе нет отдельных кругов — счётчик кругов не менялся.
            </p>
          )}
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-baseline gap-3 border-b border-neutral-800 px-4 py-2">
          <span className="text-sm text-neutral-200">{detail?.venue ?? '—'}</span>
          <span className="text-xs text-neutral-500">{detail?.driver}</span>
          <span className="ml-auto font-mono text-xs text-neutral-500">
            {cursor !== null ? `${cursor.toFixed(2)}s` : ''}
            {loading ? '  загрузка…' : ''}
          </span>
        </header>

        {error && (
          <p className="border-b border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
            {error}
          </p>
        )}

        <div className="min-h-0 flex-1 p-2">
          {window_ ? (
            <TraceChart
              panes={panes}
              fromS={window_[0]}
              toS={window_[1]}
              cursorS={cursor}
              onCursorChange={setCursor}
              onZoom={zoom}
            />
          ) : (
            <p className="p-4 text-sm text-neutral-500">
              {logs.length === 0
                ? 'Записей не найдено. LMU пишет их в свою папку LOG, когда включена автозапись телеметрии.'
                : 'Выберите заезд.'}
            </p>
          )}
        </div>

        <footer className="border-t border-neutral-800 px-4 py-1.5 text-xs text-neutral-600">
          Протяните мышью — зум по выделению. Двойной клик — назад на круг.
        </footer>
      </main>
    </div>
  );
}
