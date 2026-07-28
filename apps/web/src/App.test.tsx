import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { LiveView } from './LiveView';
import { Gauge } from './Gauge';
import { useAppStore } from './store';
import { socketUrl } from './telemetry';

describe('App', () => {
  beforeEach(() => {
    useAppStore.setState({ connection: 'disconnected', problem: null, latest: null, rows: [] });
  });

  it('asks where to connect before connecting anywhere', () => {
    render(<LiveView />);
    expect(screen.getByLabelText('Адрес пилота')).toBeDefined();
    expect(screen.getByLabelText('Код комнаты')).toBeDefined();
  });

  it('keeps the connect button disabled until a room code is entered', () => {
    render(<LiveView />);
    const button = screen.getByRole('button', { name: 'Подключиться' });
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });
});

describe('socketUrl', () => {
  it('falls back to the serving machine when no host is given', () => {
    expect(socketUrl('', 'BCDFGH', '')).toContain(window.location.host);
  });

  it('points at the driver when a host is given', () => {
    const url = socketUrl('nikmusy.tail611341.ts.net:8420', 'BCDFGH', '');
    expect(url).toBe('ws://nikmusy.tail611341.ts.net:8420/ws/view?room=BCDFGH');
  });

  it('tolerates a pasted address with a scheme or trailing slash', () => {
    // Someone will paste the whole thing out of a chat message.
    expect(socketUrl('http://host:8420/', 'BCDFGH', '')).toBe(
      'ws://host:8420/ws/view?room=BCDFGH',
    );
  });

  it('includes the token only when there is one', () => {
    expect(socketUrl('host:1', 'BCDFGH', '')).not.toContain('token');
    expect(socketUrl('host:1', 'BCDFGH', 'secret')).toContain('token=secret');
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
