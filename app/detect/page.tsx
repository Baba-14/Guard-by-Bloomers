import Link from 'next/link';
import { ArrowRight, BookOpen, Check, MessageCircle, Network, ScanSearch, ShieldCheck, TriangleAlert } from 'lucide-react';
import { Header, Footer } from '@/components/Header';
import { InlineFraudChecker } from '@/components/InlineFraudChecker';

const stages = [
  ['01','A payment is requested','Someone asks you to send Mobile Money, return a transfer, pay a fee, or release goods.'],
  ['02','Check the evidence','Add the request, recipient, screenshot, message, number, link, or call details.'],
  ['03','Guard checks the signals','Warning patterns, context, and moderated community reports are brought together.'],
  ['04','Decide before money moves','You get a plain-language risk explanation and a safer next action.'],
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
  <section className="fraud-hero"><div className="container fraud-hero-grid"><div className="fraud-hero-copy"><span className="eyebrow">Mobile Money fraud detection</span><h1>Check before your money moves.</h1><p>Guard examines suspicious Mobile Money requests, recipient details, payment screenshots, messages, numbers, links, and calls so you can pause before paying or releasing goods.</p><div className="fraud-hero-actions"><Link href="#checks" className="btn btn-primary">Check before I pay <ArrowRight size={16}/></Link><Link href="/report" className="btn btn-outline">Report a payment scam</Link></div><div className="fraud-hero-trust"><ShieldCheck size={16}/> Protect your money with explainable guidance. No account needed.</div></div><div className="fraud-console" aria-label="Example Guard risk assessment"><div className="fraud-console-top"><span><img src="/images/guard-yellow.png" alt=""/>Guard payment review</span><b>Before you pay</b></div><div className="fraud-console-score"><span className="fraud-console-ring"><strong>72</strong><small>risk score</small></span><div><span>Payment assessment</span><strong>Caution</strong><small>Do not send money until you verify independently.</small></div></div><div className="fraud-console-signals"><div><span><TriangleAlert size={15}/> Request pattern</span><b>Urgent payment</b></div><div><span><Network size={15}/> Recipient signal</span><b>Name changed</b></div><div><span><MessageCircle size={15}/> Community signal</span><b>Related reports</b></div></div><div className="fraud-console-action"><Check size={15}/> Pause the payment and verify the recipient</div></div></div></section>

  <section className="fraud-proof"><div className="container fraud-proof-grid"><div><strong>MoMo</strong><span>payment-first protection</span></div><div><strong>7</strong><span>ways to add evidence</span></div><div><strong>1</strong><span>clear next action</span></div><div><strong>0</strong><span>PINs or OTPs required</span></div></div></section>

  <InlineFraudChecker/>

  <section className="fraud-journey"><div className="container"><div className="fraud-section-head fraud-section-head-light"><div><span className="eyebrow">Protect the transaction</span><h2>Pause before the payment becomes a loss.</h2></div><p>Fraud succeeds when pressure moves faster than verification. Guard creates a clear checkpoint before money or goods leave your hands.</p></div><div className="fraud-stage-grid">{stages.map(([number,title,copy])=><article key={number}><span>{number}</span><h3>{title}</h3><p>{copy}</p></article>)}</div></div></section>

  <section className="container fraud-threats"><div className="fraud-threat-copy"><span className="eyebrow">Payment fraud coverage</span><h2>Recognise what is trying to move your money.</h2><p>Guard connects the payment request with the message, recipient, screenshot, number, link, call, and moderated community reports to explain why a transaction deserves a closer look.</p><ul><li><Check size={14}/> Mobile Money reversal and advance-fee requests</li><li><Check size={14}/> Fake payment alerts and manipulated proof</li><li><Check size={14}/> WhatsApp takeover asking contacts for money</li><li><Check size={14}/> Phishing and urgent calls targeting wallets, PINs, or OTPs</li></ul><Link href="/learn" className="btn btn-outline">Explore money fraud patterns <ArrowRight size={15}/></Link></div><div className="fraud-threat-panel"><div className="fraud-threat-panel-head"><ScanSearch size={20}/><span><strong>Guard connects the payment signals</strong><small>Evidence becomes a clearer decision</small></span></div><div className="fraud-threat-path"><span>Payment request</span><i/><span>Fraud pattern</span><i/><span>Community context</span></div><div className="fraud-threat-result"><ShieldCheck size={23}/><div><span>Before you pay</span><strong>What raised concern, why it matters, and the safest next action.</strong></div></div></div></section>

  <section className="community-patterns fraud-pattern-library"><div className="container"><div className="community-patterns-head"><div><span className="eyebrow">Fraud pattern library</span><h2>Learn the pattern behind the story.</h2></div><p>Understand how common fraud works, what warning signs to notice, and what to do before you respond.</p></div><div className="community-pattern-grid">{patterns.map(([title,description,slug],index)=><Link href={'/learn/'+slug} className="community-pattern-card" key={title}><span>{String(index+1).padStart(2,'0')}</span><BookOpen size={20}/><h3>{title}</h3><p>{description}</p><b>Read the guide <ArrowRight size={13}/></b></Link>)}</div><div className="community-patterns-cta"><div><strong>Looking for another fraud type?</strong><span>Browse the full awareness library for more practical guides.</span></div><Link href="/learn" className="btn btn-primary">Explore all fraud patterns <ArrowRight size={15}/></Link></div></div></section>

  <section className="container fraud-report"><div><span className="eyebrow">Help protect someone else</span><h2>Already encountered fraud?</h2><p>Report the WhatsApp account, number, link, payment route, message, or call. Remove passwords, PINs, and OTPs before sharing.</p></div><Link href="/report" className="btn btn-primary">Report fraud <ArrowRight size={16}/></Link></section>
  </main><Footer/></>}
