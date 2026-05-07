from backend.draft_generator import generate_drafts, revise_draft
from backend.email_classifier import classify_email
from backend.user_profile import parse_user_rules

ACADEMIC_EMAIL = """From: Professor Elena Smith <elena.smith@example.edu>
Subject: Follow-up on your research proposal

Dear Alex,
Could you send a PDF proposal and let me know whether you are available next week for a brief Zoom conversation?

Best regards,
Elena Smith
"""


def test_generates_two_drafts_for_academic_email():
    rules = parse_user_rules(
        """Salutation: Dear Professor [Last Name],
Proactively suggest meeting: yes
Mention attachment: yes
Signature: Sincerely,\\nAlex Chen
"""
    )
    classification = classify_email(ACADEMIC_EMAIL)
    drafts = generate_drafts(ACADEMIC_EMAIL, rules, classification, "I can meet Tuesday afternoon.")

    assert "Dear Professor Smith," in drafts.draft_1_concise
    assert "Thank you" in drafts.draft_1_concise
    assert "I have included the relevant attachment" not in drafts.draft_1_concise
    assert "[attach file here]" in drafts.draft_1_concise
    assert drafts.draft_1_concise != drafts.draft_2_warm
    assert any("Review and edit" in item for item in drafts.missing_info_checklist)


def test_does_not_generate_draft_for_newsletter():
    email = "Newsletter digest. View in browser. Unsubscribe now. Subscribe for more webinars."
    rules = parse_user_rules("Language: English")
    classification = classify_email(email)
    drafts = generate_drafts(email, rules, classification)

    assert drafts.draft_1_concise.startswith("No draft generated")
    assert drafts.draft_2_warm.startswith("No draft generated")


def test_revision_rejects_fabrication_request():
    revised = revise_draft("Dear Professor,\nThank you.", "Please fabricate a Nature paper.")
    assert "cannot" in revised.lower()
    assert "fabricated" in revised.lower()
