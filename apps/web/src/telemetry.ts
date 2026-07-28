import { decode } from '@msgpack/msgpack';

import { useAppStore } from './store';

export type SampleRow = { t: number; v: Record<string, number | boolean | null> };

type Frame =
  | { f: 'welcome'; session_id: string; channels: string[]; rate_hz: number; game: string | null }
  | { f: 'agent_status'; connected_to_game: boolean; game: string | null; problem: string | null }
  | { f: 'samples'; count: number; rows: SampleRow[] }
  | { f: 'error'; code: string; message: string };

/**
 * `host` empty means the machine serving this page — that is the driver
 * watching their own car. A strategist types the driver's tailnet address
 * instead, so the socket has to be able to point somewhere else entirely.
 */
export function socketUrl(host: string, room: string, token: string): string {
  const target = host.trim() || window.location.host;
  const withoutScheme = target.replace(/^\w+:\/\//, '').replace(/\/+$/, '');
  const secure = window.location.protocol === 'https:' && !host.trim();
  const params = new URLSearchParams({ room });
  if (token) {
    params.set('token', token);
  }
  return `${secure ? 'wss:' : 'ws:'}//${withoutScheme}/ws/view?${params.toString()}`;
}

export function connect(host: string, room: string, token = ''): () => void {
  useAppStore.getState().setConnection('connecting');

  const socket = new WebSocket(socketUrl(host, room, token));
  socket.binaryType = 'arraybuffer';

  socket.onmessage = (event: MessageEvent<ArrayBuffer>) => {
    const frame = decode(new Uint8Array(event.data)) as Frame;
    const state = useAppStore.getState();

    switch (frame.f) {
      case 'welcome':
        state.setChannels(frame.channels);
        break;
      case 'agent_status':
        state.setConnection(frame.connected_to_game ? 'live' : 'connecting', frame.problem);
        break;
      case 'samples':
        state.pushSamples(frame.rows);
        break;
      case 'error':
        state.setConnection('disconnected', frame.message);
        socket.close();
        break;
    }
  };

  socket.onerror = () => {
    useAppStore
      .getState()
      .setConnection('disconnected', `Не удалось подключиться к ${host || 'этой машине'}`);
  };

  socket.onclose = () => {
    const state = useAppStore.getState();
    if (state.connection !== 'disconnected') {
      state.setConnection('disconnected', 'Соединение закрыто');
    }
  };

  return () => socket.close();
}
