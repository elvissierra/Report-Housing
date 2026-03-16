import sys
from pathlib import Path

# backend/ modules use bare imports (e.g. `import schemas`, `import analysis.x`).
# Adding backend/ to sys.path allows those internal imports to resolve while
# tests import via the `backend.*` namespace from the project root.
sys.path.insert(0, str(Path(__file__).parent / "backend"))
