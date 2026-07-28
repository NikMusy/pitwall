import { CHANNELS } from '@pitwall/schema';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { App } from './App';
import { useAppStore } from './store';

describe('App', () => {
  beforeEach(() => {
    useAppStore.setState({ connection: 'disconnected', problem: null });
  });

  it('says plainly that no agent is connected', () => {
    render(<App />);
    expect(screen.getByText('Агент не подключён')).toBeDefined();
  });

  it('surfaces the reported problem instead of a generic hint', () => {
    useAppStore.setState({ problem: 'LMU не запущена' });
    render(<App />);
    expect(screen.getByText('LMU не запущена')).toBeDefined();
  });

  it('reports the channel count from the generated schema', () => {
    // Guards the codegen link end to end: the count is not hardcoded here, so
    // a broken schema import fails the assertion rather than drifting silently.
    const count = Object.keys(CHANNELS).length;
    expect(count).toBeGreaterThan(0);

    render(<App />);
    expect(screen.getByText(String(count))).toBeDefined();
  });
});
