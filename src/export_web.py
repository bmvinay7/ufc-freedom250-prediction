"""Write docs/data.js from outputs/predictions.json so the dashboard works by
simply opening docs/index.html (no server / no fetch / no CORS), and so GitHub
Pages can serve it straight from the /docs folder."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.load(open(ROOT / "outputs" / "predictions.json"))
js = "window.PREDICTIONS = " + json.dumps(data, indent=2) + ";\n"
(ROOT / "docs" / "data.js").write_text(js)
print(f"wrote docs/data.js ({len(js):,} bytes)")
