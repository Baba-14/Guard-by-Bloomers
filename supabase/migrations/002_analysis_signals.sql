-- Signals emitted by the modular Guard analysis pipeline.
insert into public.fraud_signals (key, name, weight, severity) values
  ('insecure_url', 'Insecure URL', 8, 'low'),
  ('ip_address_url', 'IP Address URL', 22, 'high'),
  ('punycode_domain', 'Punycode Domain', 18, 'high'),
  ('shortened_url', 'Shortened URL', 20, 'medium'),
  ('url_credentials', 'Misleading URL Credentials', 25, 'high'),
  ('known_risky_domain', 'Moderated Risky Domain', 40, 'high'),
  ('jev_sensitive_request', 'Jev Sensitive Information Request', 22, 'high'),
  ('jev_urgency', 'Jev Coercive Urgency', 8, 'medium'),
  ('jev_payment_request', 'Jev Payment Request', 10, 'medium'),
  ('jev_risk', 'Jev Contextual Risk', 18, 'medium'),
  ('jev_category_credential_theft', 'Jev Credential Theft Category', 6, 'medium'),
  ('jev_category_advance_fee', 'Jev Advance Fee Category', 6, 'medium'),
  ('jev_category_impersonation', 'Jev Impersonation Category', 6, 'medium'),
  ('jev_category_investment_scam', 'Jev Investment Scam Category', 6, 'medium'),
  ('jev_category_account_takeover', 'Jev Account Takeover Category', 6, 'medium')
on conflict (key) do update set
  name = excluded.name,
  weight = excluded.weight,
  severity = excluded.severity,
  active = true;
