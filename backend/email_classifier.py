"""Deterministic classifier for the MVP academic email assistant."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re

ACADEMIC_REAL_HUMAN_EMAIL = "academic_real_human_email"
ADVERTISEMENT_OR_NEWSLETTER = "advertisement_or_newsletter"
SYSTEM_NOTIFICATION = "system_notification"
SPAM_OR_IRRELEVANT = "spam_or_irrelevant"


@dataclass(frozen=True)
class ClassificationResult:
    label: str
    confidence: float
    reasons: list[str]
    should_generate_reply: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


NEWSLETTER_MARKERS = (
    "unsubscribe",
    "newsletter",
    "mailing list",
    "webinar",
    "limited time",
    "promotion",
    "subscribe",
    "digest",
    "view in browser",
    "退订",
    "订阅",
    "促销",
)

SYSTEM_MARKERS = (
    "no-reply",
    "noreply",
    "do not reply",
    "automated notification",
    "calendar notification",
    "submission received",
    "password reset",
    "ticket #",
    "系统通知",
    "自动通知",
)

SPAM_MARKERS = (
    "wire transfer",
    "crypto",
    "lottery",
    "urgent payment",
    "gift card",
    "click here to verify",
    "bitcoin",
    "prince",
    "发票异常",
    "中奖",
)

ACADEMIC_MARKERS = (
    "professor",
    "dr.",
    "research",
    "paper",
    "manuscript",
    "conference",
    "journal",
    "review",
    "course",
    "seminar",
    "collaboration",
    "lab",
    "advisor",
    "recommendation letter",
    "office hour",
    "thesis",
    "dissertation",
    "dataset",
    "教授",
    "博士",
    "论文",
    "研究",
    "课程",
    "合作",
    "会议",
    "推荐信",
)

HUMAN_MARKERS = (
    "dear",
    "hello",
    "hi ",
    "best regards",
    "sincerely",
    "thanks",
    "thank you",
    "would you",
    "could you",
    "i am",
    "we are",
    "您好",
    "谢谢",
    "请问",
)


def _count_markers(text: str, markers: tuple[str, ...]) -> int:
    lowered = text.lower()
    return sum(1 for marker in markers if marker in lowered)


def _sender_looks_automated(text: str) -> bool:
    header_match = re.search(r"^from:\s*(.+)$", text, flags=re.IGNORECASE | re.MULTILINE)
    if not header_match:
        return False
    sender = header_match.group(1).lower()
    return any(marker in sender for marker in ("no-reply", "noreply", "notification", "mailer-daemon"))


def classify_email(raw_email: str) -> ClassificationResult:
    """Classify a message and decide whether a reply draft is allowed."""
    text = raw_email.strip()
    if not text:
        return ClassificationResult(
            label=SPAM_OR_IRRELEVANT,
            confidence=0.9,
            reasons=["Empty input is not a real academic email."],
            should_generate_reply=False,
        )

    newsletter_score = _count_markers(text, NEWSLETTER_MARKERS)
    system_score = _count_markers(text, SYSTEM_MARKERS) + (2 if _sender_looks_automated(text) else 0)
    spam_score = _count_markers(text, SPAM_MARKERS)
    academic_score = _count_markers(text, ACADEMIC_MARKERS)
    human_score = _count_markers(text, HUMAN_MARKERS)

    reasons: list[str] = []
    if system_score >= 2:
        reasons.append("Automated sender or system-notification wording detected.")
        return ClassificationResult(SYSTEM_NOTIFICATION, min(0.95, 0.65 + system_score * 0.08), reasons, False)
    if spam_score >= 1 and academic_score == 0:
        reasons.append("Spam or phishing-like terms detected without academic context.")
        return ClassificationResult(SPAM_OR_IRRELEVANT, min(0.95, 0.7 + spam_score * 0.08), reasons, False)
    if newsletter_score >= 2 and human_score <= 1:
        reasons.append("Newsletter, mailing-list, or promotional markers detected.")
        return ClassificationResult(ADVERTISEMENT_OR_NEWSLETTER, min(0.95, 0.65 + newsletter_score * 0.06), reasons, False)
    if academic_score >= 1 and human_score >= 1:
        reasons.append("Academic topic markers and human correspondence markers detected.")
        return ClassificationResult(
            ACADEMIC_REAL_HUMAN_EMAIL,
            min(0.92, 0.55 + academic_score * 0.06 + human_score * 0.04),
            reasons,
            True,
        )

    reasons.append("Insufficient evidence of genuine academic human correspondence.")
    return ClassificationResult(SPAM_OR_IRRELEVANT, 0.6, reasons, False)
