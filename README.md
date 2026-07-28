# PitWall

Open telemetry and race-strategy platform for sim racing.

The analysis side aims at MoTeC i2 Pro parity — channels, lap overlay,
delta-time, track map, math channels, sections, reports. On top of that it does
two things i2 does not:

- **Live.** Telemetry streams from the driver's PC to a strategist's browser
  anywhere.
- **Strategy.** Fuel, tyre degradation, pit windows, undercut/overcut, traffic,
  and a Monte Carlo projection of the rest of the race.

Supported sims: Le Mans Ultimate / rFactor 2, F1 25, Assetto Corsa Competizione.

## Status

**Early development — M0.** Nothing works yet. The repository currently
contains the monorepo skeleton, the channel/protocol schema and CI. Follow
[PLAN.md](PLAN.md) for what is actually implemented.

## Architecture

```
  AGENT (Windows)          HUB (relay)            WEB UI (browser)
  driver's PC       WS     local or tailnet   WS  strategist / engineer
  ─────────────── ──────►  ───────────────── ──►  ──────────────────
  rF2/LMU shared mem       rooms by code          live view
  F1 25 UDP :20777         fan-out                session analysis
  ACC shared mem           session storage        strategy
  channel normalisation    REST for history
  local .pwsess recording
```

One executable, three modes:

- **Solo** — agent, hub and UI in one process, browser opens on `localhost:8420`.
- **Team** — agent connects to a hub by room code, strategist joins by link.
- **Replay** — hub only, for analysing recorded sessions.

## Requirements

- Windows 10/11
- For Le Mans Ultimate / rFactor 2: the
  [rF2 Shared Memory Map Plugin](https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin)
  installed and enabled. See [docs/lmu-setup.md](docs/lmu-setup.md).
- For F1 25: UDP telemetry enabled in game settings, port 20777.

## Data format

Sessions are stored as `.pwsess` — a zip container with `meta.json`,
`laps.json` and one Parquet file per channel group. It is readable with
standard tooling (pandas, DuckDB, Polars) without any PitWall code. That is a
requirement of the project, not a convenience.

## Development

```bash
uv sync
npm install
npm run dev
```

## Licence

MIT. Not affiliated with MoTeC, Studio 397, MSG, EA, Codemasters or Kunos.
`.ld`/`.ldx` support is implemented from open format descriptions; no MoTeC
code or assets are used.
