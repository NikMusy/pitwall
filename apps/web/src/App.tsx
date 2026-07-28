import { useState } from 'react';

import { LiveView } from './LiveView';
import { SessionView } from './analysis/SessionView';

type Tab = 'analysis' | 'live';

export function App() {
  // Analysis first: recorded sessions exist right now, live needs the shared
  // memory plugin installed.
  const [tab, setTab] = useState<Tab>('analysis');

  const button = (id: Tab, label: string) => (
    <button
      key={id}
      type="button"
      onClick={() => setTab(id)}
      className={`px-3 py-1 text-xs ${
        tab === id
          ? 'border-b-2 border-neutral-200 text-neutral-100'
          : 'border-b-2 border-transparent text-neutral-500 hover:text-neutral-300'
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="flex h-screen flex-col bg-neutral-950">
      <nav className="flex shrink-0 items-center gap-1 border-b border-neutral-800 px-3">
        <span className="mr-3 text-sm font-semibold tracking-tight text-neutral-200">PitWall</span>
        {button('analysis', 'Разбор')}
        {button('live', 'Live')}
      </nav>
      <div className="min-h-0 flex-1">{tab === 'analysis' ? <SessionView /> : <LiveView />}</div>
    </div>
  );
}
