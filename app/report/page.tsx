'use client';

import { useEffect, useState } from 'react';
import { MessageCircle, ShieldAlert, WalletCards } from 'lucide-react';
import { Header, Footer } from '@/components/Header';

const reportTypes = ['Mobile Money or payment account', 'Payment screenshot or alert', 'WhatsApp number or account', 'Phone number', 'Website or link', 'Business', 'Social-media account', 'Message or call'] as const;
const categories = ['Mobile Money Fraud', 'Fake Payment Alert or Screenshot', 'Wrong Transfer or Reversal Request', 'WhatsApp Account Takeover', 'WhatsApp Impersonation', 'OTP or Verification Code Request', 'Phishing', 'Bank Impersonation', 'Fake Online Shop', 'Investment Fraud', 'Other'];

export default function Report(){
  const [sent,setSent]=useState<{reference:string}|null>(null);
  const [reportType,setReportType]=useState<(typeof reportTypes)[number]>('Mobile Money or payment account');
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
      const response=await fetch('/api/reports',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
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

  return <><Header/><main className="page-shell"><div className="container report-shell"><div className="page-title"><div className="eyebrow">Help prevent financial loss</div><h1>Report suspicious activity.</h1><p>Deliberately reporting content is different from making a private Guard check. Only this report flow can create a candidate for Guard&apos;s reviewed intelligence dataset.</p></div>{sent?<div className="result-card"><div className="result-top" style={{background:'#f7f1ff',borderColor:'#e8d9f7'}}><span className="risk-dot" style={{background:'#6d22b7'}}/><div><h2>Report received</h2><p>Your reference number is <strong>{sent.reference}</strong>. The de-identified candidate is pending human review and is not training data yet.</p></div></div></div>:<form className="form-panel" onSubmit={submit}><label className="label" htmlFor="report-type">What are you reporting?</label><select id="report-type" className="select" value={reportType} onChange={event=>setReportType(event.target.value as typeof reportType)}>{reportTypes.map(type=><option key={type}>{type}</option>)}</select>{isPayment&&<div className="report-whatsapp-note"><WalletCards size={20}/><div><strong>Mobile Money or payment fraud</strong><span>Report suspicious recipient details, reversal requests, fake alerts, manipulated screenshots, or pressure to pay before verifying.</span></div></div>}{isWhatsApp&&<div className="report-whatsapp-note"><MessageCircle size={20}/><div><strong>WhatsApp takeover or impersonation</strong><span>Report unusual money requests, OTP requests, suspicious links, or a contact whose account appears to have been taken over.</span></div></div>}<label className="label" htmlFor="fraud-category">Fraud category</label><select id="fraud-category" className="select" value={category} onChange={event=>setCategory(event.target.value)}>{categories.map(item=><option key={item}>{item}</option>)}</select><label className="label" htmlFor="report-identifier">{identifierLabel}</label><input id="report-identifier" className="input" inputMode={isWhatsApp||isPayment?'tel':'text'} placeholder={identifierPlaceholder} value={identifier} onChange={event=>setIdentifier(event.target.value)}/><label className="label" htmlFor="report-description">What happened?</label><textarea id="report-description" className="textarea" required minLength={10} value={description} onChange={event=>setDescription(event.target.value)} placeholder={isWhatsApp?'Explain how the account behaved differently, what it requested, and whether you verified the real owner another way.':isPayment?'Describe the amount, recipient, payment route, what you were told, and whether any money or goods were released.':'Describe what you received, what was requested, and what happened next.'}/><label className="label" htmlFor="report-evidence">Evidence</label><input id="report-evidence" className="input" type="file" accept="image/png,image/jpeg,image/webp" disabled/><p className="helper">Private evidence upload is awaiting your production object-storage configuration. The text report can be submitted now.</p><p className="helper"><ShieldAlert size={14}/> Do not include a Mobile Money PIN, password, full card details, OTP, or private information about other people.</p><label style={{display:'flex',gap:10,alignItems:'flex-start',marginTop:18,fontSize:13,lineHeight:1.5}}><input type="checkbox" checked={consent} onChange={event=>setConsent(event.target.checked)} required style={{marginTop:3}}/><span>I am intentionally reporting this content. I consent to Guard de-identifying it, allowing authorised analysts to review it, and adding it to the verified dataset only if a reviewer approves it.</span></label>{error&&<p role="alert" style={{color:'#b14d46',fontSize:13,marginTop:14}}>{error}</p>}<button className="btn btn-primary" style={{marginTop:22}} disabled={loading||!consent}>{loading?'Submitting…':'Submit Fraud Report'}</button></form>}</div></main><Footer/></>;
}
