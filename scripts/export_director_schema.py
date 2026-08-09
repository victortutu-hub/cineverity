"""
Export script for Director Agent Contract v0.1 JSON Schema.

Exports the canonical JSON Schema generated directly from DirectorIntentContract.model_json_schema()
to schemas/director-intent-contract-v0.1.schema.json using deterministic canonical formatting.
"""

import json
from pathlib import Path
import sys

# Ensure project root is in sys.path when script is executed directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.contracts.director_intent import DirectorIntentContract


def export_schema() -> Path:
    """Generate and write the canonical JSON schema file."""
    # Source of truth: Pydantic v2 model_json_schema
    schema = DirectorIntentContract.model_json_schema()

    # Canonical serialization rule for byte-for-byte determinism
    canonical_json = (
        json.dumps(
            schema,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )

    # Determine workspace root relative to script location
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "schemas"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "director-intent-contract-v0.1.schema.json"
    output_path.write_text(canonical_json, encoding="utf-8")

    print(f"Successfully exported JSON schema to {output_path.relative_to(project_root)}")
    return output_path


if __name__ == "__main__":
    export_schema()
