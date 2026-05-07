from backend.email_classifier import (
    ACADEMIC_REAL_HUMAN_EMAIL,
    ADVERTISEMENT_OR_NEWSLETTER,
    SYSTEM_NOTIFICATION,
    classify_email,
)


def test_classifies_real_academic_human_email():
    email = """From: Dr. Rivera <rivera@example.edu>
Subject: Manuscript review

Dear Sam,
Could you review the attached manuscript draft for our conference panel?
Thank you,
Dr. Rivera
"""
    result = classify_email(email)
    assert result.label == ACADEMIC_REAL_HUMAN_EMAIL
    assert result.should_generate_reply is True
    assert result.confidence > 0.5


def test_classifies_newsletter_without_generating_reply():
    email = """Subject: Weekly AI Research Newsletter

View in browser. Subscribe to our webinar digest. Unsubscribe here.
"""
    result = classify_email(email)
    assert result.label == ADVERTISEMENT_OR_NEWSLETTER
    assert result.should_generate_reply is False


def test_classifies_system_notification_without_generating_reply():
    email = """From: no-reply@conference.org
Subject: Submission received

This is an automated notification. Do not reply.
"""
    result = classify_email(email)
    assert result.label == SYSTEM_NOTIFICATION
    assert result.should_generate_reply is False
