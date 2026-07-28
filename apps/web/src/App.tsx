import { CHANNELS, PROTOCOL_VERSION } from '@pitwall/schema';

import { t } from './i18n';
import { useAppStore } from './store';

export function App() {
  const language = useAppStore((s) => s.language);
  const connection = useAppStore((s) => s.connection);
  const problem = useAppStore((s) => s.problem);

  return (
    <main className="min-h-screen bg-neutral-950 px-8 py-10 text-neutral-200">
      <h1 className="text-2xl font-semibold tracking-tight">{t('appName', language)}</h1>
      <p className="mt-1 text-sm text-neutral-500">{t('milestone', language)} M0</p>

      <section className="mt-8 max-w-md rounded border border-neutral-800 bg-neutral-900 p-5">
        <p className="text-lg text-neutral-100">
          {connection === 'live' ? null : t('noAgent', language)}
        </p>
        <p className="mt-2 text-sm text-neutral-400">{problem ?? t('noAgentHint', language)}</p>
      </section>

      <dl className="mt-8 grid max-w-md grid-cols-2 gap-y-2 text-sm">
        <dt className="text-neutral-500">{t('channelsKnown', language)}</dt>
        <dd className="text-right tabular-nums">{Object.keys(CHANNELS).length}</dd>
        <dt className="text-neutral-500">{t('protocolVersion', language)}</dt>
        <dd className="text-right tabular-nums">{PROTOCOL_VERSION}</dd>
      </dl>
    </main>
  );
}
