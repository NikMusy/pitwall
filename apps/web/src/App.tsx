import { useEffect, useState } from 'react';

import { Gauge } from './Gauge';
import { t } from './i18n';
import { useAppStore } from './store';
import { connect } from './telemetry';

const MS_PER_S = 1000;

function RoomForm({ onJoin }: { onJoin: (room: string, token: string) => void }) {
  const language = useAppStore((s) => s.language);
  const [room, setRoom] = useState('');
  const [token, setToken] = useState('');

  return (
    <form
      className="mt-8 flex max-w-md flex-col gap-3"
      onSubmit={(event) => {
        event.preventDefault();
        onJoin(room.trim().toUpperCase(), token.trim());
      }}
    >
      <label className="text-sm text-neutral-400" htmlFor="room">
        {t('roomCode', language)}
      </label>
      <input
        id="room"
        value={room}
        onChange={(event) => setRoom(event.target.value)}
        autoComplete="off"
        spellCheck={false}
        className="rounded border border-neutral-700 bg-neutral-900 px-3 py-2 font-mono uppercase tracking-widest text-neutral-100"
      />
      <label className="text-sm text-neutral-400" htmlFor="token">
        {t('tokenOptional', language)}
      </label>
      <input
        id="token"
        type="password"
        value={token}
        onChange={(event) => setToken(event.target.value)}
        className="rounded border border-neutral-700 bg-neutral-900 px-3 py-2 text-neutral-100"
      />
      <button
        type="submit"
        disabled={room.trim().length === 0}
        className="mt-2 rounded bg-neutral-200 px-4 py-2 font-medium text-neutral-900 disabled:bg-neutral-800 disabled:text-neutral-600"
      >
        {t('join', language)}
      </button>
    </form>
  );
}

export function App() {
  const language = useAppStore((s) => s.language);
  const connection = useAppStore((s) => s.connection);
  const problem = useAppStore((s) => s.problem);
  const latest = useAppStore((s) => s.latest);
  const [joined, setJoined] = useState<{ room: string; token: string } | null>(null);

  useEffect(() => {
    if (joined === null) {
      return;
    }
    return connect(joined.room, joined.token);
  }, [joined]);

  const values = latest?.v;
  const speed = values?.speed;

  return (
    <main className="min-h-screen bg-neutral-950 px-8 py-10 text-neutral-200">
      <header className="flex items-baseline gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">{t('appName', language)}</h1>
        <span className="text-sm text-neutral-500">
          {joined ? joined.room : t('notJoined', language)}
        </span>
      </header>

      {joined === null ? (
        <RoomForm onJoin={(room, token) => setJoined({ room, token })} />
      ) : (
        <>
          <section className="mt-6 max-w-md rounded border border-neutral-800 bg-neutral-900 p-4">
            <p className="text-sm text-neutral-300">
              {connection === 'live' ? t('live', language) : t('noAgent', language)}
            </p>
            {problem && <p className="mt-1 text-sm text-amber-400">{problem}</p>}
          </section>

          <div className="mt-6 grid max-w-4xl grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            <Gauge
              label={t('speed', language)}
              value={typeof speed === 'number' ? speed * 3.6 : speed}
              unit="km/h"
              digits={0}
            />
            <Gauge label={t('rpm', language)} value={values?.rpm} digits={0} />
            <Gauge label={t('gear', language)} value={values?.gear} digits={0} />
            <Gauge
              label={t('throttle', language)}
              value={typeof values?.throttle === 'number' ? values.throttle * 100 : values?.throttle}
              unit="%"
              digits={0}
              fill={typeof values?.throttle === 'number' ? values.throttle : undefined}
            />
            <Gauge
              label={t('brake', language)}
              value={typeof values?.brake === 'number' ? values.brake * 100 : values?.brake}
              unit="%"
              digits={0}
              fill={typeof values?.brake === 'number' ? values.brake : undefined}
            />
            <Gauge label={t('fuel', language)} value={values?.fuel_level} unit="L" digits={1} />
            <Gauge label={t('lap', language)} value={values?.lap} digits={0} />
            <Gauge
              label={t('lapTime', language)}
              value={
                typeof values?.lap_time === 'number'
                  ? Math.round(values.lap_time * MS_PER_S) / MS_PER_S
                  : values?.lap_time
              }
              unit="s"
              digits={2}
            />
          </div>
        </>
      )}
    </main>
  );
}
