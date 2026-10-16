import Link from 'next/link';
import Image from 'next/image';
import { ArrowRight, BadgeCheck, BriefcaseBusiness, CheckCircle2, Link2, MessageSquare, Phone, Plug, Puzzle, ShieldCheck, Smartphone, Store } from 'lucide-react';
import { Header, Footer } from './Header';
import { QuickCheck } from './QuickCheck';
import { GuardDemo } from './GuardDemo';

const frauds = ['Mobile Money Fraud','Bank Impersonation','Phishing','Fake Online Shops','Investment Fraud','Job Scams','Account Takeover','Delivery Scams'];
const guardProducts = [
  {
    number: '01',
    title: 'Browser extension',
    status: 'In development',
    channel: 'Web browsers',
    icon: Puzzle,
    copy: 'Check suspicious links and websites while you browse—before you sign in, share details, or pay.',
    features: ['Page-level risk warnings', 'One-click link checks', 'Report a suspicious website'],
  },
  {
    number: '02',
    title: 'Guard mobile app',
    status: 'Planned',
    channel: 'Android and iOS',
    icon: Smartphone,
    copy: 'Send messages, numbers, screenshots, and payment requests to Guard directly from your phone.',
    features: ['Share directly to Guard', 'Check calls and messages', 'Keep a history of results'],
  },
  {
    number: '03',
    title: 'Guard plugin',
    status: 'Partner pilot',
    channel: 'Products and workflows',
    icon: Plug,
    copy: 'Bring Guard intelligence into banking, fintech, marketplace, and customer-support experiences.',
    features: ['Embedded fraud checks', 'Explainable risk signals', 'Team review workflows'],
  },
] as const;
const communitySignals = [
  ['Suspicious payment message', '“You have received a bonus. Pay a small fee to withdraw.”', 'Payment request', MessageSquare],
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
  <section className="hero"><div className="hero-slides" aria-hidden="true"><span className="hero-slide hero-slide-personal"/></div><div className="container hero-grid"><div className="hero-copy-layer"><h1><span>Spot the <em>warning</em></span><span><em>signs</em> before you act.</span></h1><p className="hero-copy"><span>Check suspicious messages, links, calls, screenshots, and payments.</span><span>Understand the risk before you reply, click, share, or pay.</span></p><div className="hero-check-block"><QuickCheck/><div className="hero-trust"><BadgeCheck size={16}/> No account needed.</div></div></div><div className="hero-art"><div className="proof-card"><strong><BadgeCheck size={15} style={{verticalAlign:'-3px',marginRight:6,color:'#00a8db'}}/>Understand the risk</strong><span>Pause. Check. Choose a safer next step.</span></div></div></div></section>
  <section className="trust-proof-section"><div className="container trust-proof-grid"><div className="trust-proof-copy"><span className="trust-proof-eyebrow">Why trust Guard</span><h2>A result you can understand.</h2><p>Guard combines detection rules with reviewed fraud reports, then explains the warning signs in plain language.</p><div className="trust-proof-points"><div><ShieldCheck size={20}/><span><strong>Privacy first</strong><small>Never submit a PIN, OTP, password, recovery code, or full card details.</small></span></div><div><BadgeCheck size={20}/><span><strong>Guidance, not certainty</strong><small>Every result includes reasons and a practical next step.</small></span></div></div><div className="trust-proof-actions"><Link href="/reports" className="btn btn-primary">Report suspicious activity <ArrowRight size={15}/></Link><Link href="/detect" className="trust-proof-link">Run a check</Link></div></div><aside className="trust-result-card" aria-label="Example Guard result"><div className="trust-result-top"><span>Example result</span><strong><i/> Caution</strong></div><h3>Verify before you continue.</h3><p>This request shows several patterns commonly used in impersonation fraud.</p><ul><li><CheckCircle2 size={16}/> Urgent request to act immediately</li><li><CheckCircle2 size={16}/> Claims to represent a trusted organisation</li><li><CheckCircle2 size={16}/> Asks you to send money or share access</li></ul><div className="trust-result-next"><span>Recommended action</span><strong>Contact the organisation through its official channel.</strong></div></aside></div></section>
  <section className="product-ecosystem-section"><div className="container"><div className="product-ecosystem-heading"><span>Guard products</span><h2>Protection wherever risk appears.</h2><p>The same fraud intelligence, delivered where people and organisations make decisions.</p></div><div className="product-ecosystem-grid">{guardProducts.map(({number,title,status,channel,icon:Icon,copy,features})=><article className="product-ecosystem-card" key={title}><div className="product-card-top"><span className="product-card-icon"><Icon size={25}/><b>{number}</b></span><span className="product-status">{status}</span></div><h3>{title}</h3><p>{copy}</p><ul>{features.map(feature=><li key={feature}><CheckCircle2 size={15}/>{feature}</li>)}</ul><div className="product-channel"><span>Works in</span><strong>{channel}</strong></div></article>)}</div></div></section>
  <section className="guard-audience-pair-section"><div className="container"><div className="guard-audience-pair-heading"><h2>Protection for people and businesses.</h2></div><div className="guard-audience-pair">{audiences.slice(0,2).map((audience,index)=><article className="guard-audience-section guard-audience-article" key={audience.title}><AudienceStory audience={audience} index={index}/></article>)}</div></div></section>
  <section className="guard-audience-section guard-audience-enterprise"><AudienceStory audience={audiences[2]} index={2}/></section>
  <section className="section community-section"><div className="container"><div className="section-head community-head"><h2>What people noticed before fraud escalated.</h2></div><div className="community-grid">{communitySignals.map(([title,quote,tag,Icon])=><article className="community-card" key={title}><div className="community-card-top"><span className="icon-box"><Icon size={18}/></span><span className="ds-pill ds-pill-lilac">{tag}</span></div><h3>{title}</h3><p>{quote}</p><div className="community-card-foot"><span><span className="community-dot"/> Community signal</span><Link href="/detect" aria-label={'Check '+title}>Check <ArrowRight size={13}/></Link></div></article>)}</div><div className="common-scam-row"><strong>Common fraud patterns</strong><div className="common-scam-tags">{frauds.slice(0,6).map(x=><Link href="/learn" key={x}>{x}<ArrowRight size={12}/></Link>)}</div></div></div></section>
  <GuardDemo/>
  <section className="section"><div className="container" style={{textAlign:'center'}}><h2>Not sure?<br/>Check it with Guard.</h2><Link href="/detect" className="btn btn-primary">Run a check <ArrowRight size={16}/></Link></div></section>
  </main><Footer/></> }
