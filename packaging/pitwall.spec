# PyInstaller spec. Build with: uv run pyinstaller packaging/pitwall.spec
#
# --onedir, not --onefile. Onefile unpacks to a temp directory on every start,
# which is slow and is a reliable way to get flagged by Defender.

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

SPEC_DIR = Path(SPECPATH).resolve()
REPO_ROOT = SPEC_DIR.parent
WEB_DIST = REPO_ROOT / "apps" / "web" / "dist"

if not (WEB_DIST / "index.html").is_file():
    raise SystemExit(
        "apps/web/dist is missing. Build the UI first:\n"
        "  npm run build --workspace @pitwall/web"
    )

# uvicorn and websockets resolve their implementations at runtime, so the
# static analyser cannot see them.
hidden = (
    collect_submodules("uvicorn")
    + collect_submodules("websockets")
    + collect_submodules("webview")
    + ["anyio", "msgpack", "clr_loader", "pythonnet"]
)

analysis = Analysis(
    [str(SPEC_DIR / "entry.py")],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=[(str(WEB_DIST), "web")],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy.testing"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    exclude_binaries=True,
    name="PitWall",
    # No console window: double-clicking must open the app, not a terminal.
    console=False,
    debug=False,
    strip=False,
    upx=False,
)

# Same program, console attached. Without it a frozen crash is invisible:
# the windowed build has nowhere to print a traceback.
debug_exe = EXE(
    pyz,
    analysis.scripts,
    exclude_binaries=True,
    name="PitWall-console",
    console=True,
    debug=False,
    strip=False,
    upx=False,
)

COLLECT(
    exe,
    debug_exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="PitWall",
)
