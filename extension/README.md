# Browser Extension Placeholder

This directory is reserved for a future Chrome Extension Manifest V3 prototype.
The MVP intentionally starts with a local CLI and optional FastAPI endpoint so
classification, safety boundaries, and draft quality can be validated before
connecting to Gmail UI surfaces.

Planned flow:
1. User highlights or imports a Gmail thread.
2. Extension sends the visible email text and user rules to the local/backend API.
3. Extension displays classification plus two editable drafts.
4. User manually copies/edits the selected draft and sends it in Gmail.

The extension must never call Gmail's send API automatically.
