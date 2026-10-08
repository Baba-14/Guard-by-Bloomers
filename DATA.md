# Guard Data Plan

## Labels

Each evaluation example should have:

- `submission_type`: `message` or `link`
- `language`: for example English, Twi, Ga, Ewe, or code-switched
- `expected_level`: lower risk, caution, or high risk
- `fraud_category`: credential theft, advance fee, impersonation, investment,
  account takeover, malicious link, or unknown
- `expected_signals`: observable warning signs supported by the content
- `source`: synthetic, public advisory, consented report, or moderated report
- `review_status`: unreviewed, reviewed, or disputed

## Initial Ghana-focused coverage

- Mobile Money reversal and advance-fee requests
- OTP, PIN, and password theft
- Bank, telecom, government, courier, and family-member impersonation
- Fake jobs, grants, prizes, investments, and delivery charges
- WhatsApp account-takeover requests
- Shortened and look-alike links
- Legitimate messages that use words such as “pay”, “urgent”, and “click”

## Handling requirements

- Remove names, phone numbers, account numbers, and other personal identifiers
  unless there is explicit consent and a documented operational need.
- Never treat an unmoderated community report as confirmed fraud.
- Keep source, review history, and label changes auditable.
- Use a held-out evaluation set when tuning weights or Jev questions.
- Measure false-positive and false-negative rates separately by language and
  fraud category.

Raw submitted content is not persisted by default. Set
`STORE_ANALYSIS_CONTENT=true` only for an approved environment with suitable
access controls and retention rules.
