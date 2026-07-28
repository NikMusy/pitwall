import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { App } from './App';
import { Gauge } from './Gauge';
import { useAppStore } from './store';

describe('App', () => {
  beforeEach(() => {
    useAppStore.setState({ connection: 'disconnected', problem: null, latest: null, rows: [] });
  });

  it('asks for a room code before connecting anywhere', () => {
    render(<App />);
    expect(screen.getByLabelText('Код комнаты')).toBeDefined();
  });

  it('keeps the join button disabled until a code is entered', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: 'Подключиться' });
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });
});

describe('Gauge', () => {
  it('renders a missing channel as a dash, never as zero', () => {
    // Zero throttle and "no throttle data" must not look the same on a pit wall.
    render(<Gauge label="Газ" value={null} />);
    expect(screen.getByText('—')).toBeDefined();
  });

  it('renders a real zero as zero', () => {
    render(<Gauge label="Газ" value={0} digits={0} />);
    expect(screen.getByText('0')).toBeDefined();
  });

  it('formats booleans instead of printing true/false', () => {
    render(<Gauge label="ABS" value={true} />);
    expect(screen.getByText('on')).toBeDefined();
  });
});
