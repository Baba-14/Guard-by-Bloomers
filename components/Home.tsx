import Link from 'next/link';
import Image from 'next/image';
import { ArrowRight, BadgeCheck, BellRing, BriefcaseBusiness, CheckCircle2, FileImage, Link2, MessageSquare, Phone, Search, ShieldCheck, Store, Upload, WalletCards } from 'lucide-react';
import { Header, Footer } from './Header';
import { QuickCheck } from './QuickCheck';
import { GuardDemo } from './GuardDemo';

const checks = [
  ['Mobile Money & Payment Requests','Check a transfer request, recipient, amount, payment instruction, or reversal story before money moves.',WalletCards,'/detect/payment'],
  ['Payment Proof & Screenshots','Inspect receipts, alerts and screenshots before releasing goods or value.',FileImage,'/detect/screenshot'],
  ['Suspicious Messages','Check SMS, WhatsApp, social-media messages and other suspicious text.',MessageSquare,'/detect/message'],
  ['Links & Websites','Analyse a URL before opening it or trusting what it asks.',Link2,'/detect/link'],
  ['Phone Numbers','Check reputation signals and moderated community reports.',Phone,'/detect/number'],
  ['Suspicious Calls','Tell Guard what a caller claimed and requested.',BellRing,'/detect/call']
] as const;
const frauds = ['Mobile Money Fraud','Bank Impersonation','Phishing','Fake Online Shops','Investment Fraud','Job Scams','Account Takeover','Delivery Scams'];
const communitySignals = [
  ['Mobile money message', '“You have received a bonus. Pay a small fee to withdraw.”', 'Payment request', MessageSquare],
  ['Fake delivery link', '“Your parcel is waiting. Confirm your address now.”', 'Suspicious link', Link2],
  ['Impersonation call', '“Your account will be blocked unless you share the code.”', 'OTP request', Phone],
] as const;
const audiences = [
  {
    number: '01',
    eyebrow: 'Individual protection',
    title: 'Everyday people and families',
    heading: 'A safer second opinion before you act.',
    tier: 'Free access',
    image: '/images/audiences/everyday-user-v2.jpg',
    alt: 'Young Ghanaian woman pausing to inspect a suspicious message on her smartphone',
    icon: Phone,
    copy: 'Guard gives people a simple place to check a Mobile Money request, payment instruction, message, call, link, or account before sending money. Basic protection remains accessible because avoiding financial loss should not depend on income.',
    points: [
      ['Check before money moves','Mobile Money requests, recipient details, messages, links, numbers and screenshots.'],
      ['Understand the warning','Plain-language reasons instead of technical security language.'],
      ['Choose a safer action','Practical guidance for verifying through a trusted channel.'],
    ],
    cta: 'Run a free check',
    href: '/detect',
    note: 'Designed for broad access and community protection.',
    theme: 'people',
  },
  {
    number: '02',
    eyebrow: 'Commercial protection',
    title: 'Merchants, informal businesses and SMEs',
    heading: 'Protect the sale before the goods leave.',
    tier: 'Business',
    image: '/images/audiences/sme-owner.jpg',
    alt: 'Ghanaian online shop owner reviewing payment proof before dispatching an order',
    icon: Store,
    copy: 'For online sellers, market traders, Mobile Money agents and growing businesses, one convincing screenshot can become a direct loss. Guard helps teams inspect the evidence before fulfilling an order or releasing value.',
    points: [
      ['Inspect payment proof','Flag visible manipulation and inconsistencies in screenshots.'],
      ['Analyse buyer behaviour','Review suspicious wording, urgency and identity changes.'],
      ['Build a fraud history','Keep checks and recurring signals visible to the business.'],
    ],
    cta: 'Explore Guard for business',
    href: '/business',
    note: 'The clearest direct subscription opportunity.',
    theme: 'business',
  },
  {
    number: '03',
    eyebrow: 'Protection at scale',
    title: 'Banks, fintechs, telcos and marketplaces',
    heading: 'Turn scattered fraud signals into shared intelligence.',
    tier: 'Enterprise',
    image: '/images/audiences/enterprise-team.jpg',
    alt: 'Ghanaian financial-services fraud operations team reviewing digital risk signals',
    icon: BriefcaseBusiness,
    copy: 'Guard can help organisations protect customers and operations with explainable risk signals, shared reporting intelligence and tools that fit into existing fraud-review workflows.',
    points: [
      ['Fraud intelligence API','Bring Guard signals into products and internal workflows.'],
      ['Operations dashboard','Review reports, patterns and high-risk activity in one place.'],
      ['Customer education','Deliver timely, locally relevant fraud guidance at scale.'],
    ],
    cta: 'Talk to Guard',
    href: '/business',
    note: 'Built for partnerships and enterprise contracts.',
    theme: 'enterprise',
  },
] as const;

