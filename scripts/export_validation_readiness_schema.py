"""Export the canonical ValidationReadinessContract v0.1 JSON Schema."""

import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.contracts.validation_readiness import ValidationReadinessContract


def canonical_schema_text() -> str:
    """Return the deterministic canonical JSON Schema representation."""
    return (
        json.dumps(
            ValidationReadinessContract.model_json_schema(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )


def export_schema(output_path: Path | None = None) -> Path:
    """Write canonical schema bytes as UTF-8 without a BOM."""
    if output_path is None:
        output_path = project_root / "schemas" / "validation-readiness-contract-v0.1.schema.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical_schema_text().encode("utf-8"))
    print(f"Successfully exported JSON schema to {output_path}")
    return output_path


if __name__ == "__main__":
    export_schema()
