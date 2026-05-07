# automated-social-email

高效学术社交邮件沟通方法。

This repository is now an MVP prototype for an **academic email intelligent draft assistant**. It helps a scholar or student classify a real incoming academic email and generate two editable reply drafts. It is **not** a bulk email sender, marketing tool, or autonomous Gmail sender.

## Current repository contents

The original repository contained:

- `README.md`: short project title and Chinese description.
- `高效学术邮件沟通方法.txt`: academic email communication guidelines covering formal salutations, concise structure, attachment checks, follow-up etiquette, and academic integrity boundaries.

The MVP keeps that original text and adds a runnable Python prototype around the same principles.

## MVP scope

Supported now:

1. Local mock email input via text files.
2. Deterministic email classification into:
   - `academic_real_human_email`
   - `advertisement_or_newsletter`
   - `system_notification`
   - `spam_or_irrelevant`
3. Draft generation only for `academic_real_human_email`.
4. Two editable drafts:
   - concise professional version
   - warmer collaborative version
5. User writing rules such as salutation, politeness, concision, meeting suggestions, attachment mentions, language preference, and signature.
6. Safety checklist output for missing information and manual review.
7. Optional FastAPI app for future browser/Gmail integration when dependencies are installed.

Not supported yet:

- Gmail OAuth or Gmail API integration.
- Chrome Extension content script integration.
- Automatic sending. This is intentionally forbidden.
- Remote LLM calls. Prompts are prepared, but the default MVP uses transparent local templates.

## Repository structure

```text
backend/
  email_classifier.py   # heuristic classifier and output schema
  draft_generator.py    # safe two-version draft generation and revision guard
  user_profile.py       # free-form user rule parsing
  prompts.py            # system/classification/generation/revision prompts
  main.py               # CLI plus optional FastAPI app
extension/
  README.md             # browser extension plan and safety note
examples/
  sample_incoming_emails/incoming_email.txt
  sample_user_rules.txt
  optional_context.txt
  generated_drafts/     # demo output directory
tests/
  test_classifier.py
  test_draft_generator.py
高效学术邮件沟通方法.txt
```

## Safety boundaries

The assistant must:

- Never automatically send email.
- Never generate deceptive, impersonating, or forged academic identity content.
- Never invent papers, results, positions, affiliations, advisor relationships, funding, or commitments.
- Use `[attach file here]` if an attachment is needed but not actually provided.
- Be conservative when information is missing and list what the user should verify.

## Run the local demo

The CLI uses only the Python standard library for the core flow.

```bash
python -m backend.main \
  --incoming-email examples/sample_incoming_emails/incoming_email.txt \
  --user-rules examples/sample_user_rules.txt \
  --optional-context examples/optional_context.txt \
  --output-dir examples/generated_drafts
```

Expected outputs:

- `examples/generated_drafts/classification_result.json`
- `examples/generated_drafts/draft_1_concise.txt`
- `examples/generated_drafts/draft_2_warm.txt`
- `examples/generated_drafts/missing_info_checklist.txt`

## Optional FastAPI usage

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the API:

```bash
uvicorn backend.main:app --reload
```

POST `/draft` with JSON:

```json
{
  "incoming_email": "From: Professor Smith ...",
  "user_rules": "Salutation: Dear Professor [Last Name],\nMention attachment: yes",
  "optional_context": "I can meet Tuesday afternoon."
}
```

The response includes classification, two drafts, a missing-info checklist, and a safety notice.

## Test

```bash
python -m pytest
```

## Next steps

1. Replace heuristic draft templates with an LLM adapter that uses `backend/prompts.py` exactly as safety guardrails.
2. Add Gmail read-only OAuth flow or a browser extension importer.
3. Store per-user writing rules locally and allow editing from a simple UI.
4. Add a draft-review screen with copy buttons and explicit manual-send warnings.
5. Expand tests with more academic, newsletter, notification, and spam examples.
