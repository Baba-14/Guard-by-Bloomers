# Guard MVP

## Outcome

Guard helps a person pause before acting on suspicious digital or payment
activity. The MVP accepts seven evidence types, evaluates independent warning signals, returns an
explainable risk assessment, and records the result for authorized review.

## Included now

- Message, screenshot text, URL, number, WhatsApp, payment and call submission.
- Browser-side screenshot OCR; the original screenshot is not uploaded by checks.
- Word-boundary-aware deterministic message rules.
- Local URL-shape checks for shortened, insecure, encoded, IP-based, and
  misleading hosted links.
- Optional Jev classification and scoring as a supporting signal.
- A Guard-owned risk engine with explicit thresholds and an AI contribution cap.
- `Low Risk`, `Caution`, and `High Risk` results with reasons and safer actions.
- Best-effort persistence of checks, results, provider metadata, and evidence.
- Authenticated user history for owned checks.
- Anonymous or authenticated fraud-report intake and analyst status review.
- Moderated domain-reputation evidence from the Guard database.
- Verified URL, phone and WhatsApp reputation evidence from the Guard database.
- An analyst-only API for reviewing recent checks.
- Regression tests for core scoring and false-positive behavior.

## Definition of done

1. Guard works without a Jev key and reports that only local checks were used.
2. A Jev timeout or API error does not prevent a result.
3. A single external AI provider cannot independently produce `High Risk`.
4. Every displayed warning maps to stored evidence and a source.
5. Lower-risk wording never claims that a submission is safe.
6. Examples for every enabled mode pass their expected bands.

## Next

- Connect a dedicated URL-reputation provider.
- Connect the admin UI to `GET /v1/admin/checks`.
- Connect the report and history screens to the implemented APIs.
- Add richer known-pattern matching after the evaluation schema is approved.
- Evaluate screenshot OCR quality before including it in a public demo.

## Later

Browser extensions, automatic monitoring, evidence storage, and third-party
messaging integrations remain outside the MVP until detection performance is measured.
