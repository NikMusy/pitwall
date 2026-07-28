import { useEffect, useRef } from 'react';

import type { ChannelTrace } from './api';

export interface Pane {
  title: string;
  unit: string;
  /** Several channels share a pane when they share a scale, like throttle and brake. */
  series: { key: string; label: string; colour: string; trace: ChannelTrace | null }[];
  /** Fixed y range where the channel has a natural one; otherwise auto. */
  range?: [number, number];
}

interface TraceChartProps {
  panes: Pane[];
  fromS: number;
  toS: number;
  cursorS: number | null;
  onCursorChange: (t: number | null) => void;
  onZoom: (fromS: number, toS: number) => void;
}

const LEFT_GUTTER = 62;
const RIGHT_PAD = 12;
const PANE_GAP = 6;
const AXIS_HEIGHT = 22;

const GRID = 'rgba(255,255,255,0.07)';
const AXIS_TEXT = 'rgba(255,255,255,0.42)';
const CURSOR = 'rgba(255,255,255,0.55)';

function niceTicks(min: number, max: number, count: number): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) {
    return [min];
  }
  const raw = (max - min) / count;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * magnitude).find((s) => s >= raw) ?? magnitude * 10;
  const first = Math.ceil(min / step) * step;
  const ticks: number[] = [];
  for (let value = first; value <= max + step * 0.001; value += step) {
    ticks.push(value);
  }
  return ticks;
}

function paneBounds(pane: Pane): [number, number] {
  if (pane.range) {
    return pane.range;
  }
  let min = Infinity;
  let max = -Infinity;
  for (const series of pane.series) {
    if (!series.trace) continue;
    for (const value of series.trace.min) min = Math.min(min, value);
    for (const value of series.trace.max) max = Math.max(max, value);
  }
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return [0, 1];
  }
  if (min === max) {
    return [min - 1, max + 1];
  }
  const padding = (max - min) * 0.06;
  return [min - padding, max + padding];
}

function valueAt(trace: ChannelTrace, t: number): number | null {
  if (trace.t.length === 0) return null;
  let low = 0;
  let high = trace.t.length - 1;
  while (low < high) {
    const mid = (low + high) >> 1;
    if (trace.t[mid]! < t) low = mid + 1;
    else high = mid;
  }
  const min = trace.min[low];
  const max = trace.max[low];
  if (min === undefined || max === undefined) return null;
  return (min + max) / 2;
}

