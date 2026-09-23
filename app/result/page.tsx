'use client';
import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, CalendarDays, ExternalLink, Link2, ShieldAlert, TriangleAlert } from 'lucide-react';
import { Header, Footer } from '@/components/Header';

type Assessment = { level: string; reason: string; signals: string[]; action: string; pattern?: string };

function ResultContent() {
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [input, setInput] = useState('');
  const [kind, setKind] = useState('link');
  useEffect(() => {
    const params = new URLSearchParams(window.location.search); const query = params.get('input') || ''; const queryKind = params.get('kind') || 'link'; setInput(query); setKind(queryKind);
    fetch('/api/analyse', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ kind: queryKind, input: query }) }).then(r => r.json()).then(setAssessment);
  }, []);
  if (!assessment) return <main className="result-page result-loading"><div><div className="eyebrow">Guard is checking</div><h1>Reviewing the signals…</h1><p>We’re checking the submitted information and preparing an explanation.</p></div></main>;
  const high = assessment.level === 'High Risk'; const caution = assessment.level === 'Caution';
  return <main className={'result-page '+(high?'result-high':caution?'result-caution':'result-uncertain')}><div className="container result-container"><Link href="/" className="result-back"><ArrowLeft size={15}/> Back to Guard</Link><div className="result-head"><div className="eyebrow">Guard intelligence result · {kind === 'number' ? 'Phone number' : 'Link'}</div><div className="result-status"><ShieldAlert size={44}/><div><h1>{assessment.level}</h1><p>{assessment.reason}</p></div></div><p className="result-disclaimer">This assessment is decision support based on the information submitted. It is not a legal determination of fraud, safety, or authenticity.</p></div><div className="result-grid"><div className="result-detail"><TriangleAlert size={20}/><span>Likely pattern<strong>{assessment.pattern || 'Fraud-risk assessment'}</strong></span></div><div className="result-detail"><Link2 size={20}/><span>Submitted item<strong className="truncate-value">{input}</strong></span></div><div className="result-detail"><ExternalLink size={20}/><span>Recommended action<strong>{assessment.action}</strong></span></div><div className="result-detail"><CalendarDays size={20}/><span>Guard status<strong>Reviewed just now</strong></span></div></div><section className="result-signals"><div><h2>Why Guard flagged it</h2><ul>{assessment.signals.map(signal => <li key={signal}><span>!</span>{signal}</li>)}</ul></div><div className="result-next"><h2>What to do next</h2><p>{assessment.action}</p><div className="result-actions"><Link href="/report" className="btn btn-outline">Report this <ArrowRight size={15}/></Link><Link href="/detect" className="btn btn-primary">Check something else <ArrowRight size={15}/></Link></div></div></section><div className="result-community"><strong>Community intelligence</strong><span>Reports and evidence help Guard identify recurring fraud patterns. Submit what happened to help protect others.</span><Link href="/report">Submit a report <ArrowRight size={14}/></Link></div></div></main>;
}

export default function ResultPage() { return <Suspense fallback={<main className="result-page result-loading"><h1>Loading result…</h1></main>}><ResultContent/></Suspense>; }
