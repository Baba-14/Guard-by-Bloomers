'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, Check, ChevronDown, ShieldCheck, Sparkles } from 'lucide-react';
import { Header, Footer } from '@/components/Header';

const products = ['Payment & MoMo checks', 'Community intelligence', 'Case management', 'API & integrations'] as const;
const extras = ['Shared team workspace', 'Custom detection rules', 'API access'] as const;

const plans = [
  { name: 'Pilot', price: 'Free', suffix: 'to get started', copy: 'For small teams testing payment verification before goods or value are released.', commitment: 'No monthly commitment', features: ['100 payment and fraud checks each month', '3 team members', 'Payment-proof explanations', 'Community reputation signals'], action: 'Start a free pilot', href: '/register' },
  { name: 'Protect', price: 'GHS 1,500', suffix: 'per month', copy: 'For merchants and support teams preventing payment fraud and avoidable transaction losses every day.', commitment: 'Includes 2,500 checks monthly', features: ['Everything in Pilot', '15 team members', 'Payment review queues and history', 'Shared notes and evidence', 'Priority fraud intelligence'], action: 'Choose Protect', href: '/register' },
  { name: 'Scale', price: 'Let’s talk', suffix: 'built around your operation', copy: 'For organisations that need configurable fraud operations and integrations.', commitment: 'Custom volume and support', features: ['Everything in Protect', 'Custom team access', 'Configurable detection rules', 'API and data integrations', 'Dedicated intelligence support'], action: 'Talk to Guard', href: '/report' },
] as const;

const faqs = [
  ['Can we try Guard before paying?', 'Yes. The Pilot plan lets a small team run up to 100 checks each month without a monthly commitment.'],
  ['What counts as a fraud check?', 'A check is one submitted message, link, phone number, screenshot, call description, or payment request analysed by Guard.'],
  ['Can our team change plans later?', 'Yes. You can move from Pilot to Protect or speak with us about a Scale plan as your volume and workflow grow.'],
  ['Do you support custom fraud rules?', 'Custom rules are available for Scale customers and can reflect your organisation’s channels, policies, and recurring fraud patterns.'],
] as const;

export default function Business() {
  const [product, setProduct] = useState<(typeof products)[number]>('Payment & MoMo checks');
  const [volume, setVolume] = useState(500);
  const [selectedExtras, setSelectedExtras] = useState<string[]>([]);
  const recommended = volume <= 100 ? 0 : volume <= 2500 ? 1 : 2;
  const volumeLabel = volume >= 5000 ? '5,000+' : volume.toLocaleString();
  const recommendation = useMemo(() => plans[recommended], [recommended]);

  const toggleExtra = (extra: string) => setSelectedExtras(current => current.includes(extra) ? current.filter(item => item !== extra) : [...current, extra]);

  return <><Header/><main className="business-page">
    <section className="business-hero"><div className="container business-hero-inner"><div className="business-hero-copy"><span className="eyebrow">Payment protection for organisations</span><h1>Verify the payment before the goods leave.</h1><p>Guard helps merchants, Mobile Money agents, SMEs and larger teams inspect payment proof, recipient behaviour and fraud signals before a transaction becomes a loss.</p></div><div className="business-hero-mark" aria-hidden="true"><img src="/images/guard-yellow.png" alt=""/><span>Protect every transaction</span></div></div></section>

    <section className="container business-config-wrap"><div className="business-config"><div className="business-config-heading"><span><Sparkles size={17}/> Build your Guard plan</span><strong>{recommendation.name} is your best starting point</strong></div><div className="business-config-grid"><div className="business-question"><label>What are you interested in?</label><div className="business-choice-row">{products.map(item=><button type="button" key={item} className={product===item?'active':''} onClick={()=>setProduct(item)}>{item}</button>)}</div></div><div className="business-question"><div className="business-range-head"><label>How many checks do you expect each month?</label><output>{volumeLabel}</output></div><input className="business-range" type="range" min="100" max="5000" step="100" value={volume} onChange={event=>setVolume(Number(event.target.value))}/><div className="business-range-scale"><span>100</span><span>5,000+</span></div></div><div className="business-question"><label>Do you need extra capabilities?</label><div className="business-extra-row">{extras.map(extra=><button type="button" key={extra} className={selectedExtras.includes(extra)?'active':''} onClick={()=>toggleExtra(extra)}><span>{selectedExtras.includes(extra)&&<Check size={12}/>}</span>{extra}</button>)}</div></div></div><div className="business-config-result"><div><span>Suggested plan for {product.toLowerCase()}</span><strong>{recommendation.name}</strong><small>{selectedExtras.length ? `${selectedExtras.length} extra ${selectedExtras.length===1?'capability':'capabilities'} selected` : 'Core capabilities selected'}</small></div><a href={'#plan-'+recommendation.name.toLowerCase()} className="btn btn-primary">View recommendation <ArrowRight size={15}/></a></div></div></section>

    <section className="container business-plans" id="plans"><div className="business-section-head"><span className="eyebrow">Plans and pricing</span><h2>Start clearly. Scale confidently.</h2><p>Every plan gives your team explainable fraud signals and practical next steps.</p></div><div className="business-plan-grid">{plans.map((plan,index)=><article id={'plan-'+plan.name.toLowerCase()} className={'business-plan-card '+(recommended===index?'recommended':'')} key={plan.name}>{recommended===index&&<span className="business-plan-badge">Recommended for you</span>}<div className="business-plan-name">{plan.name}</div><div className="business-plan-price">{plan.price}</div><div className="business-plan-suffix">{plan.suffix}</div><p>{plan.copy}</p><Link href={plan.href} className={'btn '+(recommended===index?'btn-primary':'btn-outline')}>{plan.action}<ArrowRight size={15}/></Link><div className="business-plan-commitment">{plan.commitment}</div><ul>{plan.features.map(feature=><li key={feature}><span><Check size={13}/></span>{feature}</li>)}</ul></article>)}</div><p className="business-pricing-note">All prices exclude applicable taxes. Higher-volume and custom integration pricing is tailored to your operating needs.</p></section>

    <section className="business-proof"><div className="container business-proof-grid"><div><span className="eyebrow">Stop avoidable transaction losses</span><h2>One place to verify payment evidence before your team releases value.</h2></div><div className="business-proof-stats"><div><strong>MoMo</strong><span>payment-first checks</span></div><div><strong>24/7</strong><span>decision support</span></div><div><strong>1</strong><span>shared fraud picture</span></div></div></div></section>

    <section className="container business-faq"><div className="business-section-head"><span className="eyebrow">Questions</span><h2>Good to know before you start.</h2></div><div className="business-faq-list">{faqs.map(([question,answer])=><details key={question}><summary>{question}<ChevronDown size={18}/></summary><p>{answer}</p></details>)}</div><div className="business-final-cta"><div><ShieldCheck size={22}/><span><strong>Need a plan built around your operation?</strong><small>Tell us about your channels, volume, and fraud workflow.</small></span></div><Link href="/report" className="btn btn-primary">Talk to Guard <ArrowRight size={15}/></Link></div></section>
  </main><Footer/></>;
}
