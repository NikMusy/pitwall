# Le Mans Ultimate / rFactor 2 setup

PitWall reads LMU telemetry from Windows shared memory. The game does not
expose it on its own — it is written there by a third-party plugin that you
install yourself.

## Install the shared memory plugin

LMU is built on the rFactor 2 engine and uses the same plugin. There is no
LMU-specific build; the stock one works.

1. Download `rf2_sm_tools_3.7.15.1.zip` from
   [TheIronWolfModding/rF2SharedMemoryMapPlugin](https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin).
2. Copy `rFactor2SharedMemoryMapPlugin64.dll` into:
   ```
   ...\steamapps\common\Le Mans Ultimate\Plugins\
   ```
3. Start LMU once, then quit it.
4. Check that the plugin registered itself in:
   ```
   ...\Le Mans Ultimate\UserData\player\CustomPluginVariables.JSON
   ```
   It should now contain an entry like:
   ```json
   "rFactor2SharedMemoryMapPlugin64.dll": {
     " Enabled": 1
   }
   ```
   The leading space in `" Enabled"` is not a typo — that is the key the game
   writes.

## If the entry never appears

This is the common failure and it is almost always missing runtimes: LMU cannot
load the DLL, so it silently skips it rather than reporting an error.

Install **all four** redistributables from the game's own `Support` folder:

```
...\Le Mans Ultimate\Support\vcredist_2012_x64.exe
...\Le Mans Ultimate\Support\vcredist_2012_x86.exe
...\Le Mans Ultimate\Support\vcredist_2013_x64.exe
...\Le Mans Ultimate\Support\vcredist_2013_x86.exe
```

Then restart LMU and re-check the JSON. As a last resort the entry can be added
by hand, but if the runtimes were the problem the plugin still will not load.

## Verifying

With LMU running and a car on track:

```bash
uv run pitwall-agent doctor
```

This reports which shared memory sections are present and readable. It does not
guess: a section that is missing is reported as missing.

## Shared memory sections used

| Section | Rate | Purpose |
|---|---|---|
| `$rFactor2SMMP_Telemetry$` | 50–90 Hz | Per-vehicle physics: wheels, inputs, motion |
| `$rFactor2SMMP_Scoring$` | ~5 Hz | All cars on track — timing, sectors, pit state |
| `$rFactor2SMMP_Extended$` | low | Plugin state, session transitions |
| `$rFactor2SMMP_Rules$` | low | FCY/SC state, pit rules |

Scoring covers every car in the session, not just yours. That is the basis for
live timing and the whole strategy module, so the agent always reads all of it.

## A note on the plugin's double buffering

The plugin writes each section twice with a version counter before and after the
payload. A read where the two counters disagree caught a write in progress and
must be discarded and retried. Skipping this check produces frames that are
individually plausible and internally inconsistent — exactly the kind of bug
that never announces itself. The provider must implement it.

## Steam updates

A game update can wipe `Plugins\`. If telemetry stops after a patch, check that
the DLL is still there before debugging anything else.
