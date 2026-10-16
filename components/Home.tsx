import Link from 'next/link';
import Image from 'next/image';
import { ArrowRight, BadgeCheck, BellRing, BriefcaseBusiness, CheckCircle2, FileImage, Link2, MessageSquare, Phone, Search, ShieldCheck, Store, Upload, WalletCards } from 'lucide-react';
import { Header, Footer } from './Header';
import { QuickCheck } from './QuickCheck';
import { GuardDemo } from './GuardDemo';

const checks = [
  ['Payment Requests & Transfers','Check a transfer request, recipient, amount, payment instruction, or reversal story before money moves.',WalletCards,'/detect/payment'],
  ['Payment Proof & Screenshots','Inspect receipts, alerts and screenshots before releasing goods or value.',FileImage,'/detect/screenshot'],
  ['Suspicious Messages','Check SMS, WhatsApp, social-media messages and other suspicious text.',MessageSquare,'/detect/message'],
  ['Links & Websites','Analyse a URL before opening it or trusting what it asks.',Link2,'/detect/link'],
  ['Phone Numbers','Check reputation signals and moderated community reports.',Phone,'/detect/number'],
  ['Suspicious Calls','Tell Guard what a caller claimed and requested.',BellRing,'/detect/call']
] as const;
const frauds = ['Mobile Money Fraud','Bank Impersonation','Phishing','Fake Online Shops','Investment Fraud','Job Scams','Account Takeover','Delivery Scams'];
const communitySignals = [
  ['Suspicious payment message', '“You have received a bonus. Pay a small fee to withdraw.”', 'Payment request', MessageSquare],
  ['Fake delivery link', '“Your parcel is waiting. Confirm your address now.”', 'Suspicious link', Link2],
  ['Impersonation call', '“Your account will be blocked unless you share the code.”', 'OTP request', Phone],
] as const;
const trustNumbers = [
  ['7', 'ways to check'],
  ['3', 'simple steps'],
  ['1', 'clear next action'],
  ['0', 'PINs or OTPs needed'],
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
    copy: 'Check a message, link, number, account, or payment request before you act.',
    points: [
      ['Check before you act','Messages, links, numbers, accounts, payment requests and screenshots.'],
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
    copy: 'Review suspicious evidence before releasing goods or value.',
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
    copy: 'Bring explainable risk signals into existing fraud-review workflows.',
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
  const {title,tier,image,alt,icon:Icon,copy,points,cta,href,theme} = audience;
  return <div className={'container guard-audience-layout guard-audience-'+theme+(index%2===1?' guard-audience-reverse':'')}><div className="guard-audience-photo"><Image src={image} alt={alt} width={index===1?1122:1536} height={index===1?1402:1024} sizes="(max-width: 760px) 100vw, 50vw" unoptimized/><div className="guard-audience-image-label"><Icon size={17}/><strong>{tier}</strong></div></div><div className="guard-audience-copy"><h2>{title}</h2><p>{copy}</p><div className="guard-audience-services">{points.map(([service])=><div key={service}><BadgeCheck size={17}/><strong>{service}</strong></div>)}</div><div className="guard-audience-action"><Link href={href} className="btn btn-primary">{cta}<ArrowRight size={15}/></Link></div></div></div>;
}

export function Home() { return <><Header overlay/><main className="home-page">
  <section className="hero"><div className="container hero-grid"><div className="hero-copy-layer"><h1><span>Spot the warning</span><span>signs before you act.</span></h1><p className="hero-copy">Understand the risk before you reply, click, share, or pay.</p><QuickCheck/><div className="hero-trust"><BadgeCheck size={16}/> No account needed.</div></div><div className="hero-art"><div className="proof-card"><strong><BadgeCheck size={15} style={{verticalAlign:'-3px',marginRight:6,color:'#00a8db'}}/>Understand the risk</strong><span>Pause. Check. Choose a safer next step.</span></div></div></div></section>
  <section className="trust-number-marquee" aria-label="Guard at a glance"><div className="trust-number-track">{[...trustNumbers,...trustNumbers].map(([number,label],index)=><div className="trust-number-item" key={label+'-'+index} aria-hidden={index>=trustNumbers.length}><strong>{number}</strong><span>{label}</span><i/></div>)}</div></section>
  <section className="simple-how-section"><div className="container"><div className="simple-how-heading"><h2>Check in three steps.</h2></div><div className="simple-how-grid"><article className="simple-how-card"><div className="simple-how-icon"><Search size={28}/><b>01</b></div><h3>Choose a type</h3><div className="simple-how-options"><span><WalletCards size={13}/> Payment</span><span><FileImage size={13}/> Screenshot</span><span><MessageSquare size={13}/> Message</span><span><Phone size={13}/> Number</span><span><Link2 size={13}/> Link</span></div></article><div className="simple-how-arrow"><ArrowRight size={20}/></div><article className="simple-how-card"><div className="simple-how-icon"><Upload size={28}/><b>02</b></div><h3>Add details</h3><div className="simple-how-input"><span>Paste or describe it…</span><strong>Check</strong></div></article><div className="simple-how-arrow"><ArrowRight size={20}/></div><article className="simple-how-card"><div className="simple-how-icon"><ShieldCheck size={28}/><b>03</b></div><h3>Review the guidance</h3><div className="simple-how-result"><span><i/>Caution</span><strong><CheckCircle2 size={14}/> Verify before you continue</strong></div></article></div></div></section>
  <section className="guard-audience-pair-section"><div className="container"><div className="guard-audience-pair-heading"><h2>Protection for people and businesses.</h2></div><div className="guard-audience-pair">{audiences.slice(0,2).map((audience,index)=><article className="guard-audience-section guard-audience-article" key={audience.title}><AudienceStory audience={audience} index={index}/></article>)}</div></div></section>
  <section className="guard-audience-section guard-audience-enterprise"><AudienceStory audience={audiences[2]} index={2}/></section>
  <section className="section community-section"><div className="container"><div className="section-head community-head"><h2>What people noticed before fraud escalated.</h2></div><div className="community-grid">{communitySignals.map(([title,quote,tag,Icon])=><article className="community-card" key={title}><div className="community-card-top"><span className="icon-box"><Icon size={18}/></span><span className="ds-pill ds-pill-lilac">{tag}</span></div><h3>{title}</h3><p>{quote}</p><div className="community-card-foot"><span><span className="community-dot"/> Community signal</span><Link href="/detect" aria-label={'Check '+title}>Check <ArrowRight size={13}/></Link></div></article>)}</div><div className="common-scam-row"><strong>Common fraud patterns</strong><div className="common-scam-tags">{frauds.slice(0,6).map(x=><Link href="/learn" key={x}>{x}<ArrowRight size={12}/></Link>)}</div></div></div></section>
  <section className="section feature-section"><div className="container"><div className="section-head split-head"><h2>Check what reached you.</h2></div><div className="card-grid">{checks.map(([title,,Icon,href],i)=><Link href={href} className={'feature-card feature-'+i} key={title}><div className="icon-box"><Icon size={19}/></div><h3>{title}</h3><span className="card-arrow">Check <ArrowRight size={14}/></span></Link>)}</div></div></section>
  <GuardDemo/>
  <section className="section"><div className="container" style={{textAlign:'center'}}><h2>Not sure?<br/>Check it with Guard.</h2><Link href="/detect" className="btn btn-primary">Run a check <ArrowRight size={16}/></Link></div></section>
  </main><Footer/></> }
