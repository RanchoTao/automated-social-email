"""User writing rules for the academic email drafting MVP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class UserRules:
    """Normalized user preferences used by the draft generator."""

    salutation_format: str = "Dear Professor/Dr. [Last Name],"
    politeness_level: str = "professional"
    be_concise: bool = True
    proactively_suggest_meeting: bool = False
    mention_attachment: bool = False
    language_preference: str = "English"
    signature: str = "Sincerely,\n[Your Full Name]"
    extra_rules: str = ""


def _flag(text: str, positive_markers: tuple[str, ...], negative_markers: tuple[str, ...] = ()) -> bool:
    lowered = text.lower()
    if any(marker in lowered for marker in negative_markers):
        return False
    return any(marker in lowered for marker in positive_markers)


def parse_user_rules(raw_rules: str) -> UserRules:
    """Parse a free-form rules file into conservative defaults.

    This intentionally accepts simple text rather than a rigid config format so
    early users can paste their own academic-email style notes.
    """
    text = raw_rules.strip()
    lowered = text.lower()

    salutation = "Dear Professor/Dr. [Last Name],"
    for line in text.splitlines():
        if "称呼" in line or "salutation" in line.lower() or "greeting" in line.lower():
            _, _, value = line.partition(":" if ":" in line else "：")
            if value.strip():
                salutation = value.strip()

    if "中文" in text and "英文" in text:
        language = "Bilingual Chinese and English"
    elif "中文" in text or "chinese" in lowered:
        language = "Chinese"
    elif "bilingual" in lowered or "双语" in text:
        language = "Bilingual Chinese and English"
    else:
        language = "English"

    signature = "Sincerely,\n[Your Full Name]"
    for line in text.splitlines():
        if "signature" in line.lower() or "署名" in line:
            _, _, value = line.partition(":" if ":" in line else "：")
            if value.strip():
                signature = value.strip().replace("\\n", "\n")

    return UserRules(
        salutation_format=salutation,
        politeness_level="warm" if ("warm" in lowered or "礼貌" in text) else "professional",
        be_concise=not _flag(text, ("detailed", "详细", "展开"), ()),
        proactively_suggest_meeting=_flag(
            text,
            ("meeting", "zoom", "office hour", "主动提出 meeting", "面谈", "会议"),
            ("no meeting", "不要主动", "不主动提出 meeting"),
        ),
        mention_attachment=_flag(text, ("attachment", "附件", "attach"), ("no attachment", "不提附件")),
        language_preference=language,
        signature=signature,
        extra_rules=text,
    )


def load_user_rules(path: str | Path) -> UserRules:
    """Load user rules from a text file."""
    return parse_user_rules(Path(path).read_text(encoding="utf-8"))
