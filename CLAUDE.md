# PitWall — project rules

Open telemetry and race-strategy platform for sim racing. Functional target is
MoTeC i2 Pro for analysis depth, plus two things i2 does not do: live streaming
to a remote strategist, and a strategy module.

## Non-negotiables

**No fabricated data.** Never emit random, demo, or placeholder values that
could be mistaken for telemetry. If a channel is unavailable, it is `null` and
the UI says why. If a derived number is not measured yet (pit loss, degradation
slope), display "not measured", never a plausible-looking guess.

**No silent failures.** A parser that cannot make sense of a buffer raises. An
agent that lost the game says so in the UI. Swallowed exceptions in binary
parsing produce data that looks fine and is wrong — that is the worst possible
outcome for this project.

**Schema is generated, never hand-synced.** `packages/schema/schema/*.yaml` is
the single source of truth for channels and the wire protocol. Python and
TypeScript are generated from it. CI fails if generated files are stale. Do not
edit generated files; edit the YAML and regenerate.

**No MoTeC assets.** No copied code, icons, or branding. `.ld`/`.ldx` support is
implemented from open format descriptions only. Our UI is our own.

## Code

- Code, comments, identifiers, commit messages: English.
- UI strings: i18n, `ru` default, `en` second. Never hardcode user-facing text.
- Comments explain *why*, not *what*. Do not narrate the code.
- No abstractions on speculation. The second provider justifies an interface,
  the first does not.
- Channel keys are `snake_case` and stable. Renaming a key is a breaking change
  to saved sessions and presets — treat it as one.
- Telemetry arrays are `Float32Array` / numpy, never arrays of objects. This is
  a performance contract, not a style preference.

## Tests

- Binary parsers and math get tests **before** implementation. They break
  quietly otherwise.
- Every provider is tested against a recorded raw dump in `tests/fixtures/`.
  Dumps are produced by the agent itself via `--record-raw`.
- Delta-time, math channels and section timing are validated against MoTeC i2
  output on the same lap where possible — we have i2 and real `.ld` logs, so
  "looks about right" is not an acceptable standard.
- Fixtures stay small and curated. Full sessions never get committed.

## Performance contract (M4 onward)

Regressions here fail CI, they are not warnings.

| Metric | Budget |
|---|---|
| Pan/zoom on 20M samples | 60 fps |
| First frame of a 1-hour session | < 2 s |
| Agent to browser latency (LAN) | < 250 ms |
| Tab memory, 1-hour session | < 800 MB |

Min/max decimation per pixel column must preserve outliers exactly. Losing a
brake pressure spike to downsampling defeats the purpose of the tool.

## Commits

Conventional commits, one meaningful unit of work each. Scopes: `agent`, `hub`,
`web`, `schema`, `ci`, `docs`, `packaging`.

## Decisions already made

See `PLAN.md` for the full record. Summary:

- M1 targets **Le Mans Ultimate**, not F1 25.
- Hub runs locally; the remote strategist connects over **Tailscale**. No VPS,
  no nginx/caddy, no docker.
- Access is team-only: room code plus roles. No public spectator mode.
- Track and car names are normalised to a shared reference, with the raw
  per-game name preserved alongside.
