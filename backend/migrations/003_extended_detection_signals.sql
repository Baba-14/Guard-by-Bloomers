begin;

insert into public.fraud_signals (key, name, weight, severity) values
  ('impersonation_claim', 'Institution or Authority Impersonation', 16, 'medium'),
  ('secrecy_request', 'Secrecy Request', 14, 'medium'),
  ('momo_reversal', 'Mobile Money Reversal Story', 32, 'high'),
  ('fake_payment_claim', 'Unverified Payment Claim', 28, 'high'),
  ('account_takeover', 'Possible Account Takeover', 24, 'high'),
  ('unusual_payment_destination', 'Changed Payment Destination', 18, 'high'),
  ('known_risky_url', 'Verified Risky URL', 60, 'critical'),
  ('known_risky_phone', 'Verified Risky Phone Number', 60, 'critical')
on conflict (key) do update set
  name = excluded.name,
  weight = excluded.weight,
  severity = excluded.severity,
  active = true;

commit;
