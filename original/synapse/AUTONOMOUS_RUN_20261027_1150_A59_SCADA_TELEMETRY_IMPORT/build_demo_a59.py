"""Build one clearly synthetic, reproducible SCADA import example."""
from pathlib import Path
from test_a59 import fixture
from a59_scada_ingest import ingest
import json

root = Path(__file__).resolve().parent
inputs = root / "DEMO_SYNTHETIC_INPUT"
output = root / "DEMO_SYNTHETIC_NORMALIZED"
if inputs.exists() or output.exists():
    raise SystemExit("DEMO_EXISTS_REFUSE_OVERWRITE")
inputs.mkdir()
raw, mapping, _, _ = fixture(inputs)
proof = ingest(raw, mapping, output)
print(json.dumps({"demo": "SYNTHETIC_NOT_EQUIPMENT", "input": str(inputs),
                  "output": str(output), "rows": proof["rows"],
                  "physical_release": False}, indent=2))
