import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { Header, Footer } from '@/components/Header';

const questions = [
  ['What is Guard?', 'Guard is a fraud-risk decision-support tool. It helps you inspect suspicious messages, links, phone numbers, calls, screenshots and payment requests before you act.'],
  ['Does Guard guarantee that something is safe or fraudulent?', 'No. Guard provides guidance based on the information submitted and available signals. Treat every result as decision support, not as an absolute guarantee.'],
  ['Do I need an account to check something?', 'No. You can use the quick checker without an account. An account may be useful when you want to save results or manage reports.'],
  ['What should I never share with Guard?', 'Do not submit passwords, PINs, one-time passwords, private keys or other secrets. Remove sensitive personal information before submitting screenshots or messages.'],
  ['How does Guard use community reports?', 'Community reports help identify recurring patterns and improve the context shown to users. We aim to remove unnecessary personal information and do not treat a report as proof by itself.'],
  ['What should I do if I have already lost money?', 'Contact your bank or mobile-money provider immediately through an official channel, secure your accounts, preserve evidence and report the incident to the relevant authorities.'],
];

export default function FAQ() { return <><Header/><main className="page-shell"><div className="container faq-shell"><div className="page-title"><div className="eyebrow">Help and guidance</div><h1>Frequently asked questions.</h1><p>Clear answers about checking suspicious activity, privacy and what Guard can—and cannot—do.</p></div><div className="faq-list">{questions.map(([question,answer])=><details key={question}><summary>{question}<span>+</span></summary><p>{answer}</p></details>)}</div><div className="faq-cta"><div><strong>Still unsure about something?</strong><span>Use Guard to check the interaction before you respond.</span></div><Link href="/detect" className="btn btn-primary">Start a check <ArrowRight size={15}/></Link></div></div></main><Footer/></> }
