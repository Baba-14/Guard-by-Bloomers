import Link from 'next/link';
import { Header, Footer } from '@/components/Header';
import {
  AlertTriangle, ArrowDown, ArrowRight, Banknote, BookOpen, Brain, CheckCircle2,
  ExternalLink, Eye, Fingerprint, Globe2, Landmark, LockKeyhole, MessageSquareWarning,
  MousePointerClick, Phone, Radar, Search, ShieldCheck, Smartphone, Target, Timer,
  TriangleAlert, UserRoundCheck, WalletCards, Waypoints,
} from 'lucide-react';
import './learn.css';

const bogReport = 'https://www.bog.gov.gh/wp-content/uploads/2025/04/NOTICE-NO.-BG-GOV-SEC-2025-09-Publication-of-Banks-SDIS-and-PSPS-2024-Fraud-Report-1.pdf';
const csaReport = 'https://www.csa.gov.gh/resources/Annual%20Report%202024.pdf';

const statistics = [
  { value: '16,733', label: 'fraud cases recorded', detail: 'Across banks, specialised deposit-taking institutions and payment service providers in 2024.', change: '+5% year on year', source: 'Bank of Ghana 2024 Fraud Report', href: bogReport },
  { value: 'GH¢99m', label: 'total value at risk', detail: 'Up from approximately GH¢88 million across the same regulated sectors in 2023.', change: '+13% year on year', source: 'Bank of Ghana 2024 Fraud Report', href: bogReport },
  { value: '15,673', label: 'payment-provider cases', detail: 'Payment service providers accounted for about 94% of reported cases across the three sectors.', change: 'GH¢19m at risk', source: 'Bank of Ghana 2024 Fraud Report', href: bogReport },
  { value: 'GH¢23.1m', label: 'reported cybercrime losses', detail: 'Losses reported through the CSA contact points in 2024; this is a separate reporting scope.', change: '2,751 actual incidents', source: 'CSA Annual Report 2024', href: csaReport },
] as const;

const execution = [
  { step: '01', title: 'Select a target', text: 'The fraudster finds a person, business, phone number or public profile that fits the story they want to tell.', Icon: Target },
  { step: '02', title: 'Build borrowed trust', text: 'They impersonate a bank, network, employer, relative, courier, merchant or public institution.', Icon: UserRoundCheck },
  { step: '03', title: 'Create a trigger', text: 'Urgency, fear, scarcity, authority or an unexpected reward is used to reduce careful thinking.', Icon: Timer },
  { step: '04', title: 'Move value or access', text: 'The request shifts to money, an OTP, account access, a malicious link or sensitive identity information.', Icon: WalletCards },
  { step: '05', title: 'Break the trail', text: 'Funds are dispersed, accounts are abandoned and the victim is blocked or asked to pay again.', Icon: Waypoints },
] as const;

const patterns = [
  { title: 'Mobile money reversal', label: 'Payment manipulation', description: 'A caller claims money was sent by mistake, then pressures you to “reverse” it by initiating a new transfer.', signals: ['Unexpected credit story', 'Urgent callback', 'New transfer request'], slug: 'mobile-money-fraud', Icon: Smartphone, tone: 'orange' },
  { title: 'Bank impersonation', label: 'Authority abuse', description: 'A fraudster claims your account is blocked or compromised and asks for an OTP, PIN or remote access.', signals: ['Fear of account loss', 'Credential request', 'Unverified number'], slug: 'bank-impersonation', Icon: Landmark, tone: 'violet' },
  { title: 'Fake online merchant', label: 'Commerce fraud', description: 'A convincing social profile advertises scarce or discounted goods, collects payment and never delivers.', signals: ['Price below market', 'Payment before inspection', 'Recently created page'], slug: 'fake-online-shops', Icon: MousePointerClick, tone: 'gold' },
  { title: 'Investment platform', label: 'Confidence fraud', description: 'Fake returns and small early withdrawals create trust before larger deposits become impossible to recover.', signals: ['Guaranteed return', 'Fake testimonials', 'Withdrawal fee'], slug: 'investment-fraud', Icon: Banknote, tone: 'green' },
  { title: 'Recruitment and task scam', label: 'Advance-fee fraud', description: 'A job, scholarship or online task requires registration, training, equipment or “unlock” payments.', signals: ['No formal interview', 'Fee before employment', 'Messaging-only contact'], slug: 'recruitment-scams', Icon: Fingerprint, tone: 'blue' },
  { title: 'Delivery and customs fee', label: 'Phishing + payment', description: 'A fake courier notice claims a parcel is delayed and requires a small clearance fee through a copied site.', signals: ['Unexpected parcel', 'Shortened link', 'Immediate deadline'], slug: 'delivery-scams', Icon: Globe2, tone: 'red' },
] as const;

