"""CLI and optional FastAPI entrypoint for the academic email assistant MVP."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from backend.draft_generator import DraftBundle, generate_drafts
from backend.email_classifier import classify_email
from backend.user_profile import parse_user_rules


def _create_api_app() -> Any:
    """Create a FastAPI app when optional web dependencies are installed."""
    fastapi_module = importlib.import_module("fastapi")
    pydantic_module = importlib.import_module("pydantic")
    fast_api = fastapi_module.FastAPI
    base_model = pydantic_module.BaseModel

    class DraftRequest(base_model):
        incoming_email: str
        user_rules: str
        optional_context: str = ""

    api_app = fast_api(
        title="Academic Email Draft Assistant MVP",
        description="Classifies academic emails and generates editable reply drafts without sending anything.",
        version="0.1.0",
    )

    @api_app.post("/draft")
    def create_draft(request: DraftRequest) -> dict[str, object]:
        rules = parse_user_rules(request.user_rules)
        classification = classify_email(request.incoming_email)
        drafts = generate_drafts(request.incoming_email, rules, classification, request.optional_context)
        return {
            "classification": classification.to_dict(),
            "draft_1_concise": drafts.draft_1_concise,
            "draft_2_warm": drafts.draft_2_warm,
            "missing_info_checklist": drafts.missing_info_checklist,
            "safety_notice": "Drafts are editable text only. This tool never sends email automatically.",
        }

    return api_app


app = _create_api_app() if importlib.util.find_spec("fastapi") and importlib.util.find_spec("pydantic") else None


def _read_optional(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8")


def _write_outputs(output_dir: Path, classification: dict[str, object], drafts: DraftBundle) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "classification_result.json").write_text(
        json.dumps(classification, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "draft_1_concise.txt").write_text(drafts.draft_1_concise + "\n", encoding="utf-8")
    (output_dir / "draft_2_warm.txt").write_text(drafts.draft_2_warm + "\n", encoding="utf-8")
    (output_dir / "missing_info_checklist.txt").write_text(
        "\n".join(f"- {item}" for item in drafts.missing_info_checklist) + "\n",
        encoding="utf-8",
    )


def run_demo(incoming_email_path: str, user_rules_path: str, optional_context_path: str | None, output_dir: str) -> None:
    incoming_email = Path(incoming_email_path).read_text(encoding="utf-8")
    raw_rules = Path(user_rules_path).read_text(encoding="utf-8")
    optional_context = _read_optional(optional_context_path)

    rules = parse_user_rules(raw_rules)
    classification = classify_email(incoming_email)
    drafts = generate_drafts(incoming_email, rules, classification, optional_context)
    _write_outputs(Path(output_dir), classification.to_dict(), drafts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate safe academic email reply drafts.")
    parser.add_argument("--incoming-email", required=True, help="Path to incoming_email.txt")
    parser.add_argument("--user-rules", required=True, help="Path to user_rules.txt")
    parser.add_argument("--optional-context", help="Path to optional_context.txt")
    parser.add_argument("--output-dir", default="examples/generated_drafts", help="Directory for generated outputs")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_demo(args.incoming_email, args.user_rules, args.optional_context, args.output_dir)
    print(f"Draft outputs written to {args.output_dir}")
    print("Safety notice: this MVP never sends emails automatically.")


if __name__ == "__main__":
    main()
