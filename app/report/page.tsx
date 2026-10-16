'use client';

import { useEffect, useState } from 'react';
import { Database, MessageCircle, Send, ShieldAlert, ShieldCheck, WalletCards } from 'lucide-react';
import { Header, Footer } from '@/components/Header';
import { authenticatedHeaders } from '@/lib/client-api';

const reportTypes = ['Message or call', 'Website or link', 'Phone number', 'WhatsApp number or account', 'Social-media account', 'Mobile Money or payment account', 'Payment screenshot or alert', 'Business'] as const;
const categories = ['Mobile Money Fraud', 'Fake Payment Alert or Screenshot', 'Wrong Transfer or Reversal Request', 'WhatsApp Account Takeover', 'WhatsApp Impersonation', 'OTP or Verification Code Request', 'Phishing', 'Bank Impersonation', 'Fake Online Shop', 'Investment Fraud', 'Other'];

export default function Report(){
  const [sent,setSent]=useState<{reference:string}|null>(null);
  const [reportType,setReportType]=useState<(typeof reportTypes)[number]>('Message or call');
  const [category,setCategory]=useState(categories[0]);
  const [identifier,setIdentifier]=useState('');
  const [description,setDescription]=useState('');
  const [consent,setConsent]=useState(false);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  const isWhatsApp=reportType==='WhatsApp number or account';
  const isPayment=reportType==='Mobile Money or payment account'||reportType==='Payment screenshot or alert';
  const identifierLabel=isWhatsApp?'WhatsApp number':isPayment?'Recipient number, account name, or transaction reference':'Phone, account, username, or link';
  const identifierPlaceholder=isWhatsApp?'+233 24 XXX XXXX':isPayment?'Add the payment identifier you can safely share':'Optional identifier';

  useEffect(()=>{
    const params=new URLSearchParams(window.location.search);
    const kind=params.get('kind');
    const submitted=params.get('input')?.trim();
    const typeByKind:Record<string,(typeof reportTypes)[number]>={
      payment:'Mobile Money or payment account',screenshot:'Payment screenshot or alert',whatsapp:'WhatsApp number or account',
      number:'Phone number',link:'Website or link',message:'Message or call',call:'Message or call',
    };
    if(kind&&typeByKind[kind]) setReportType(typeByKind[kind]);
    if(submitted){
      if(kind==='link'||kind==='number'||kind==='whatsapp') setIdentifier(submitted);
      setDescription(submitted.length>=10?submitted:`Suspicious ${kind||'item'} received: ${submitted}`);
    }
  },[]);

  const submit=async(event:React.FormEvent)=>{
    event.preventDefault(); setError(''); setLoading(true);
    try {
      const response=await fetch('/api/reports',{method:'POST',headers:authenticatedHeaders(),body:JSON.stringify({
        report_type:reportType,category,identifier:identifier||null,description,
        contribution_consent:consent,consent_version:'guard-report-v1',country_code:'GH',
        channel:isWhatsApp?'whatsapp':isPayment?'payment':'other',
      })});
      const body=await response.json();
      if(!response.ok) throw new Error(body.detail||'The report could not be submitted.');
      setSent(body);
    } catch(reason) { setError(reason instanceof Error?reason.message:'The report could not be submitted.'); }
    finally { setLoading(false); }
  };

  return <><Header/><main className="page-shell reports-page"><div className="container report-shell">
    <div className="page-title report-page-title"><div className="eyebrow">Reports &amp; community data</div><h1>Send fraud information to Guard.</h1><p>Report a suspicious message, number, account, link, payment request, or incident. Your submission becomes a review candidate—not trusted intelligence—until an authorised analyst verifies it.</p></div>
    {sent?<div className="report-success"><ShieldCheck size={28}/><div><span>Submission received</span><h2>Thank you for adding to Guard&apos;s fraud intelligence.</h2><p>Your reference number is <strong>{sent.reference}</strong>. The information is now pending human review and will not affect checks until it is verified.</p></div></div>:
    <form className="form-panel report-form" onSubmit={submit}>
      <section className="report-data-box">
        <div className="report-data-heading"><span><Database size={22}/></span><div><small>Submit data for review</small><h2>What information did you receive?</h2><p>Paste the message or describe what happened. Include useful context such as the payment request, sender, amount, number, account, or link.</p></div></div>
        <label className="label" htmlFor="report-description">Report or information</label>
        <textarea id="report-description" className="textarea report-data-input" required minLength={10} value={description} onChange={event=>setDescription(event.target.value)} placeholder={isWhatsApp?'Paste the unusual WhatsApp message and explain what the account requested…':isPayment?'Paste the payment request or describe the amount, recipient, payment route, and what you were told…':'Paste the suspicious content or describe exactly what happened…'}/>
        <p className="report-data-safety"><ShieldAlert size={15}/> Remove PINs, passwords, OTPs, full card details, and unrelated private information.</p>
      </section>

      <div className="report-details-heading"><span>Help us classify the report</span><p>These details make the submission easier for an analyst to review.</p></div>
      <div className="report-field-grid"><label><span className="label">What are you reporting?</span><select id="report-type" className="select" value={reportType} onChange={event=>setReportType(event.target.value as typeof reportType)}>{reportTypes.map(type=><option key={type}>{type}</option>)}</select></label><label><span className="label">Fraud category</span><select id="fraud-category" className="select" value={category} onChange={event=>setCategory(event.target.value)}>{categories.map(item=><option key={item}>{item}</option>)}</select></label></div>
      {isPayment&&<div className="report-whatsapp-note"><WalletCards size={20}/><div><strong>Mobile Money or payment fraud</strong><span>Add recipient details, reversal requests, fake alerts, manipulated screenshots, or pressure to pay.</span></div></div>}
      {isWhatsApp&&<div className="report-whatsapp-note"><MessageCircle size={20}/><div><strong>WhatsApp takeover or impersonation</strong><span>Add unusual money requests, OTP requests, suspicious links, or signs that the real owner lost control of the account.</span></div></div>}
      <label className="label" htmlFor="report-identifier">{identifierLabel}</label><input id="report-identifier" className="input" inputMode={isWhatsApp||isPayment?'tel':'text'} placeholder={identifierPlaceholder} value={identifier} onChange={event=>setIdentifier(event.target.value)}/>
      <label className="label" htmlFor="report-evidence">Evidence</label><input id="report-evidence" className="input" type="file" accept="image/png,image/jpeg,image/webp" disabled/><p className="helper">Screenshot upload is not part of the MVP demo yet. You can submit the visible text and description now.</p>
      <label className="report-consent"><input type="checkbox" checked={consent} onChange={event=>setConsent(event.target.checked)} required/><span><strong>I am intentionally submitting this information to Guard.</strong> Guard may de-identify it and allow authorised analysts to review it. It enters the verified dataset only after reviewer approval.</span></label>
      {error&&<p className="report-error" role="alert">{error}</p>}
      <button className="btn btn-primary report-submit" disabled={loading||!consent}>{loading?'Submitting…':<><Send size={16}/> Submit information for review</>}</button>
    </form>}
  </div></main><Footer/></>;
}