function AudienceStory({ audience, index }: { audience: (typeof audiences)[number], index: number }) {
  const {number,eyebrow,title,heading,tier,image,alt,icon:Icon,copy,points,cta,href,note,theme} = audience;
  return <div className={'container guard-audience-layout guard-audience-'+theme+(index%2===1?' guard-audience-reverse':'')}><div className="guard-audience-photo"><Image src={image} alt={alt} width={index===1?1122:1536} height={index===1?1402:1024} sizes="(max-width: 760px) 100vw, 50vw"/><div className="guard-audience-image-label"><Icon size={17}/><span><small>{number} / Who Guard protects</small><strong>{tier}</strong></span></div></div><div className="guard-audience-copy"><div className="guard-audience-kicker"><span className="eyebrow">{eyebrow}</span><b>{tier}</b></div><h3>{title}</h3><h2>{heading}</h2><p>{copy}</p><div className="guard-audience-services">{points.map(([service,description])=><div key={service}><BadgeCheck size={17}/><span><strong>{service}</strong><small>{description}</small></span></div>)}</div><div className="guard-audience-action"><Link href={href} className="btn btn-primary">{cta}<ArrowRight size={15}/></Link><small>{note}</small></div></div></div>;
}

export function Home() { return <><Header overlay/><main className="home-page">
  <section className="hero"><div className="container hero-grid"><div className="hero-copy-layer"><div className="eyebrow">Mobile Money fraud prevention</div><h1>Keep your money<br/>safe from fraud.</h1><p className="hero-copy">Check a Mobile Money request, payment screenshot, recipient, message, number or link before you send money or release goods.</p><QuickCheck/><div className="hero-trust"><BadgeCheck size={16}/> Check before you pay. No account needed.</div></div><div className="hero-art"><div className="proof-card"><strong><BadgeCheck size={15} style={{verticalAlign:'-3px',marginRight:6,color:'#6d22b7'}}/>Protect the transaction</strong><span>Pause. Check. Keep your money safe.</span></div></div></div><div className="hero-partner-row"><div className="container"><span>Growing the safety ecosystem</span><div aria-label="Potential partner categories"><b>Mobile Money</b><b>Merchants</b><b>Banking partners</b><b>CSA Ghana</b><b>Community networks</b></div></div></div></section>
  <section className="simple-how-section"><div className="container"><div className="simple-how-heading"><span className="eyebrow">How Guard protects your money</span><h2>Check before you pay<br/>in three simple steps.</h2><p>Start with the payment request or the evidence that came with it. Guard helps you understand the warning signs before money or goods leave your hands.</p></div><div className="simple-how-grid"><article className="simple-how-card"><div className="simple-how-icon"><Search size={28}/><b>01</b></div><h3>Choose what reached you</h3><p>Start with the Mobile Money request, payment proof, message, caller, number, or link.</p><div className="simple-how-options"><span><WalletCards size={13}/> MoMo request</span><span><FileImage size={13}/> Payment proof</span><span><MessageSquare size={13}/> Message</span><span><Phone size={13}/> Number</span><span><Link2 size={13}/> Link</span></div></article><div className="simple-how-arrow"><ArrowRight size={20}/></div><article className="simple-how-card"><div className="simple-how-icon"><Upload size={28}/><b>02</b></div><h3>Add the payment details</h3><p>Describe the request or paste and upload the evidence you received. Remove PINs, passwords and OTPs.</p><div className="simple-how-input"><span>Amount, recipient, message or screenshot…</span><strong>Check</strong></div></article><div className="simple-how-arrow"><ArrowRight size={20}/></div><article className="simple-how-card"><div className="simple-how-icon"><ShieldCheck size={28}/><b>03</b></div><h3>Decide before money moves</h3><p>Guard explains the risk, what raised concern, and whether to pause, verify independently, or avoid paying.</p><div className="simple-how-result"><span><i/>Caution</span><strong><CheckCircle2 size={14}/> Do not pay until verified</strong></div></article></div><div className="simple-how-action"><div><strong>One pause can prevent a loss.</strong><span>Check the request before you send money or release goods.</span></div><Link href="/detect" className="btn btn-primary">Check before you pay <ArrowRight size={15}/></Link></div></div></section>
  <section className="guard-audience-pair-section"><div className="container"><div className="guard-audience-pair-heading"><span className="eyebrow">Who Guard is for</span><h2>Protection for people.<br/>Tools for the businesses they trust.</h2><p>One connected safety layer for everyday decisions and the merchants who serve them.</p></div><div className="guard-audience-pair">{audiences.slice(0,2).map((audience,index)=><article className="guard-audience-section guard-audience-article" key={audience.title}><AudienceStory audience={audience} index={index}/></article>)}</div></div></section>
  <section className="guard-audience-section guard-audience-enterprise"><AudienceStory audience={audiences[2]} index={2}/></section>
  <section className="section community-section"><div className="container"><div className="section-head community-head"><div><div className="eyebrow">Community payment warnings</div><h2>What people saw before money moved.</h2></div><p>Shared experiences make payment fraud easier to recognise. These are the messages, links, calls and impersonation tactics people encountered before being asked to pay.</p></div><div className="community-grid">{communitySignals.map(([title,quote,tag,Icon])=><article className="community-card" key={title}><div className="community-card-top"><span className="icon-box"><Icon size={18}/></span><span className="ds-pill ds-pill-lilac">{tag}</span></div><h3>{title}</h3><p>{quote}</p><div className="community-card-foot"><span><span className="community-dot"/> Seen before a payment request</span><Link href="/detect" aria-label={'Check '+title}>Check before paying <ArrowRight size={13}/></Link></div></article>)}</div><div className="common-scam-row"><div><div className="eyebrow">Browse common money scams</div><strong>Recognise the pattern before it becomes a loss.</strong></div><div className="common-scam-tags">{frauds.slice(0,6).map(x=><Link href="/learn" key={x}>{x}<ArrowRight size={12}/></Link>)}</div></div></div></section>
  <section className="section feature-section"><div className="container"><div className="section-head split-head"><div><div className="eyebrow">Stop the loss before it happens</div><h2>Every signal leads back to protecting your money</h2></div><p>Fraud may arrive through WhatsApp, SMS, a call, screenshot or link. Guard examines those signals to help you avoid a bad payment or unsafe transaction.</p></div><div className="card-grid">{checks.map(([title,desc,Icon,href],i)=><Link href={href} className={'feature-card feature-'+i} key={title}><div className="icon-box"><Icon size={19}/></div><h3>{title}</h3><p>{desc}</p><span className="card-arrow">Explore check <ArrowRight size={14}/></span></Link>)}</div></div></section>
  <GuardDemo/>
  <section className="section"><div className="container" style={{textAlign:'center'}}><div className="eyebrow">Before money moves</div><h2>Not sure about the request?<br/>Check before you pay.</h2><Link href="/detect" className="btn btn-primary">Protect my money <ArrowRight size={16}/></Link></div></section>
  </main><Footer/></> }
