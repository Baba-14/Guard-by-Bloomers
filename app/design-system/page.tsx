import {
  ArrowRight,
  Check,
  ChevronDown,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Sparkles,
  WalletCards,
  X,
} from 'lucide-react';

const swatches = [
  ['Void Plum', '#180A2E', 'Primary canvas'],
  ['Signal Violet', '#6D22B7', 'Brand / active'],
  ['Ultraviolet', 'rgba(152, 40, 229, 1)', 'Accent / glow'],
  ['Safety Orange', '#FF7A18', 'Warning / CTA'],
  ['Warm Gold', '#FFB52E', 'Highlight / attention'],
  ['Lilac Mist', '#F0E9FF', 'Soft surface'],
  ['Paper', '#FFFDFC', 'Primary surface'],
  ['Ink', '#241539', 'Primary text'],
];

const typeScale = [
  ['Display', '64 / 0.95', 'Not sure? Pause first.'],
  ['Heading 1', '42 / 1.05', 'Make safer decisions'],
  ['Heading 2', '28 / 1.1', 'Signals worth noticing'],
  ['Body', '16 / 1.55', 'Clear guidance for everyday digital life.'],
  ['Label', '12 / 1.2', 'SECURITY CHECK'],
];

function Section({ eyebrow, title, children }: { eyebrow: string; title: string; children: React.ReactNode }) {
  return <section className="ds-section"><div className="ds-section-head"><span className="ds-eyebrow">{eyebrow}</span><h2>{title}</h2></div>{children}</section>;
}

export default function DesignSystemPage() {
  return <main className="ds-page">
    <header className="ds-nav">
      <a className="ds-brand" href="#top"><span className="ds-brand-mark"><img src="/images/guard-white.png" alt=""/></span>Guard</a>
      <nav><a href="#tokens">Tokens</a><a href="#components">Components</a><a href="#patterns">Patterns</a></nav>
      <button className="ds-button ds-button-orange ds-button-small">Run a check <ArrowRight size={14}/></button>
    </header>

    <section id="top" className="ds-hero">
      <div className="ds-hero-copy"><span className="ds-eyebrow ds-eyebrow-orange">Guard design system / 01</span><h1>Clarity in the moment that matters.</h1><p>A bold, human security system for helping people pause, understand risk, and act with confidence.</p><div className="ds-hero-actions"><button className="ds-button ds-button-orange">Explore components <ArrowRight size={16}/></button><button className="ds-button ds-button-ghost">View principles</button></div></div>
      <div className="ds-orbit-art" aria-hidden="true"><div className="ds-orbit ds-orbit-1"/><div className="ds-orbit ds-orbit-2"/><div className="ds-orbit ds-orbit-3"/><div className="ds-head-shape"><LockKeyhole size={58}/></div><span className="ds-floating ds-float-mail"><Mail size={20}/></span><span className="ds-floating ds-float-wallet"><WalletCards size={22}/></span><span className="ds-floating ds-float-spark"><Sparkles size={19}/></span></div>
      <div className="ds-hero-stamp"><span className="ds-stamp-dot"/> Pause. Check. Decide.</div>
    </section>

    <div id="tokens" className="ds-content">
      <Section eyebrow="02 / Foundations" title="The system speaks in signals."><div className="ds-grid ds-grid-colors">{swatches.map(([name, hex, use])=><div className="ds-swatch" key={name}><div className="ds-color" style={{background:hex}}><span>{hex}</span></div><strong>{name}</strong><small>{use}</small></div>)}</div></Section>

      <Section eyebrow="03 / Typography" title="Confident, compact, human."><div className="ds-type-panel">{typeScale.map(([name, spec, sample])=><div className="ds-type-row" key={name}><div><span>{name}</span><small>{spec}</small></div><p className={'ds-type-'+name.toLowerCase().replace(' ','-')}>{sample}</p></div>)}</div></Section>

      <div id="components"><Section eyebrow="04 / Components" title="Built for quick comprehension."><div className="ds-component-grid">
        <div className="ds-demo-card"><span className="ds-eyebrow">Buttons</span><div className="ds-demo-row"><button className="ds-button ds-button-orange">Check this <ArrowRight size={15}/></button><button className="ds-button ds-button-dark">Secondary</button><button className="ds-icon-button"><ShieldCheck size={17}/></button></div><div className="ds-demo-row"><span className="ds-pill ds-pill-orange">High risk</span><span className="ds-pill ds-pill-gold">Needs review</span><span className="ds-pill ds-pill-lilac">Verified</span></div></div>
        <div className="ds-demo-card"><span className="ds-eyebrow">Input / quick check</span><label className="ds-input-label">Paste a link, phone number, or message</label><div className="ds-input-wrap"><input placeholder="e.g. https://example.com"/><button className="ds-input-submit"><ArrowRight size={16}/></button></div><small className="ds-helper">No account needed for a quick check.</small></div>
        <div className="ds-demo-card ds-dark-card"><span className="ds-eyebrow ds-eyebrow-orange">Security status</span><div className="ds-status-title"><span className="ds-status-icon"><LockKeyhole size={19}/></span><div><strong>Pause before paying</strong><small>3 signals need your attention</small></div></div><div className="ds-progress"><span/></div><div className="ds-status-foot"><span>Risk level</span><b>High</b></div></div>
        <div className="ds-demo-card"><span className="ds-eyebrow">Alert / caution</span><div className="ds-alert"><span className="ds-alert-icon">!</span><div><strong>This request looks unusual</strong><p>The sender is creating urgency and asking for payment through an unfamiliar route.</p><a href="#patterns">See the signals <ArrowRight size={13}/></a></div><button className="ds-close"><X size={15}/></button></div></div>
      </div></Section></div>

      <div id="patterns"><Section eyebrow="05 / Product patterns" title="A calm path through a high-stakes moment."><div className="ds-pattern"><div className="ds-pattern-side"><span className="ds-step-active">01</span><span>02</span><span>03</span></div><div className="ds-pattern-main"><div className="ds-pattern-top"><span className="ds-eyebrow">Message check</span><span className="ds-pattern-meta">2 min read</span></div><h3>“Your account will be closed today. Send the code now.”</h3><p>Guard finds pressure language, a request for a one-time code, and an identity mismatch.</p><div className="ds-signal-list"><div><span className="ds-check"><Check size={13}/></span><div><strong>Urgency is being used</strong><small>Scammers often force a rushed decision.</small></div></div><div><span className="ds-check"><Check size={13}/></span><div><strong>Never share a verification code</strong><small>Legitimate teams won’t ask for your private code.</small></div></div></div><button className="ds-button ds-button-orange">Show me what to do <ArrowRight size={16}/></button></div></div></Section></div>
    </div>
    <footer className="ds-footer"><span className="ds-brand"><span className="ds-brand-mark"><img src="/images/guard-violet.png" alt=""/></span>Guard</span><span>Design system preview · Signal over noise</span></footer>
  </main>;
}
