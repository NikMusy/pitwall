import { decode } from '@msgpack/msgpack';

import { useAppStore } from './store';

export type SampleRow = { t: number; v: Record<string, number | boolean | null> };

type Frame =
  | { f: 'welcome'; session_id: string; channels: string[]; rate_hz: number; game: string | null }
  | { f: 'agent_status'; connected_to_game: boolean; game: string | null; problem: string | null }
  | { f: 'samples'; count: number; rows: SampleRow[] }
  | { f: 'error'; code: string; message: string };

/** Same origin as the page: the strategist reached it over the tailnet, so the
 * socket goes back to exactly the address that served the page. */
function socketUrl(room: string, token: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const params = new URLSearchParams({ room });
  if (token) {
    params.set('token', token);
  }
  return `${protocol}//${window.location.host}/ws/view?${params.toString()}`;
}

export function connect(room: string, token = ''): () => void {
  const store = useAppStore.getState();
  store.setConnection('connecting');

  const socket = new WebSocket(socketUrl(room, token));
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
    useAppStore.getState().setConnection('disconnected', 'WebSocket error');
  };

  socket.onclose = () => {
    const state = useAppStore.getState();
    if (state.connection !== 'disconnected') {
      state.setConnection('disconnected', 'Connection closed');
    }
  };

  return () => socket.close();
}