export function TraceChart({
  panes,
  fromS,
  toS,
  cursorS,
  onCursorChange,
  onZoom,
}: TraceChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dragRef = useRef<{ startX: number; currentX: number } | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext('2d');
    if (!context) return;

    const draw = () => {
      const ratio = window.devicePixelRatio || 1;
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      canvas.width = width * ratio;
      canvas.height = height * ratio;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      context.clearRect(0, 0, width, height);

      const plotWidth = width - LEFT_GUTTER - RIGHT_PAD;
      const plotHeight = height - AXIS_HEIGHT;
      const paneHeight = (plotHeight - PANE_GAP * (panes.length - 1)) / panes.length;
      const span = toS - fromS || 1;
      const xOf = (t: number) => LEFT_GUTTER + ((t - fromS) / span) * plotWidth;

      panes.forEach((pane, index) => {
        const top = index * (paneHeight + PANE_GAP);
        const [min, max] = paneBounds(pane);
        const yOf = (value: number) =>
          top + paneHeight - ((value - min) / (max - min || 1)) * paneHeight;

        context.fillStyle = 'rgba(255,255,255,0.02)';
        context.fillRect(LEFT_GUTTER, top, plotWidth, paneHeight);

        context.strokeStyle = GRID;
        context.lineWidth = 1;
        context.fillStyle = AXIS_TEXT;
        context.font = '10px ui-monospace, monospace';
        context.textAlign = 'right';
        for (const tick of niceTicks(min, max, 3)) {
          const y = Math.round(yOf(tick)) + 0.5;
          if (y < top || y > top + paneHeight) continue;
          context.beginPath();
          context.moveTo(LEFT_GUTTER, y);
          context.lineTo(LEFT_GUTTER + plotWidth, y);
          context.stroke();
          context.fillText(tick.toFixed(Math.abs(tick) < 10 ? 1 : 0), LEFT_GUTTER - 6, y + 3);
        }

        for (const series of pane.series) {
          if (!series.trace || series.trace.t.length === 0) continue;
          context.strokeStyle = series.colour;
          context.lineWidth = 1.25;
          context.beginPath();
          // One vertical stroke per column spans that column's min and max, so
          // a spike narrower than a pixel is still drawn at full height.
          for (let i = 0; i < series.trace.t.length; i += 1) {
            const x = xOf(series.trace.t[i]!);
            const yMin = yOf(series.trace.min[i]!);
            const yMax = yOf(series.trace.max[i]!);
            if (i === 0) context.moveTo(x, yMax);
            else context.lineTo(x, yMax);
            if (yMin !== yMax) context.lineTo(x, yMin);
          }
          context.stroke();
        }

        context.fillStyle = 'rgba(255,255,255,0.75)';
        context.font = '11px ui-sans-serif, system-ui';
        context.textAlign = 'left';
        const label = pane.unit ? `${pane.title}  ${pane.unit}` : pane.title;
        context.fillText(label, LEFT_GUTTER + 6, top + 13);

        if (cursorS !== null) {
          let offset = 0;
          for (const series of pane.series) {
            const value = series.trace ? valueAt(series.trace, cursorS) : null;
            context.fillStyle = series.colour;
            context.textAlign = 'right';
            context.fillText(
              value === null ? '—' : value.toFixed(1),
              LEFT_GUTTER + plotWidth - 6 - offset,
              top + 13,
            );
            offset += 54;
          }
        }
      });

      context.strokeStyle = GRID;
      context.beginPath();
      context.moveTo(LEFT_GUTTER, plotHeight + 0.5);
      context.lineTo(LEFT_GUTTER + plotWidth, plotHeight + 0.5);
      context.stroke();

      context.fillStyle = AXIS_TEXT;
      context.font = '10px ui-monospace, monospace';
      context.textAlign = 'center';
      for (const tick of niceTicks(fromS, toS, 8)) {
        const x = xOf(tick);
        if (x < LEFT_GUTTER || x > LEFT_GUTTER + plotWidth) continue;
        context.fillText(`${tick.toFixed(1)}s`, x, plotHeight + 14);
      }

      if (cursorS !== null) {
        const x = Math.round(xOf(cursorS)) + 0.5;
        context.strokeStyle = CURSOR;
        context.beginPath();
        context.moveTo(x, 0);
        context.lineTo(x, plotHeight);
        context.stroke();
      }

      const drag = dragRef.current;
      if (drag && Math.abs(drag.currentX - drag.startX) > 2) {
        context.fillStyle = 'rgba(120,180,255,0.16)';
        context.fillRect(
          Math.min(drag.startX, drag.currentX),
          0,
          Math.abs(drag.currentX - drag.startX),
          plotHeight,
        );
      }
    };

    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [panes, fromS, toS, cursorS]);

  const timeAt = (clientX: number): number => {
    const canvas = canvasRef.current;
    if (!canvas) return fromS;
    const rect = canvas.getBoundingClientRect();
    const plotWidth = rect.width - LEFT_GUTTER - RIGHT_PAD;
    const ratio = (clientX - rect.left - LEFT_GUTTER) / plotWidth;
    return fromS + Math.max(0, Math.min(1, ratio)) * (toS - fromS);
  };

  return (
    <canvas
      ref={canvasRef}
      className="h-full w-full cursor-crosshair"
      onMouseMove={(event) => {
        onCursorChange(timeAt(event.clientX));
        if (dragRef.current) {
          const rect = event.currentTarget.getBoundingClientRect();
          dragRef.current.currentX = event.clientX - rect.left;
        }
      }}
      onMouseLeave={() => {
        onCursorChange(null);
        dragRef.current = null;
      }}
      onMouseDown={(event) => {
        const rect = event.currentTarget.getBoundingClientRect();
        const x = event.clientX - rect.left;
        dragRef.current = { startX: x, currentX: x };
      }}
      onMouseUp={(event) => {
        const drag = dragRef.current;
        dragRef.current = null;
        if (!drag) return;
        const rect = event.currentTarget.getBoundingClientRect();
        if (Math.abs(event.clientX - rect.left - drag.startX) < 6) return;
        const a = timeAt(rect.left + drag.startX);
        const b = timeAt(event.clientX);
        onZoom(Math.min(a, b), Math.max(a, b));
      }}
      onDoubleClick={() => onZoom(Number.NaN, Number.NaN)}
    />
  );
}
