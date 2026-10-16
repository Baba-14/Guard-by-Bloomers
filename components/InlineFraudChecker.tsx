'use client';

import { useRef, useState } from 'react';
import {
  ArrowRight,
  BellRing,
  ChevronDown,
  FileImage,
  FileUp,
  Link2,
  LockKeyhole,
  MessageCircle,
  MessageSquare,
  Phone,
  WalletCards,
} from 'lucide-react';
import { AnalysisScanner, GuardResult, type AnalysisResult, type Kind } from './Checker';
import { authenticatedHeaders, responseJson } from '@/lib/client-api';
import { extractScreenshotText } from '@/lib/screenshot-ocr';

function ChannelVisual({ kind, icon: Icon }: { kind: Kind; icon: typeof MessageSquare }) {
  if (kind === 'whatsapp') return <span className="guided-channel-visual whatsapp"><img src="/images/channel-whatsapp.svg" alt=""/></span>;
  if (kind === 'message') return <span className="guided-channel-visual sms"><Icon size={19}/><b>SMS</b></span>;
  if (kind === 'screenshot') return <span className="guided-channel-visual screenshot"><i/><i/><i/><FileImage size={18}/></span>;
  if (kind === 'number') return <span className="guided-channel-visual number"><Phone size={17}/><b>+233</b></span>;
  if (kind === 'link') return <span className="guided-channel-visual web"><b>www</b><Link2 size={16}/></span>;
  if (kind === 'payment') return <span className="guided-channel-visual payment"><b>GH₵</b><WalletCards size={17}/></span>;
  return <span className="guided-channel-visual call"><i/><Phone size={20}/><i/></span>;
}

const options: Array<{
  kind: Kind;
  title: string;
  description: string;
  instruction: string;
  example: string;
  button: string;
  icon: typeof MessageSquare;
}> = [
  { kind:'payment', title:'Payment request or transfer', description:'Check who wants to be paid, the amount, recipient details, payment method, and the reason they gave.', instruction:'Describe who requested the money, the amount, the recipient name or number, and how they asked you to pay.', example:'Example: “The seller asked for GH₵450 to a different recipient name before delivery.”', button:'Check this payment', icon:WalletCards },
  { kind:'screenshot', title:'Screenshot or payment proof', description:'Upload a suspicious conversation, receipt, payment alert, seller page, or transaction screenshot.', instruction:'Upload the clearest image available. Keep the sender, amount and relevant message visible, but hide private documents or full card details.', example:'PNG, JPG, JPEG or WEBP · Maximum 10 MB', button:'Inspect this screenshot', icon:FileImage },
  { kind:'whatsapp', title:'WhatsApp request or account takeover', description:'A familiar account changed behaviour, contacted you from a new number, or asked for money, a code, or personal information.', instruction:'Enter the WhatsApp number. Add the unusual message and any request so Guard can understand what happened.', example:'Example: +233 24 000 0000 — “I changed my number. Send the money here instead.”', button:'Check WhatsApp signals', icon:MessageCircle },
  { kind:'message', title:'SMS, chat, email, or social message', description:'Check a suspicious SMS, WhatsApp message, email, social-media DM, alert, offer, or request.', instruction:'Paste the complete message exactly as you received it. Remove passwords, PINs and OTPs first.', example:'Example: “Your account will be suspended. Verify it now using this link.”', button:'Analyse this message', icon:MessageSquare },
  { kind:'number', title:'Phone number', description:'Look for reputation signals and moderated reports connected to a caller or sender.', instruction:'Enter the complete number, including the country code when possible.', example:'Example: +233 24 000 0000', button:'Check this number', icon:Phone },
  { kind:'link', title:'Link or website', description:'Inspect a URL before opening it, signing in, paying, or sharing personal information.', instruction:'Paste the complete link from the message or your browser. Do not open it just to copy more information.', example:'Example: https://example.com/verify-account', button:'Inspect this link', icon:Link2 },
  { kind:'call', title:'Suspicious call', description:'Describe a caller claiming to represent a bank, telco, government office, courier, or another person.', instruction:'Tell Guard who the caller claimed to be and exactly what they asked you to do or share.', example:'Example: “The caller said my wallet was blocked and asked me to read my OTP.”', button:'Analyse this call', icon:BellRing },
];

