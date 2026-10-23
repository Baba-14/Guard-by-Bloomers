import Link from 'next/link';
import { ArrowRight, Braces, CheckCircle2, Copy, KeyRound, LockKeyhole, ShieldCheck, Zap } from 'lucide-react';
import { Footer, Header } from '@/components/Header';

const curlExample = `curl -X POST https://YOUR_GUARD_DOMAIN/api/v1/checks \\
  -H "Authorization: Bearer guard_test_your_key" \\
  -H "Idempotency-Key: order-review-4821" \\
  -H "Content-Type: application/json" \\
  -d '{
    "type": "message",
    "content": "Urgent: send your OTP to reverse the transfer.",
    "customer_reference": "customer-123",
    "metadata": { "channel": "support_chat" }
  }'`;

const responseExample = `{
  "request_id": "014a38c5-6af7-49e1-a7de-f3b3b3940371",
  "level": "High Risk",
  "score": 78,
  "signals": ["Requests a one-time password", "Creates urgency"],
  "explanation": "The message requests a security code and pressures the recipient to act.",
  "recommended_action": "Do not share the code. Contact the provider through its official channel.",
  "pattern": "Credential theft",
  "confidence": 0.92,
  "sources": ["guard_rules"],
  "check_id": "stored-check-id",
  "evidence": []
}`;

const kinds = [
  ['message', 'SMS, email, chat, or social message text'],
  ['link', 'A URL that should be assessed before opening'],
  ['number', 'A phone number requiring a reputation lookup'],
  ['whatsapp', 'A WhatsApp number or suspicious account context'],
  ['payment', 'A payment request or proof-of-payment description'],
  ['call', 'A description or transcript of a suspicious call'],
  ['screenshot', 'Text extracted from a screenshot on the client side'],
];

export default function DevelopersPage() {
  return <><Header/><main className="developers-page">
    <section className="developers-hero"><div className="container developers-hero-grid"><div><span className="eyebrow">Guard for developers</span><h1>Put fraud protection inside your customer experience.</h1><p>Use one explainable API to assess suspicious messages, links, numbers, calls, and payment requests before your customer acts.</p><div className="developers-actions"><a className="btn btn-primary" href="#quickstart">Read the quickstart <ArrowRight size={16}/></a><Link className="btn btn-outline" href="/business">Discuss a pilot</Link></div><div className="developers-trust"><span><ShieldCheck size={15}/> Versioned contract</span><span><LockKeyhole size={15}/> Hashed API keys</span><span><Zap size={15}/> Synchronous results</span></div></div><aside className="developers-terminal"><header><span/><span/><span/><b>POST /api/v1/checks</b></header><pre><code>{`{
  "type": "payment",
  "content": "Pay the release fee now...",
  "customer_reference": "case-4821"
}`}</code></pre><div className="developers-terminal-result"><span>200 OK</span><strong>High Risk · 72</strong><small>Recommended action included</small></div></aside></div></section>

    <section className="container developers-overview"><div className="developers-section-title"><span>API overview</span><h2>A small contract with enough context to act.</h2><p>Guard returns a risk assessment, the evidence behind it, and a safer next step your product can show immediately.</p></div><div className="developers-feature-grid"><article><Braces size={22}/><h3>One endpoint</h3><p>Send supported fraud evidence to a single versioned check endpoint.</p></article><article><KeyRound size={22}/><h3>Partner authentication</h3><p>Separate test and live API keys identify your organization and usage.</p></article><article><CheckCircle2 size={22}/><h3>Explainable results</h3><p>Every warning includes signals, evidence, confidence, and recommended action.</p></article></div></section>

    <section className="developers-docs" id="quickstart"><div className="container developers-docs-grid"><aside className="developers-sidebar"><strong>Documentation</strong><a href="#quickstart" className="active">Quickstart</a><a href="#authentication">Authentication</a><a href="#request">Request</a><a href="#response">Response</a><a href="#errors">Errors</a><a href="#privacy">Privacy</a></aside><div className="developers-content"><span className="developers-kicker">QUICKSTART</span><h2>Run your first fraud check</h2><p>Ask Guard to assess content at the point where your customer receives, reviews, or acts on it. Use a test key during development and a live key only in production.</p><div className="developers-callout"><ShieldCheck size={19}/><div><strong>Pilot access</strong><span>Partner keys are provisioned by Guard during onboarding. Self-service key management is coming next.</span></div></div>

      <h3 id="authentication">1. Authenticate your server</h3><p>Send the API key as a Bearer token. Keep it on your server—never place a live key in browser or mobile-app code.</p><div className="developers-code"><header><span>Authorization header</span><Copy size={14}/></header><pre><code>Authorization: Bearer guard_test_your_key</code></pre></div>

      <h3 id="request">2. Create a check</h3><p>Use an idempotency key when a network retry must not count as a second check. Customer references should be opaque identifiers rather than names, phone numbers, or email addresses.</p><div className="developers-code"><header><span>cURL</span><Copy size={14}/></header><pre><code>{curlExample}</code></pre></div>

      <div className="developers-table-wrap"><table><thead><tr><th>Field</th><th>Required</th><th>Description</th></tr></thead><tbody><tr><td><code>type</code></td><td>Yes</td><td>The evidence type Guard should evaluate.</td></tr><tr><td><code>content</code></td><td>Yes</td><td>1–20,000 characters. Never include passwords, PINs, OTPs, or full card data.</td></tr><tr><td><code>customer_reference</code></td><td>No</td><td>Your opaque reference, up to 128 characters.</td></tr><tr><td><code>metadata</code></td><td>No</td><td>Up to 20 short operational key/value pairs.</td></tr></tbody></table></div>

      <h3>Supported evidence types</h3><div className="developers-kind-grid">{kinds.map(([kind, copy])=><div key={kind}><code>{kind}</code><span>{copy}</span></div>)}</div>

      <h3 id="response">3. Use the result</h3><p>Show the risk level and recommended action together. Guard provides decision support—not a guarantee that content is safe or fraudulent.</p><div className="developers-code"><header><span>200 response</span><Copy size={14}/></header><pre><code>{responseExample}</code></pre></div>

      <h3 id="errors">Errors and request tracing</h3><div className="developers-table-wrap"><table><thead><tr><th>Status</th><th>Meaning</th></tr></thead><tbody><tr><td><code>400</code></td><td>Malformed idempotency key or request.</td></tr><tr><td><code>401</code></td><td>Missing, malformed, expired, revoked, or invalid API key.</td></tr><tr><td><code>403</code></td><td>Organization suspended or key scope not permitted.</td></tr><tr><td><code>422</code></td><td>Request fields failed validation.</td></tr><tr><td><code>429</code></td><td>The organization’s monthly quota was reached.</td></tr><tr><td><code>503</code></td><td>Guard could not complete or meter the request.</td></tr></tbody></table></div><p>Successful responses include <code>X-Guard-Request-Id</code>. Keep it when contacting support.</p>

      <h3 id="privacy">Privacy and data handling</h3><p>Raw partner submissions are not stored by default. Guard records a content hash, length, result, organization, usage information, and optional opaque references for audit and metering. Submitted content never enters training data automatically.</p><div className="developers-next"><div><span>Ready to embed Guard?</span><strong>Start with a controlled partner pilot.</strong></div><Link href="/business" className="btn btn-primary">Talk to Guard <ArrowRight size={15}/></Link></div>
    </div></div></section>
  </main><Footer/></>;
}
