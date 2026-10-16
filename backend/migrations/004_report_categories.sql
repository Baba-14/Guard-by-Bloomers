-- Keep the public report form and intelligence reporting taxonomy aligned.
begin;

insert into public.fraud_categories(name, slug, description) values
  ('Fake Payment Alert or Screenshot', 'fake-payment-alert-or-screenshot', 'Fabricated or manipulated payment confirmation'),
  ('Wrong Transfer or Reversal Request', 'wrong-transfer-or-reversal-request', 'Requests to return or reverse a supposedly mistaken transfer'),
  ('WhatsApp Account Takeover', 'whatsapp-account-takeover', 'Compromised WhatsApp accounts used to request money or information'),
  ('WhatsApp Impersonation', 'whatsapp-impersonation', 'WhatsApp accounts pretending to be a trusted person or organisation'),
  ('OTP or Verification Code Request', 'otp-or-verification-code-request', 'Attempts to obtain one-time passwords or verification codes'),
  ('Bank Impersonation', 'bank-impersonation', 'People or messages pretending to represent a bank'),
  ('Fake Online Shop', 'fake-online-shop', 'Fraudulent shops, merchants or product listings'),
  ('Other', 'other', 'Reported fraud that does not yet match a specific category')
on conflict (slug) do update set
  name = excluded.name,
  description = excluded.description;

commit;