export function InlineFraudChecker() {
  const [active, setActive] = useState<Kind | null>('payment');
  const [input, setInput] = useState('');
  const [subject, setSubject] = useState('Individual or business');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [ocrProgress, setOcrProgress] = useState(0);
  const shellRef = useRef<HTMLDivElement>(null);
  const option = options.find(item => item.kind === active);

  const choose = (kind: Kind) => {
    setActive(current => current === kind ? null : kind);
    setInput('');
    setFile(null);
    setError('');
    setResult(null);
  };

  const submit = async () => {
    if (!active || (active === 'screenshot' ? !file && !input.trim() : !input.trim())) {
      setError(active === 'screenshot' ? 'Choose a screenshot or paste its visible text.' : 'Add something for Guard to check.');
      return;
    }
    setResult(null);
    setError('');
    setLoading(true);
    shellRef.current?.scrollIntoView({ behavior:'smooth', block:'start' });
    try {
      let content = input.trim();
      if (active === 'screenshot' && file) {
        setOcrProgress(1);
        content = await extractScreenshotText(file, setOcrProgress);
        setInput(content);
      }
      const response = await fetch('/api/analyse', { method:'POST', headers:authenticatedHeaders(), body:JSON.stringify({ kind:active, input: active === 'call' || active === 'payment' ? `${subject}. ${content}` : content }) });
      setResult(await responseJson<AnalysisResult>(response));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Guard could not complete the check.');
    } finally { setLoading(false); setOcrProgress(0); }
  };

  return <section id="checks" className="guided-check-section"><div className="container"><div className="guided-check-heading"><div><span className="eyebrow">Understand the risk</span><h2>What reached you?</h2></div><p>Choose the message, link, phone number, WhatsApp account, screenshot, call, or payment request. Guard will show you exactly what to add.</p></div><div className="guided-check-shell" ref={shellRef}><div className="guided-check-progress"><span className="active">1 <b>Choose</b></span><i/><span className={active?'active':''}>2 <b>Add details</b></span><i/><span className={result?'active':''}>3 <b>Choose an action</b></span></div><div className="guided-check-list">{options.map(({kind,title,description,icon:Icon}) => {const open=active===kind; return <article className={'guided-check-item channel-'+kind+(open?' open':'')} key={kind}><button type="button" aria-expanded={open} onClick={()=>choose(kind)}><ChannelVisual kind={kind} icon={Icon}/><span className="guided-check-item-copy"><em>{kind==='whatsapp'?'WhatsApp':kind==='message'?'SMS · chat · email':kind==='screenshot'?'Image upload':kind==='number'?'Caller or sender':kind==='link'?'Website or URL':kind==='payment'?'Transfer · bank · cash':'Voice call'}</em><strong>{title}</strong><small>{description}</small></span><span className="guided-check-open">{open?'Open':'Choose'} <ChevronDown size={17}/></span></button>{open&&option&&<div className="guided-check-panel">{loading?<><AnalysisScanner kind={kind} compact/>{kind==='screenshot'&&ocrProgress>0&&<p className="helper">Reading screenshot text… {ocrProgress}%</p>}</>:result?<GuardResult result={result} kind={kind} input={active==='call'||active==='payment'?`${subject}. ${input}`:input}/>:<div className="guided-check-form"><div className="guided-check-instruction"><span>What to provide</span><strong>{option.instruction}</strong><small>{option.example}</small></div>{kind==='screenshot'?<><label className="guided-upload"><FileUp size={28}/><strong>{file?.name || 'Choose a screenshot'}</strong><small>Text is read locally in your browser</small><input type="file" accept="image/png,image/jpeg,image/webp" onChange={event=>{setFile(event.target.files?.[0]||null);setError('')}}/></label><textarea className="textarea" rows={3} placeholder="Or paste the visible text here…" value={input} onChange={event=>setInput(event.target.value)}/></>:<div className="guided-check-fields">{(kind==='call'||kind==='payment')&&<label className="guided-check-subject"><span>{kind==='payment'?'Who wants to be paid?':'Who did they claim to be?'}</span><select className="select" value={subject} onChange={event=>setSubject(event.target.value)}><option>Individual or business</option><option>Bank</option><option>Telecom provider</option><option>Mobile-money provider</option><option>Government organisation</option><option>Other</option></select></label>}{kind==='message'||kind==='payment'||kind==='call'||kind==='whatsapp'?<textarea className="textarea" rows={kind==='whatsapp'?3:5} placeholder={option.example.replace('Example: ','')} value={input} onChange={event=>setInput(event.target.value)}/>:<input className="input" placeholder={option.example.replace('Example: ','')} value={input} onChange={event=>setInput(event.target.value)}/>}</div>}{error&&<p role="alert" style={{color:'#b14d46',fontSize:13}}>{error}</p>}<div className="guided-check-submit"><span><LockKeyhole size={14}/> Never submit a PIN, password, OTP, recovery code, or card details.</span><button type="button" className="btn btn-primary" disabled={loading||(kind==='screenshot'?!file&&!input.trim():!input.trim())} onClick={submit}>{option.button}<ArrowRight size={15}/></button></div></div>}</div>}</article>})}</div></div></div></section>;
}
