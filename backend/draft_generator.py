"""Draft generation for genuine academic emails.

This MVP uses transparent templates rather than a remote LLM. The templates are
conservative by design: they never invent facts, never send anything, and expose
placeholders for attachments or missing details that require user review.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from backend.email_classifier import ACADEMIC_REAL_HUMAN_EMAIL, ClassificationResult
from backend.user_profile import UserRules


@dataclass(frozen=True)
class DraftBundle:
    draft_1_concise: str
    draft_2_warm: str
    missing_info_checklist: list[str]


def _extract_sender_name(raw_email: str) -> str:
    from_match = re.search(r"^from:\s*([^<\n]+)", raw_email, flags=re.IGNORECASE | re.MULTILINE)
    if from_match:
        name = from_match.group(1).strip().strip('"')
        if name and "@" not in name:
            return name
    greeting_match = re.search(r"(?:best|sincerely|regards|thanks),?\s*\n\s*([A-Z][A-Za-z .'-]+)", raw_email)
    if greeting_match:
        return greeting_match.group(1).strip()
    return "Professor/Dr. [Last Name]"


def _subject_hint(raw_email: str) -> str:
    subject_match = re.search(r"^subject:\s*(.+)$", raw_email, flags=re.IGNORECASE | re.MULTILINE)
    if subject_match:
        return subject_match.group(1).strip()
    return "your message"


def _detect_requested_actions(raw_email: str) -> list[str]:
    lowered = raw_email.lower()
    actions: list[str] = []
    if any(term in lowered for term in ("meet", "zoom", "call", "office hour", "面谈", "会议")):
        actions.append("confirm whether you want to propose specific meeting times")
    if any(term in lowered for term in ("cv", "resume", "proposal", "transcript", "attachment", "attach", "附件", "材料")):
        actions.append("attach the requested file or keep the attachment placeholder")
    if any(term in lowered for term in ("deadline", "by friday", "by monday", "due", "截止")):
        actions.append("verify any deadline before sending")
    if any(term in lowered for term in ("recommendation", "reference letter", "推荐信")):
        actions.append("confirm recommender details, deadline, and submission link")
    return actions


def build_missing_info_checklist(raw_email: str, rules: UserRules, optional_context: str = "") -> list[str]:
    """Return items the user should verify before sending."""
    checklist = [
        "Review and edit the draft manually before sending; this tool never sends email.",
        "Confirm the recipient's correct title and last name.",
    ]
    checklist.extend(_detect_requested_actions(raw_email))

    if rules.mention_attachment and "attach" not in optional_context.lower() and "附件" not in optional_context:
        checklist.append("Add the required attachment manually or leave the [attach file here] placeholder.")
    if rules.proactively_suggest_meeting and not any(day in optional_context.lower() for day in ("monday", "tuesday", "wednesday", "thursday", "friday", "周一", "周二", "周三", "周四", "周五")):
        checklist.append("Add real availability before proposing a meeting time.")
    if not optional_context.strip():
        checklist.append("Add optional context if the reply needs facts about your work, schedule, paper, or role.")
    return list(dict.fromkeys(checklist))


def _language_note(rules: UserRules) -> str:
    if rules.language_preference == "Chinese":
        return "（请在发送前根据需要改成中文正式邮件措辞。）"
    if "Bilingual" in rules.language_preference:
        return "（可保留英文版本，并按需补充中文说明。）"
    return ""


def _attachment_sentence(rules: UserRules, optional_context: str) -> str:
    if not rules.mention_attachment:
        return ""
    lowered_context = optional_context.lower()
    provided_markers = ("attachment provided", "file provided", "already attached", "attached file provided", "附件已提供")
    if any(marker in lowered_context for marker in provided_markers) or "附件已提供" in optional_context:
        return "I have included the relevant attachment for your review."
    return "I will include the relevant file here: [attach file here]."


def _meeting_sentence(rules: UserRules, warm: bool) -> str:
    if not rules.proactively_suggest_meeting:
        return ""
    if warm:
        return "If it would be helpful, I would be glad to find a time to discuss this further at your convenience."
    return "If useful, I can also follow up with a brief meeting at a time that works for you."


def _context_sentence(optional_context: str) -> str:
    context = optional_context.strip()
    if not context:
        return ""
    return f"For context, {context}"


def _compose_draft(raw_email: str, rules: UserRules, optional_context: str, *, warm: bool) -> str:
    sender = _extract_sender_name(raw_email)
    subject = _subject_hint(raw_email)
    salutation = rules.salutation_format.replace("[Last Name]", sender.split()[-1] if sender else "[Last Name]")
    language_note = _language_note(rules)

    context_sentence = _context_sentence(optional_context)
    attachment_sentence = _attachment_sentence(rules, optional_context)
    meeting_sentence = _meeting_sentence(rules, warm)

    if warm:
        body_lines = [
            f"Thank you very much for your message about {subject}.",
            "I appreciate you reaching out and would be happy to continue the conversation.",
        ]
    else:
        body_lines = [
            f"Thank you for your message about {subject}.",
            "I appreciate the update and am glad to respond.",
        ]

    for sentence in (context_sentence, attachment_sentence, meeting_sentence):
        if sentence:
            body_lines.append(sentence)

    body_lines.append(
        "Please let me know if there are specific details you would like me to address."
        if warm
        else "Please let me know if you would like any additional information."
    )

    if language_note:
        body_lines.append(language_note)

    return "\n\n".join([salutation, "\n".join(body_lines), rules.signature])


def generate_drafts(
    raw_email: str,
    rules: UserRules,
    classification: ClassificationResult,
    optional_context: str = "",
) -> DraftBundle:
    """Generate two safe editable drafts for academic human emails only."""
    checklist = build_missing_info_checklist(raw_email, rules, optional_context)
    if classification.label != ACADEMIC_REAL_HUMAN_EMAIL or not classification.should_generate_reply:
        return DraftBundle(
            draft_1_concise="No draft generated because the email was not classified as a genuine academic human email.",
            draft_2_warm="No draft generated because the email was not classified as a genuine academic human email.",
            missing_info_checklist=checklist,
        )

    return DraftBundle(
        draft_1_concise=_compose_draft(raw_email, rules, optional_context, warm=False),
        draft_2_warm=_compose_draft(raw_email, rules, optional_context, warm=True),
        missing_info_checklist=checklist,
    )


def revise_draft(existing_draft: str, user_feedback: str) -> str:
    """Return a conservative revision note plus the original draft for MVP editing."""
    unsafe_terms = ("pretend", "fabricate", "fake", "冒充", "伪造", "编造")
    if any(term in user_feedback.lower() for term in unsafe_terms):
        return (
            "I cannot revise the draft to include deceptive or fabricated academic claims. "
            "Please provide truthful details to add.\n\n"
            + existing_draft
        )
    return (
        "Revision request noted. Please edit the draft below according to this feedback while verifying all facts: "
        f"{user_feedback}\n\n{existing_draft}"
    )
