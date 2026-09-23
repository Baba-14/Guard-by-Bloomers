import Link from 'next/link';
import { Check, ArrowRight } from 'lucide-react';
import { Header, Footer } from '@/components/Header';

const plans = [
  { name: 'Everyday', price: 'Free', copy: 'For quick checks when something feels off.', features: ['5 checks per day', 'Message, link and number checks', 'Plain-language risk guidance'], action: 'Start checking', href: '/detect', featured: false },
  { name: 'Guard Plus', price: 'Coming soon', copy: 'More room to keep your digital decisions together.', features: ['Unlimited checks', 'Saved results and history', 'Priority report review'], action: 'Join the waitlist', href: '/register', featured: true },
  { name: 'Teams', price: 'Let’s talk', copy: 'Shared fraud intelligence for organisations and support teams.', features: ['Analyst workspace', 'Community intelligence tools', 'Configurable detection rules'], action: 'Contact Guard', href: '/report', featured: false }
];

export default function Pricing() { return <><Header/><main className="page-shell"><div className="container"><div className="page-title"><div className="eyebrow">Simple, fair access</div><h1>Protection should be easy to start.</h1><p>Use Guard for free today. Paid plans are designed for people and teams who need more history, collaboration and intelligence.</p></div><div className="pricing-grid">{plans.map(plan=><div className={'price-card '+(plan.featured?'price-card-featured':'')} key={plan.name}>{plan.featured&&<span className="price-badge">Coming next</span>}<h3>{plan.name}</h3><div className="price-value">{plan.price}</div><p>{plan.copy}</p><ul>{plan.features.map(feature=><li key={feature}><Check size={15}/>{feature}</li>)}</ul><Link href={plan.href} className={'btn '+(plan.featured?'btn-primary':'btn-outline')}>{plan.action}<ArrowRight size={15}/></Link></div>)}</div></div></main><Footer/></> }
