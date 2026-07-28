export interface LogSummary {
  id: string;
  recorded_at: string;
  size_bytes: number;
}

export interface Lap {
  number: number;
  start_s: number;
  end_s: number;
}

export interface LogDetail {
  id: string;
  driver: string;
  venue: string;
  date: string;
  time: string;
  duration_s: number;
  channels: { key: string; unit: string; rate_hz: number }[];
  laps: Lap[];
}

/** Min/max per pixel column, so peaks survive decimation. */
export interface ChannelTrace {
  t: number[];
  min: number[];
  max: number[];
}

export type ChannelResponse = Record<string, ChannelTrace | null>;

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`${path} → HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

export function fetchLogs(): Promise<LogSummary[]> {
  return getJson<LogSummary[]>('/api/logs');
}

export function fetchLog(id: string): Promise<LogDetail> {
  return getJson<LogDetail>(`/api/logs/${encodeURIComponent(id)}`);
}

export async function fetchChannels(
  id: string,
  keys: string[],
  fromS: number,
  toS: number,
  columns: number,
): Promise<ChannelResponse> {
  const params = new URLSearchParams({
    keys: keys.join(','),
    from: String(fromS),
    to: String(toS),
    columns: String(Math.round(columns)),
  });
  const body = await getJson<{ channels: ChannelResponse }>(
    `/api/logs/${encodeURIComponent(id)}/channels?${params.toString()}`,
  );
  return body.channels;
}