const signalGroups = [
  { number: '01', title: 'The story', text: 'Does the explanation make sense without the urgency?', items: ['Unexpected problem or reward', 'Claims that cannot be independently checked', 'Details that change when questioned'], Icon: MessageSquareWarning },
  { number: '02', title: 'The pressure', text: 'Fraud depends on shrinking your decision time.', items: ['Act now or lose access', 'Keep this conversation secret', 'Limited stock, role or investment window'], Icon: Timer },
  { number: '03', title: 'The request', text: 'The requested action often reveals the real objective.', items: ['Send money to an unfamiliar recipient', 'Share an OTP, PIN or password', 'Install software or open a link'], Icon: MousePointerClick },
  { number: '04', title: 'The mismatch', text: 'Compare the claim with the channel, identity and destination.', items: ['Personal wallet for a business payment', 'Domain or number differs from the official one', 'Account name does not match the story'], Icon: Search },
] as const;

const guides = [
  ['Mobile Money Fraud', 'How reversal stories, wallet takeovers and cash-out requests work.', 'mobile-money-fraud', Smartphone],
  ['Phishing', 'How copied pages and messages capture credentials and payment details.', 'phishing', MousePointerClick],
  ['OTP Theft', 'Why one code can hand control of an account to someone else.', 'otp-theft', LockKeyhole],
  ['Fake Online Shops', 'How to verify a seller, payment recipient and delivery promise.', 'fake-online-shops', Globe2],
  ['Investment Fraud', 'How fake dashboards and early returns create false confidence.', 'investment-fraud', Banknote],
  ['Recruitment Scams', 'How fake jobs turn applications into fees or identity theft.', 'recruitment-scams', Fingerprint],
] as const;

