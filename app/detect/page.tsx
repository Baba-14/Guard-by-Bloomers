import Link from 'next/link';
import { ArrowRight, BookOpen, Check, MessageCircle, Network, ScanSearch, ShieldCheck, TriangleAlert } from 'lucide-react';
import { Header, Footer } from '@/components/Header';
import { InlineFraudChecker } from '@/components/InlineFraudChecker';

const stages = [
  ['01','Something suspicious reaches you','A message, link, call, account, screenshot, or payment request does not feel right.'],
  ['02','Check the evidence','Add the message, link, number, account, screenshot, call, or payment details.'],
  ['03','Guard checks the signals','Warning patterns, context, and moderated community reports are brought together.'],
  ['04','Choose a safer next step','You get a plain-language risk explanation and practical guidance before you act.'],
] as const;

const patterns = [
  ['Mobile Money Fraud','A reversal story, false alert, or urgent transfer moves you before you confirm.','mobile-money-fraud'],
  ['WhatsApp Account Takeover','A familiar contact suddenly asks for money, an OTP, or secrecy.','whatsapp-account-takeover'],
  ['Phishing','A believable message or website tries to collect passwords, OTPs, or card details.','phishing'],
  ['OTP Theft','Someone asks for a code meant only for your login, reset, or payment.','otp-theft'],
  ['Fake Online Shops','A polished social page takes payment but does not deliver what was promised.','fake-online-shops'],
  ['Bank Impersonation','A caller creates fear about your account and asks for sensitive information.','bank-impersonation'],
] as const;

export default function Detect(){return <><Header/><main className="fraud-page">
  <section className="fraud-hero"><div className="container fraud-hero-grid"><div className="fraud-hero-copy"><span className="eyebrow">Fraud detection and decision support</span><h1>Check before you trust, click, or pay.</h1><p>Guard examines suspicious messages, links, phone numbers, WhatsApp accounts, calls, payment requests, and screenshots so you can understand the risk before acting.</p><div className="fraud-hero-actions"><Link href="#checks" className="btn btn-primary">Run a fraud check <ArrowRight size={16}/></Link><Link href="/reports" className="btn btn-outline">Report fraud</Link></div><div className="fraud-hero-trust"><ShieldCheck size={16}/> Get explainable guidance. No account needed.</div></div><div className="fraud-console" aria-label="Example Guard risk assessment"><div className="fraud-console-top"><span><img src="/images/guard-violet.png" alt=""/>Guard fraud review</span><b>Before you act</b></div><div className="fraud-console-score"><span className="fraud-console-ring"><strong>72</strong><small>risk score</small></span><div><span>Risk assessment</span><strong>Caution</strong><small>Pause and verify through a separate trusted channel.</small></div></div><div className="fraud-console-signals"><div><span><TriangleAlert size={15}/> Request pattern</span><b>Urgency detected</b></div><div><span><Network size={15}/> Identity signal</span><b>Details changed</b></div><div><span><MessageCircle size={15}/> Community signal</span><b>Related reports</b></div></div><div className="fraud-console-action"><Check size={15}/> Pause and verify through a trusted channel</div></div></div></section>

  <section className="fraud-proof"><div className="container fraud-proof-grid"><div><strong>Multi</strong><span>channel fraud checks</span></div><div><strong>7</strong><span>ways to add evidence</span></div><div><strong>1</strong><span>clear next action</span></div><div><strong>0</strong><span>PINs or OTPs required</span></div></div></section>

  <InlineFraudChecker/>

  <section className="fraud-journey"><div className="container"><div className="fraud-section-head fraud-section-head-light"><div><span className="eyebrow">Create a moment to verify</span><h2>Pause before suspicious activity becomes a loss.</h2></div><p>Fraud succeeds when pressure moves faster than verification. Guard creates a clear checkpoint before you reply, click, share information, send money, or release goods.</p></div><div className="fraud-stage-grid">{stages.map(([number,title,copy])=><article key={number}><span>{number}</span><h3>{title}</h3><p>{copy}</p></article>)}</div></div></section>

  <section className="container fraud-threats"><div className="fraud-threat-copy"><span className="eyebrow">Fraud coverage</span><h2>Recognise what is trying to earn your trust.</h2><p>Guard connects the content, identity details, requested action, and moderated community reports to explain why an interaction deserves a closer look.</p><ul><li><Check size={14}/> Phishing links, fake websites, and credential theft</li><li><Check size={14}/> WhatsApp takeover and impersonation requests</li><li><Check size={14}/> Fake payment alerts and Mobile Money reversal stories</li><li><Check size={14}/> Suspicious calls, numbers, screenshots, and online shops</li></ul><Link href="/learn" className="btn btn-outline">Explore fraud patterns <ArrowRight size={15}/></Link></div><div className="fraud-threat-panel"><div className="fraud-threat-panel-head"><ScanSearch size={20}/><span><strong>Guard connects the risk signals</strong><small>Evidence becomes a clearer decision</small></span></div><div className="fraud-threat-path"><span>Suspicious content</span><i/><span>Fraud pattern</span><i/><span>Community context</span></div><div className="fraud-threat-result"><ShieldCheck size={23}/><div><span>Before you act</span><strong>What raised concern, why it matters, and the safest next action.</strong></div></div></div></section>

  <section className="community-patterns fraud-pattern-library"><div className="container"><div className="community-patterns-head"><div><span className="eyebrow">Fraud pattern library</span><h2>Learn the pattern behind the story.</h2></div><p>Understand how common fraud works, what warning signs to notice, and what to do before you respond.</p></div><div className="community-pattern-grid">{patterns.map(([title,description,slug],index)=><Link href={'/learn/'+slug} className="community-pattern-card" key={title}><span>{String(index+1).padStart(2,'0')}</span><BookOpen size={20}/><h3>{title}</h3><p>{description}</p><b>Read the guide <ArrowRight size={13}/></b></Link>)}</div><div className="community-patterns-cta"><div><strong>Looking for another fraud type?</strong><span>Browse the full awareness library for more practical guides.</span></div><Link href="/learn" className="btn btn-primary">Explore all fraud patterns <ArrowRight size={15}/></Link></div></div></section>

  <section className="container fraud-report"><div><span className="eyebrow">Help protect someone else</span><h2>Already encountered fraud?</h2><p>Report the WhatsApp account, number, link, payment route, message, or call. Remove passwords, PINs, and OTPs before sharing.</p></div><Link href="/reports" className="btn btn-primary">Report fraud <ArrowRight size={16}/></Link></section>
  </main><Footer/></>}
