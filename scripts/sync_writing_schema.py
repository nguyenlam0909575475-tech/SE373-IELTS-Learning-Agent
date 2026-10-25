"""Export Member 3's actual model; never generate a competing Pydantic model."""
import argparse
import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def export_schema(module_name, output, *, check=False, manifest=None):
    model = importlib.import_module(module_name).WritingAssessment
    schema = model.model_json_schema()
    output = Path(output)
    manifest_path = Path(manifest) if manifest is not None else None
    spec = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path is not None
        else None
    )
    if check:
        if json.loads(output.read_text(encoding="utf-8")) != schema:
            raise ValueError("Skill schema differs from Member 3 WritingAssessment")
        if spec is not None and spec["output"].get("json_schema") != schema:
            raise ValueError("skill.yaml schema differs from Member 3 WritingAssessment")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if spec is not None:
            spec["output"]["json_schema"] = schema
            spec["schema_authority"].update(
                status="Exported from the actual Member 3 model; run --check to detect drift.",
                module=module_name,
            )
            manifest_path.write_text(
                json.dumps(spec, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    return schema


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--module",
        default="src.agent.schemas",
        help="Import path for Person 3's authoritative schema",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "skills/writing-assessment/writing_assessment.schema.json",
    )
    parser.add_argument(
        "--manifest", type=Path, default=ROOT / "skills/writing-assessment/skill.yaml"
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        export_schema(args.module, args.output, check=args.check, manifest=args.manifest)
    except (ImportError, AttributeError, ValueError, OSError) as exc:
        parser.exit(
            1,
            f"Schema sync unavailable: {type(exc).__name__}. "
            "Merge Member 3's actual model first.\n",
        )
    print(
        "Member 3 WritingAssessment schema matches"
        if args.check
        else "Exported Member 3 WritingAssessment schema"
    )


if __name__ == "__main__":
    main()
