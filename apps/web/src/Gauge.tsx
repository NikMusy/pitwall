interface GaugeProps {
  label: string;
  value: number | boolean | null | undefined;
  unit?: string;
  digits?: number;
  /** Fraction 0..1 for the bar, when the channel has a natural range. */
  fill?: number;
}

/**
 * A channel with no value renders as an em dash, never as zero. Zero throttle
 * and "we are not receiving throttle" mean completely different things on a
 * pit wall.
 */
export function Gauge({ label, value, unit, digits = 1, fill }: GaugeProps) {
  const missing = value === null || value === undefined;
  const text = missing
    ? '—'
    : typeof value === 'boolean'
      ? value
        ? 'on'
        : 'off'
      : value.toFixed(digits);

  return (
    <div className="rounded border border-neutral-800 bg-neutral-900 px-4 py-3">
      <div className="text-xs uppercase tracking-wide text-neutral-500">{label}</div>
      <div className="mt-1 flex items-baseline gap-1">
        <span
          className={`text-2xl tabular-nums ${missing ? 'text-neutral-600' : 'text-neutral-100'}`}
        >
          {text}
        </span>
        {unit && !missing && <span className="text-xs text-neutral-500">{unit}</span>}
      </div>
      {fill !== undefined && !missing && (
        <div className="mt-2 h-1 w-full overflow-hidden rounded bg-neutral-800">
          <div
            className="h-full bg-neutral-300"
            style={{ width: `${Math.max(0, Math.min(1, fill)) * 100}%` }}
          />
        </div>
      )}
    </div>
  );
}
