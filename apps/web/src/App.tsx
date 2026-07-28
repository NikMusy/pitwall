import { useEffect, useState } from 'react';

import { Gauge } from './Gauge';
import { t } from './i18n';
import { useAppStore } from './store';
import { connect } from './telemetry';

interface Target {
  host: string;
  room: string;
  token: string;
}

/** The driver's own machine prefills these through the desktop launcher. */
function initialTarget(): Target {
  const params = new URLSearchParams(window.location.search);
  return {
    host: params.get('host') ?? '',
    room: (params.get('room') ?? '').toUpperCase(),
    token: params.get('token') ?? '',
  };
}

function ConnectForm({ onJoin }: { onJoin: (target: Target) => void }) {
  const language = useAppStore((s) => s.language);
  const [target, setTarget] = useState<Target>(initialTarget);

  const field =
    'rounded border border-neutral-700 bg-neutral-900 px-3 py-2 text-neutral-100 outline-none focus:border-neutral-500';

  return (
    <form
      className="mt-8 flex max-w-md flex-col gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        onJoin({ ...target, room: target.room.trim().toUpperCase() });
      }}
    >
      <label className="text-sm text-neutral-400" htmlFor="host">
        {t('driverAddress', language)}
      </label>
      <input
        id="host"
        value={target.host}
        placeholder={t('driverAddressHint', language)}
        onChange={(event) => setTarget({ ...target, host: event.target.value })}
        autoComplete="off"
        spellCheck={false}
        className={field}
      />

      <label className="mt-2 text-sm text-neutral-400" htmlFor="room">
        {t('roomCode', language)}
      </label>
      <input
        id="room"
        value={target.room}
        onChange={(event) => setTarget({ ...target, room: event.target.value })}
        autoComplete="off"
        spellCheck={false}
        className={`${field} font-mono uppercase tracking-widest`}
      />

      <label className="mt-2 text-sm text-neutral-400" htmlFor="token">
        {t('tokenOptional', language)}
      </label>
      <input
        id="token"
        type="password"
        value={target.token}
        onChange={(event) => setTarget({ ...target, token: event.target.value })}
        className={field}
      />

      <button
        type="submit"
        disabled={target.room.trim().length === 0}
        className="mt-4 rounded bg-neutral-200 px-4 py-2 font-medium text-neutral-900 disabled:bg-neutral-800 disabled:text-neutral-600"
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
  const [target, setTarget] = useState<Target | null>(null);

  useEffect(() => {
    if (target === null) {
      return;
    }
    return connect(target.host, target.room, target.token);
  }, [target]);

  const values = latest?.v;
  const speed = values?.speed;
  const pct = (value: number | boolean | null | undefined) =>
    typeof value === 'number' ? value * 100 : value;

  return (
    <main className="min-h-screen bg-neutral-950 px-8 py-8 text-neutral-200">
      <header className="flex items-baseline justify-between">
        <h1 className="text-xl font-semibold tracking-tight">{t('appName', language)}</h1>
        {target && (
          <span className="font-mono text-sm text-neutral-500">
            {target.host || t('thisMachine', language)} · {target.room}
          </span>
        )}
      </header>

      {target === null ? (
        <ConnectForm onJoin={setTarget} />
      ) : (
        <>
          <section className="mt-5 flex items-center gap-3">
            <span
              className={`h-2 w-2 rounded-full ${
                connection === 'live' ? 'bg-emerald-400' : 'bg-neutral-600'
              }`}
            />
            <span className="text-sm text-neutral-300">
              {connection === 'live' ? t('live', language) : t('noAgent', language)}
            </span>
            <button
              type="button"
              onClick={() => setTarget(null)}
              className="ml-auto text-sm text-neutral-500 underline"
            >
              {t('disconnect', language)}
            </button>
          </section>

          {problem && (
            <p className="mt-3 max-w-2xl rounded border border-amber-900 bg-amber-950/40 px-3 py-2 text-sm text-amber-300">
              {problem}
            </p>
          )}

          <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            <Gauge
              label={t('speed', language)}
              value={typeof speed === 'number' ? speed * 3.6 : speed}
              unit="km/h"
              digits={0}
            />
            <Gauge label={t('rpm', language)} value={values?.rpm} digits={0} />
            <Gauge label={t('gear', language)} value={values?.gear} digits={0} />
            <Gauge label={t('lap', language)} value={values?.lap} digits={0} />
            <Gauge
              label={t('throttle', language)}
              value={pct(values?.throttle)}
              unit="%"
              digits={0}
              fill={typeof values?.throttle === 'number' ? values.throttle : undefined}
            />
            <Gauge
              label={t('brake', language)}
              value={pct(values?.brake)}
              unit="%"
              digits={0}
              fill={typeof values?.brake === 'number' ? values.brake : undefined}
            />
            <Gauge label={t('fuel', language)} value={values?.fuel_level} unit="L" digits={1} />
            <Gauge label={t('lapTime', language)} value={values?.lap_time} unit="s" digits={2} />
            <Gauge
              label={t('tyreFl', language)}
              value={
                typeof values?.tyre_temp_fl_m === 'number' ? values.tyre_temp_fl_m - 273.15 : null
              }
              unit="°C"
              digits={0}
            />
            <Gauge
              label={t('tyreFr', language)}
              value={
                typeof values?.tyre_temp_fr_m === 'number' ? values.tyre_temp_fr_m - 273.15 : null
              }
              unit="°C"
              digits={0}
            />
            <Gauge
              label={t('tyreRl', language)}
              value={
                typeof values?.tyre_temp_rl_m === 'number' ? values.tyre_temp_rl_m - 273.15 : null
              }
              unit="°C"
              digits={0}
            />
            <Gauge
              label={t('tyreRr', language)}
              value={
                typeof values?.tyre_temp_rr_m === 'number' ? values.tyre_temp_rr_m - 273.15 : null
              }
              unit="°C"
              digits={0}
            />
          </div>
        </>
      )}
    </main>
  );
}
