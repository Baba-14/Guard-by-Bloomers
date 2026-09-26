'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  CheckCircle2,
  Link2,
  MessageCircle,
  Phone,
  ScanSearch,
  ShieldAlert,
  WalletCards,
} from 'lucide-react';

const scenarios = [
  {
    label: 'WhatsApp',
    icon: MessageCircle,
    sender: 'Kwame — new number',
    time: '10:42',
    message: 'Please send GH₵800 now. I will explain later. Do not call this number.',
    score: 86,
    verdict: 'High risk',
    tone: 'danger',
    signal: 'Urgency + identity change',
    action: 'Call the person on the number you already know.',
    href: '/detect/whatsapp',
  },
  {
    label: 'Mobile Money',
    icon: WalletCards,
    sender: 'MoMo adjustment',
    time: '12:18',
    message: 'A transfer was made to you by mistake. Send it back to this merchant number now.',
    score: 72,
    verdict: 'Caution',
    tone: 'caution',
    signal: 'Reversal pressure',
    action: 'Confirm your balance and contact your provider directly.',
    href: '/detect/payment',
  },
  {
    label: 'Suspicious link',
    icon: Link2,
    sender: 'Delivery update',
    time: '14:03',
    message: 'Your parcel is on hold. Pay the GH₵4.50 delivery fee at gh-post-track.help.',
    score: 91,
    verdict: 'High risk',
    tone: 'danger',
    signal: 'Imitation domain + payment',
    action: 'Do not open the link. Visit the courier site yourself.',
    href: '/detect/link',
  },
  {
    label: 'Phone call',
    icon: Phone,
    sender: 'Unknown caller',
    time: '16:27',
    message: 'Your bank account is being closed. Read the six-digit code to stop it.',
    score: 95,
    verdict: 'High risk',
    tone: 'danger',
    signal: 'OTP request + fear',
    action: 'End the call and contact your bank using its official number.',
    href: '/detect/call',
  },
] as const;

export function GuardDemo() {
  const [active, setActive] = useState(0);
  const scenario = scenarios[active];
  const Icon = scenario.icon;

  return (
    <section className="guard-demo-section">
      <div className="container">
        <div className="guard-demo-heading">
          <div>
            <span className="eyebrow">See Guard in the moment</span>
            <h2>Fraud moves fast.<br/>Your answer should be clear.</h2>
          </div>
          <p>Explore a familiar situation and see how Guard turns a suspicious request into signals you can understand and an action you can take.</p>
        </div>

        <div className="guard-demo-tabs" role="tablist" aria-label="Fraud examples">
          {scenarios.map((item, index) => {
            const TabIcon = item.icon;
            return <button key={item.label} type="button" role="tab" aria-selected={active === index} className={active === index ? 'active' : ''} onClick={() => setActive(index)}><TabIcon size={16}/>{item.label}</button>;
          })}
        </div>

        <div className="guard-demo-stage" data-tone={scenario.tone}>
          <div className="guard-demo-copy">
            <span className="guard-demo-step">01 / What reached you</span>
            <h3>It looks believable.<br/>That is the point.</h3>
            <p>Pressure, a familiar name, and a small change in behaviour can be enough to make someone act before they verify.</p>
            <div className="guard-demo-signal"><ShieldAlert size={19}/><span><small>Signal Guard noticed</small><strong>{scenario.signal}</strong></span></div>
            <Link href={scenario.href} className="btn btn-primary">Check something like this <ArrowRight size={16}/></Link>
          </div>

          <div className="guard-phone-wrap" aria-live="polite">
            <div className="guard-orbit guard-orbit-one"/>
            <div className="guard-orbit guard-orbit-two"/>
            <div className="guard-phone">
              <img className="guard-phone-frame" src="/images/guard-iphone-frame.png" alt="" aria-hidden="true"/>
              <div className="guard-phone-screen">
                <div className="guard-phone-island"/>
                <div className="guard-phone-top"><span>{scenario.time}</span><i/><b>Guard</b></div>
                <div className="guard-phone-contact"><span><Icon size={20}/></span><div><strong>{scenario.sender}</strong><small>{scenario.label}</small></div></div>
                <div className="guard-phone-message">{scenario.message}</div>
                <div className="guard-phone-checking"><ScanSearch size={15}/><span>Guard checked the request</span><i/></div>
                <div className="guard-phone-result">
                  <div className="guard-phone-score"><strong>{scenario.score}</strong><span>risk<br/>score</span></div>
                  <div><small>Assessment</small><strong>{scenario.verdict}</strong></div>
                </div>
                <div className="guard-phone-action"><CheckCircle2 size={17}/><span>{scenario.action}</span></div>
              </div>
            </div>
          </div>

          <div className="guard-demo-outcome">
            <span className="guard-demo-step">02 / What you can do</span>
            <div className="guard-demo-outcome-mark"><img src="/images/guard-yellow.png" alt=""/></div>
            <h3>Pause with a reason,<br/>not just a warning.</h3>
            <p>Guard shows what raised concern, what to avoid, and how to verify safely through another channel.</p>
            <ul><li><CheckCircle2 size={15}/> Plain-language assessment</li><li><CheckCircle2 size={15}/> Visible risk signals</li><li><CheckCircle2 size={15}/> A practical next step</li></ul>
          </div>
        </div>
      </div>
    </section>
  );
}