export default function Learn() {
  return <><Header />
    <main className="learn-page">
      <section className="learn-hero">
        <div className="container learn-hero-grid">
          <div className="learn-hero-copy">
            <span className="learn-kicker"><Radar size={14} /> Ghana fraud intelligence</span>
            <h1>Fraud is not one act.<br /><em>It is a system.</em></h1>
            <p>Learn how a believable story becomes pressure, how pressure becomes a payment, and where you can interrupt the pattern before money or access leaves your control.</p>
            <div className="learn-hero-actions"><a href="#patterns" className="btn btn-primary">Explore fraud patterns <ArrowDown size={15} /></a><Link href="/detect" className="btn btn-outline">Check something suspicious</Link></div>
            <div className="learn-source-note"><ShieldCheck size={15} /><span>Ghana-focused evidence, practical explanations, and direct links to primary sources.</span></div>
          </div>
          <div className="learn-hero-visual" aria-label="Fraud execution cycle">
            <div className="learn-radar-ring ring-one" /><div className="learn-radar-ring ring-two" /><div className="learn-radar-ring ring-three" />
            <div className="learn-radar-core"><TriangleAlert size={32} /><strong>Recognise</strong><span>the pattern</span></div>
            <div className="learn-radar-node node-story"><MessageSquareWarning size={17} /><span>Story</span></div>
            <div className="learn-radar-node node-pressure"><Timer size={17} /><span>Pressure</span></div>
            <div className="learn-radar-node node-payment"><WalletCards size={17} /><span>Payment</span></div>
            <div className="learn-radar-node node-exit"><Waypoints size={17} /><span>Exit</span></div>
          </div>
        </div>
      </section>

      <nav className="learn-subnav" aria-label="Fraud intelligence sections"><div className="container"><a href="#ghana">Ghana snapshot</a><a href="#anatomy">How fraud works</a><a href="#triangle">Fraud triangle</a><a href="#patterns">Pattern library</a><a href="#signals">Warning signals</a><a href="#respond">What to do</a></div></nav>

      <section className="learn-section learn-ghana" id="ghana"><div className="container">
        <div className="learn-section-head"><div><span className="learn-kicker">The Ghanaian picture</span><h2>The risk is measurable.<br />The human cost is larger.</h2></div><p>These figures come from different official reporting systems and should not be added together. They describe reported activity, not the full amount of fraud occurring in Ghana.</p></div>
        <div className="learn-stat-grid">{statistics.map((stat, index) => <article key={stat.label} className={index === 0 ? 'featured' : ''}><span className="learn-stat-index">0{index + 1}</span><strong>{stat.value}</strong><h3>{stat.label}</h3><p>{stat.detail}</p><div><b>{stat.change}</b><a href={stat.href} target="_blank" rel="noreferrer">{stat.source}<ExternalLink size={11} /></a></div></article>)}</div>
        <div className="learn-evidence-callout"><AlertTriangle size={22} /><div><strong>What changed in 2024?</strong><p>The Bank of Ghana reported notable increases in document forgery and identity theft or impersonation. Payment service providers continued to carry the largest case volume, reflecting the scale—and the exposure—of digital payments.</p></div><a href={bogReport} target="_blank" rel="noreferrer">Read the official report <ArrowRight size={14} /></a></div>
      </div></section>

      <section className="learn-section learn-anatomy" id="anatomy"><div className="container">
        <div className="learn-section-head light"><div><span className="learn-kicker">Anatomy of an attack</span><h2>A scam usually moves through a sequence.</h2></div><p>The channel may change—from a phone call to WhatsApp to a payment page—but the underlying journey is surprisingly consistent.</p></div>
        <div className="learn-execution">{execution.map(({ step, title, text, Icon }, index) => <article key={step}><div className="learn-execution-icon"><Icon size={20} /></div><span>{step}</span><h3>{title}</h3><p>{text}</p>{index < execution.length - 1 && <ArrowRight className="learn-flow-arrow" size={17} />}</article>)}</div>
        <div className="learn-break-point"><span>Break the sequence</span><strong>Verification is most powerful before step 04.</strong><p>Stop the conversation, find the official contact yourself, and verify the story through a separate channel.</p><Link href="/detect">Run a Guard check <ArrowRight size={14} /></Link></div>
      </div></section>

      <section className="learn-section learn-triangle-section" id="triangle"><div className="container learn-triangle-layout">
        <div className="learn-triangle-copy"><span className="learn-kicker">The fraud triangle</span><h2>Why fraud can happen inside trusted systems.</h2><p>The classic fraud triangle is most useful for understanding occupational or insider fraud. It describes three conditions that can make misconduct more likely—not proof that a person will commit fraud.</p><div className="learn-triangle-notes"><div><span>01</span><p><strong>Pressure</strong>Financial, personal or performance pressure creates a perceived need.</p></div><div><span>02</span><p><strong>Opportunity</strong>Weak controls, excessive access or limited oversight creates a path.</p></div><div><span>03</span><p><strong>Rationalisation</strong>The person finds a story that makes the action feel acceptable to them.</p></div></div></div>
        <div className="fraud-triangle" aria-label="Fraud triangle showing pressure, opportunity, and rationalisation"><svg viewBox="0 0 500 440"><defs><linearGradient id="triangleFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#9828e5" stopOpacity=".38"/><stop offset="1" stopColor="#ff7a18" stopOpacity=".12"/></linearGradient></defs><path d="M250 40 L455 385 L45 385 Z"/><path className="inner" d="M250 126 L376 340 L124 340 Z"/></svg><div className="triangle-centre"><Brain size={25}/><strong>Fraud risk</strong><span>Conditions overlap</span></div><div className="triangle-label pressure"><b>Pressure</b><span>The perceived need</span></div><div className="triangle-label opportunity"><b>Opportunity</b><span>The available path</span></div><div className="triangle-label rationale"><b>Rationalisation</b><span>The internal excuse</span></div></div>
      </div></section>

      <section className="learn-section learn-patterns" id="patterns"><div className="container"><div className="learn-section-head"><div><span className="learn-kicker">Pattern library</span><h2>Different stories.<br />Recognisable mechanics.</h2></div><p>A fraud pattern is not a verdict. It is a repeatable combination of story, pressure, requested action and destination that deserves closer verification.</p></div><div className="learn-pattern-grid">{patterns.map(({ title, label, description, signals, slug, Icon, tone }, index) => <article className={`learn-pattern-card tone-${tone}`} key={title}><header><div><Icon size={21} /></div><span>{String(index + 1).padStart(2, '0')}</span></header><small>{label}</small><h3>{title}</h3><p>{description}</p><ul>{signals.map(signal => <li key={signal}><CheckCircle2 size={12} />{signal}</li>)}</ul><Link href={`/learn/${slug}`}>Understand this pattern <ArrowRight size={14} /></Link></article>)}</div></div></section>

      <section className="learn-section learn-signals" id="signals"><div className="container"><div className="learn-section-head light"><div><span className="learn-kicker">Signal framework</span><h2>Do not judge one detail.<br />Read the stack.</h2></div><p>A single unusual detail can be innocent. Several connected mismatches create context worth investigating.</p></div><div className="learn-signal-grid">{signalGroups.map(({ number, title, text, items, Icon }) => <article key={number}><header><span>{number}</span><Icon size={20} /></header><h3>{title}</h3><p>{text}</p><ul>{items.map(item => <li key={item}>{item}</li>)}</ul></article>)}</div><div className="learn-signal-formula"><span>Believable story</span><b>+</b><span>Emotional pressure</span><b>+</b><span>Unusual request</span><b>+</b><span>Identity mismatch</span><strong>= Pause and verify</strong></div></div></section>

      <section className="learn-section learn-response" id="respond"><div className="container"><div className="learn-section-head"><div><span className="learn-kicker">Respond with a process</span><h2>Before, during, and after a suspicious request.</h2></div><p>Speed helps the fraudster. A simple response routine gives you back the decision time they are trying to remove.</p></div><div className="learn-response-grid"><article><span>Before money moves</span><h3>Pause and verify</h3><ul><li>Do not use the contact details sent in the suspicious message.</li><li>Find the organisation’s official number or website yourself.</li><li>Check the phone number, link, message or payment request.</li></ul><Link href="/detect">Check with Guard <ArrowRight size={14} /></Link></article><article><span>If you already acted</span><h3>Contain the loss</h3><ul><li>Contact the bank, mobile money provider or card issuer immediately.</li><li>Change exposed passwords and secure affected accounts.</li><li>Do not pay a second “recovery” or “release” fee.</li></ul><Link href="/report">Document the incident <ArrowRight size={14} /></Link></article><article className="official"><span>Official support</span><h3>Preserve and report</h3><ul><li>Keep screenshots, transaction IDs, numbers, URLs and timestamps.</li><li>CSA reporting contact: call or text <strong>292</strong>.</li><li>WhatsApp: <strong>050 160 3111</strong> · Email: <strong>report@csa.gov.gh</strong></li></ul><a href="https://www.csa.gov.gh/report" target="_blank" rel="noreferrer">Cyber Security Authority <ExternalLink size={13} /></a></article></div></div></section>

      <section className="learn-section learn-guides"><div className="container"><div className="learn-section-head"><div><span className="learn-kicker">Go deeper</span><h2>Practical guides for real situations.</h2></div><p>Use each guide to understand the setup, warning signals, verification steps and safest next action.</p></div><div className="learn-guide-grid">{guides.map(([title, text, slug, Icon], index) => <Link href={`/learn/${slug}`} key={slug}><span>{String(index + 1).padStart(2, '0')}</span><Icon size={19} /><h3>{title}</h3><p>{text}</p><b>Read guide <ArrowRight size={13} /></b></Link>)}</div></div></section>

      <section className="learn-method"><div className="container"><div><ShieldCheck size={24} /><span><strong>Evidence, with context.</strong><p>Guard distinguishes reported cases, attempted fraud, successful loss and value at risk. Statistics are dated, scoped and linked to their original publisher.</p></span></div><div className="learn-method-links"><a href={bogReport} target="_blank" rel="noreferrer">Bank of Ghana fraud report <ExternalLink size={12} /></a><a href={csaReport} target="_blank" rel="noreferrer">CSA annual report <ExternalLink size={12} /></a></div></div></section>
    </main>
    <Footer />
  </>;
}
