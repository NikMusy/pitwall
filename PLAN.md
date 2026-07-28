# PLAN

Living checklist. Updated at the end of every milestone.

## Decisions

Settled before M0 started:

| Question | Decision | Consequence |
|---|---|---|
| Where does the hub run? | Locally on the driver's PC | No VPS, no docker-compose, no nginx/caddy in M6 |
| How does the strategist connect? | **Tailscale** | Hub binds the tailnet interface; TLS comes from `tailscale serve` on `*.ts.net`. Reconfirmed after the repo was made public — "public" applies to the source, not to hub access |
| Priority game for M1 | **Le Mans Ultimate** | M1 depends on the rF2 shared memory plugin being installed |
| Public spectator mode | No — team only | Roles: `driver`, `engineer`. Room code plus optional token |
| Track/car naming | Single normalised reference | `packages/schema` owns the mapping; raw per-game name is kept alongside |

## Assets already available

Reduces risk, do not rebuild from scratch:

- `NikMusy/le-mans-ultimate-telemetry` — working rF2 ctypes structs
  (`rF2Telemetry`, `rF2Scoring`, `rF2VehicleTelemetry`, `rF2VehicleScoring`,
  `rF2Wheel`) and an F1 UDP parser. Use as a starting point, re-verify against
  the plugin headers.
- `LMU-Engineer/ldread.py` — `.ld` reader, relevant to M8.
- 145 real `.ld` logs from LMU, plus MoTeC i2 Standard 1.1 installed — these are
  the validation baseline for M4/M5 math, not just import fixtures.

Explicitly **not** carried over: `demo_snapshot()` and any other synthetic data
generator.

## Milestones

### M0 — skeleton, schema codegen, CI

- [x] Repo initialised, MIT, `.gitignore`, README
- [x] `CLAUDE.md`, `PLAN.md`
- [x] `packages/schema`: `channels.yaml` + `protocol.yaml`
- [x] Codegen to Python and TypeScript, staleness check in CI
- [x] `apps/agent` skeleton (uv, ruff, mypy, pytest)
- [x] `apps/hub` skeleton (FastAPI, `/health`)
- [x] `apps/web` skeleton (Vite, React, TS, Tailwind, Zustand, i18n)
- [x] `ci.yml` written, green locally
- [x] Pushed to <https://github.com/NikMusy/pitwall>, tagged `v0.0.1-m0`
- [ ] **Blocked:** CI green on the runner

Local state: 76 channels generate to both languages, mypy strict clean,
79 Python tests and 3 web tests pass, production build succeeds.

The runner never started either job: *"The job was not started because your
account is locked due to a billing issue."* Not a code failure and not fixable
from here — it needs the GitHub account billing resolved. M0 stays formally
open until a run goes green.

### M1 — LMU live

- [x] rF2 struct definitions from the plugin header, layout tests
- [x] Shared memory reader with the double-buffer version check
- [x] Channel mapping: units, tyre wear inversion, orientation angles
- [x] Agent to hub to browser over WebSocket, MessagePack frames
- [x] Room codes, roles, token, fan-out that drops slow viewers
- [x] Hub binds the tailnet address, serves the built UI
- [x] Live readouts in the browser, missing channels render as absent
- [x] PyInstaller `--onedir` build, verified running frozen
- [ ] `--record-raw` dump mode, fixtures committed
- [ ] **Blocked:** verification against real telemetry

Everything above is exercised by tests and by running the built executable.
What has never seen real data is the mapping itself: the plugin is not
installed, so no lap has ever gone through it.

Two things are explicitly unverified until a dump exists:

- The sign convention of `pitch` and `roll`. Magnitudes come from the
  orientation basis vectors and are right; a sign could be inverted.
- Whether `mDentSeverity[0..3]` really orders as front/rear/left/right. The
  scale (0–2, so divided by 2) is from the header; the ordering is an
  assumption.

Done when: throttle, brake and speed are visible live in the browser, and the
above are confirmed against a recorded lap.

### M2 — remaining providers

- [ ] F1 25 UDP listener, verified against the current official spec
- [ ] ACC shared memory
- [ ] Provider autodetect and hot switching

Done when: all three games deliver the core channel set.

### M3 — recording and session load

- [ ] `.pwsess` writer and reader
- [ ] Lap segmentation, in/out lap detection
- [ ] Session loading in the UI

### M4 — the renderer (do not defer)

- [ ] WebGL2 line renderer
- [ ] LOD pyramid in a worker, IndexedDB cache
- [ ] Min/max per-pixel-column decimation
- [ ] Delta-T, track map, lap overlay
- [ ] 20M-point benchmark wired into CI

If the renderer cannot hold the budget, the project premise fails — this has to
be found out early, not at M8.

### M5 — analysis parity with i2

- [ ] Math channel parser (own expression parser, not `eval`)
- [ ] Sections, channel report, section report, ideal lap
- [ ] Histogram, X-Y scatter, FFT

### M6 — hub as relay

- [ ] Rooms, roles, backpressure
- [ ] Tailscale access path documented and tested end to end
- [ ] Live timing tower
- [ ] Multi-driver endurance support

### M7 — strategy

- [ ] Fuel model, tyre degradation, stint planner
- [ ] Undercut/overcut with measured pit loss
- [ ] Traffic projection, alerts

### M8 — projection and import

- [ ] Monte Carlo race projection
- [ ] Race log, debrief report
- [ ] `.ld`/`.ldx` import

### M9 — packaging

- [ ] PyInstaller `--onedir`, Inno Setup installer
- [ ] Smoke test in `release.yml`
- [ ] Auto-update check
- [ ] v1.0.0
