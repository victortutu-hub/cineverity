"""Export the canonical ResearchEvidenceContract v0.1 JSON Schema."""

import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.contracts.research_evidence import ResearchEvidenceContract


def canonical_schema_text() -> str:
    """Return the deterministic canonical JSON Schema representation."""
    return (
        json.dumps(
            ResearchEvidenceContract.model_json_schema(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )


def export_schema() -> Path:
    """Generate and write the checked-in canonical Research schema artifact."""
    output_path = project_root / "schemas" / "research-evidence-contract-v0.1.schema.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical_schema_text().encode("utf-8"))
    print(f"Successfully exported JSON schema to {output_path.relative_to(project_root)}")
    return output_path


if __name__ == "__main__":
    export_schema()
