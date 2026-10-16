'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { BrainCircuit, Building2, Check, Database, FileUp, Globe2, Inbox, LayoutDashboard, Link2, Loader2, Phone, Plus, ShieldCheck } from 'lucide-react';

type Section = 'Overview'|'Incoming Reports'|'Review Queue'|'Dataset'|'Training'|'URLs'|'Phone Numbers'|'Brands'|'Sources';
type Label = 'fraud'|'legitimate'|'uncertain';
type DatasetRow = {id:string;content:string;label:Label;category:string|null;source:string;source_type:string;country_code:string|null;is_ghana_specific:boolean;verification_status:string;channel?:string|null};
type ReviewRow = DatasetRow & {queue_id:string};
type Source = {id:string;name:string;source_type:string;description?:string;authoritative:boolean};
type Category = {id:string;name:string;slug:string};
type IntelligenceReport = {id:string;created_at:string;report_type:string|null;identifier:string|null;description:string;status:string;reporter:'registered'|'anonymous';category:string;review_status:string;channel:string|null};
type TrainingVersion = {id:string;name:string;version:string;status:string;notes:string|null;item_count:number;created_at:string};
type OverviewData = {total_items:number;pending_review:number;verified:number;ghana_specific:number;labels:Record<Label,number>;reports:{total:number;registered_reporters:number;anonymous_reports:number;training_ready:number;training_labels:{fraud:number;legitimate:number};by_type:{type:string;count:number}[];by_category:{category:string;reports:number;registered_reporters:number;verified:number}[]}};
type Notice = {kind:'ok'|'error';text:string}|null;

const sections:[Section,React.ElementType][]=[['Overview',LayoutDashboard],['Incoming Reports',Inbox],['Review Queue',ShieldCheck],['Dataset',Database],['Training',BrainCircuit],['URLs',Link2],['Phone Numbers',Phone],['Brands',Building2],['Sources',Globe2]];
const previewDataset:DatasetRow[]=[
  {id:'preview-1',content:'Your MoMo account will be suspended. Verify immediately using this link.',label:'fraud',category:'Phishing',source:'Guard user reports',source_type:'user_report',country_code:'GH',is_ghana_specific:true,verification_status:'verified',channel:'sms'},
  {id:'preview-2',content:'Your monthly statement is ready in the official banking app.',label:'legitimate',category:null,source:'Partner sample',source_type:'partner',country_code:'GH',is_ghana_specific:true,verification_status:'verified',channel:'sms'},
  {id:'preview-3',content:'Congratulations, call this number to receive your reward.',label:'uncertain',category:'Prize or Promotion Scam',source:'Manual entry',source_type:'manual',country_code:'GH',is_ghana_specific:true,verification_status:'pending',channel:'whatsapp'},
];
const previewSources:Source[]=[
  {id:'preview-user',name:'Guard user reports',source_type:'user_report',description:'Explicit, consented community reports',authoritative:false},
  {id:'preview-manual',name:'Guard manual entry',source_type:'manual',description:'Analyst-entered candidates',authoritative:false},
  {id:'preview-patterns',name:'Guard authoritative patterns',source_type:'authoritative_pattern',description:'Verified advisories and curated patterns',authoritative:true},
];
const previewCategories:Category[]=[{id:'preview-phishing',name:'Phishing',slug:'phishing'},{id:'preview-momo',name:'Mobile Money Fraud',slug:'mobile-money-fraud'},{id:'preview-impersonation',name:'Impersonation',slug:'impersonation'}];
const previewOverview:OverviewData={total_items:3,pending_review:1,verified:2,ghana_specific:3,labels:{fraud:1,legitimate:1,uncertain:1},reports:{total:2,registered_reporters:1,anonymous_reports:1,training_ready:1,training_labels:{fraud:1,legitimate:0},by_type:[{type:'Message or call',count:1},{type:'Website or link',count:1}],by_category:[{category:'Phishing',reports:1,registered_reporters:1,verified:1},{category:'Mobile Money Fraud',reports:1,registered_reporters:0,verified:0}]}};

async function api<T>(path:string,init:RequestInit={}):Promise<T>{
  const headers=new Headers(init.headers);
  if(init.body&&!(init.body instanceof FormData)) headers.set('Content-Type','application/json');
  const response=await fetch(`/api/intelligence/${path}`,{...init,headers});
  const body=await response.json();
  if(!response.ok) throw new Error(body.detail||'The intelligence request failed.');
  return body;
}

function Pill({value}:{value:string}){return <span className={`gi-pill gi-${value.replaceAll('_','-')}`}>{value.replaceAll('_',' ')}</span>}

export default function IntelligenceWorkspace(){
  const [section,setSection]=useState<Section>('Overview');
  const [dataset,setDataset]=useState<DatasetRow[]>(previewDataset);
  const [queue,setQueue]=useState<ReviewRow[]>(previewDataset.filter(x=>x.verification_status==='pending').map(x=>({...x,queue_id:`queue-${x.id}`})));
  const [sources,setSources]=useState<Source[]>(previewSources);
  const [categories,setCategories]=useState<Category[]>(previewCategories);
  const [reports,setReports]=useState<IntelligenceReport[]>([]);
  const [trainingVersions,setTrainingVersions]=useState<TrainingVersion[]>([]);
  const [overview,setOverview]=useState<OverviewData>(previewOverview);
  const [connected,setConnected]=useState(false);
  const [loading,setLoading]=useState(false);
  const [notice,setNotice]=useState<Notice>(null);
  const [filter,setFilter]=useState({label:'',source:'',ghana:false,verified:''});
  const [decision,setDecision]=useState<Label>('fraud');
  const [categoryId,setCategoryId]=useState('');
  const [notes,setNotes]=useState('');
  const [showAdd,setShowAdd]=useState(false);
  const [manual,setManual]=useState({content:'',label:'uncertain' as Label,source_id:'',category_id:'',channel:'sms',ghana:true});
  const [file,setFile]=useState<File|null>(null);

  const refresh=useCallback(async()=>{
    setLoading(true);
    try{
      const [summary,items,reviews,sourceRows,categoryRows,reportRows,versions]=await Promise.all([
        api<OverviewData>('overview'),api<DatasetRow[]>('dataset?limit=200'),api<ReviewRow[]>('review-queue'),api<Source[]>('sources'),api<Category[]>('categories'),api<IntelligenceReport[]>('reports'),api<TrainingVersion[]>('training-datasets'),
      ]);
      setOverview(summary);setDataset(items);setQueue(reviews);setSources(sourceRows);setCategories(categoryRows);setReports(reportRows);setTrainingVersions(versions);setConnected(true);
      setManual(value=>({...value,source_id:value.source_id||sourceRows.find(x=>x.source_type==='manual')?.id||sourceRows[0]?.id||''}));
    }catch(error){setNotice({kind:'error',text:error instanceof Error?error.message:'Could not load intelligence data.'});}
    finally{setLoading(false)}
  },[]);
  useEffect(()=>{refresh()},[refresh]);

  const filtered=useMemo(()=>dataset.filter(row=>(!filter.label||row.label===filter.label)&&(!filter.source||row.source_type===filter.source)&&(!filter.ghana||row.is_ghana_specific)&&(!filter.verified||row.verification_status===filter.verified)),[dataset,filter]);
  const currentReview=queue[0];

  const review=async()=>{
    if(!currentReview)return;
    if(decision==='fraud'&&!categoryId){setNotice({kind:'error',text:'Choose a fraud category before approving a fraud decision.'});return}
    setLoading(true);
    try{
      await api(`review-queue/${currentReview.queue_id}/decision`,{method:'POST',body:JSON.stringify({decision,category_id:categoryId||null,notes,approve:true})});
      setNotice({kind:'ok',text:'Review approved and moved into the verified dataset.'});setNotes('');await refresh();
    }catch(error){setNotice({kind:'error',text:error instanceof Error?error.message:'Could not save the review.'});}
    finally{setLoading(false)}
  };
  const addManual=async(event:React.FormEvent)=>{
    event.preventDefault();setLoading(true);
    try{
      await api('dataset',{method:'POST',body:JSON.stringify({content:manual.content,label:manual.label,source_id:manual.source_id,category_id:manual.category_id||null,channel:manual.channel,country_code:manual.ghana?'GH':null,is_ghana_specific:manual.ghana,language:'en'})});
      setNotice({kind:'ok',text:'Candidate added to the review queue.'});setShowAdd(false);setManual(value=>({...value,content:''}));await refresh();
    }catch(error){setNotice({kind:'error',text:error instanceof Error?error.message:'Could not add the candidate.'});}
    finally{setLoading(false)}
  };
  const upload=async()=>{
    if(!file||!manual.source_id)return;
    const body=new FormData();body.append('file',file);setLoading(true);
    try{const result=await api<{imported:number;duplicates_skipped:number}>(`dataset/import?source_id=${manual.source_id}`,{method:'POST',body});setNotice({kind:'ok',text:`Imported ${result.imported} candidates; ${result.duplicates_skipped} duplicates skipped. All are pending review.`});setFile(null);await refresh();}
    catch(error){setNotice({kind:'error',text:error instanceof Error?error.message:'Could not import the dataset.'});}
    finally{setLoading(false)}
  };
  const prepareTrainingDataset=async()=>{
    setLoading(true);setNotice(null);
    try{
      const result=await api<{item_count:number;trainable:boolean;version:string}>('training-datasets',{method:'POST',body:JSON.stringify({notes:'Prepared from the Guard Intelligence workspace'})});
      setNotice({kind:'ok',text:`Dataset ${result.version} prepared with ${result.item_count} reviewed items.${result.trainable?' It contains both fraud and legitimate examples.':' Add reviewed examples from both labels before running model training.'}`});
      await refresh();
    }catch(error){setNotice({kind:'error',text:error instanceof Error?error.message:'Could not prepare the training dataset.'});}
    finally{setLoading(false)}
  };

  return <div className="gi-shell">
    <div className="gi-subnav">{sections.map(([name,Icon])=><button key={name} className={section===name?'active':''} onClick={()=>setSection(name)}><Icon size={14}/>{name}{name==='Review Queue'&&<b>{overview.pending_review}</b>}</button>)}</div>
    <div className="gi-state"><span className={connected?'connected':''}/>{connected?'Live PostgreSQL data':'Preview data · sign in with an API-backed admin account to edit'}{loading&&<Loader2 className="gi-spin" size={14}/>}</div>
    {notice&&<div className={`gi-notice ${notice.kind}`}><span>{notice.text}</span><button onClick={()=>setNotice(null)}>×</button></div>}

    {section==='Overview'&&<><div className="gi-stats">{[['Reports received',overview.reports.total,'From the public reporting form'],['Registered reporters',overview.reports.registered_reporters,`${overview.reports.anonymous_reports} anonymous submissions`],['Pending review',overview.pending_review,'Waiting for an analyst'],['Training-ready',overview.reports.training_ready,'Consented fraud or legitimate labels']].map(([label,value,detail])=><article key={label}><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>)}</div><div className="gi-grid gi-report-overview"><section className="gi-card"><header><div><span>Community reporting</span><h2>Reports by fraud category</h2></div><Inbox size={20}/></header>{overview.reports.by_category.length?overview.reports.by_category.map(item=><div className="gi-category-row" key={item.category}><div><strong>{item.category}</strong><small>{item.verified} verified · {item.registered_reporters} registered reporters</small></div><b>{item.reports}</b></div>):<div className="gi-empty gi-empty-compact"><Inbox size={22}/><strong>No reports received yet</strong></div>}</section><section className="gi-card"><header><div><span>Submitted entities</span><h2>What people are reporting</h2></div><Database size={20}/></header>{overview.reports.by_type.length?overview.reports.by_type.map(item=><div className="gi-category-row" key={item.type}><div><strong>{item.type}</strong><small>Public fraud reports</small></div><b>{item.count}</b></div>):<div className="gi-empty gi-empty-compact"><Database size={22}/><strong>No report types yet</strong></div>}</section></div><div className="gi-grid"><section className="gi-card"><header><div><span>Dataset composition</span><h2>Labels after review</h2></div><ShieldCheck size={20}/></header>{Object.entries(overview.labels).map(([label,value])=><div className="gi-meter" key={label}><span>{label}</span><i><b style={{width:`${overview.total_items?Math.max(6,(value/overview.total_items)*100):0}%`}}/></i><strong>{value}</strong></div>)}</section><section className="gi-card gi-governance"><header><div><span>Governance gate</span><h2>Report → review → training version</h2></div></header><ol><li><b>1</b><span>Explicit report received<small>Message, link, phone number or payment information.</small></span></li><li><b>2</b><span>De-identification and analyst review<small>Assign fraud, legitimate or uncertain and confirm its category.</small></span></li><li><b>3</b><span>Version reviewed training data<small>Only consented, verified records are eligible.</small></span></li></ol></section></div></>}

    {section==='Incoming Reports'&&<section className="gi-table gi-reports-table"><table><thead><tr><th>Report</th><th>Category</th><th>Type</th><th>Reporter</th><th>Review</th><th>Received</th></tr></thead><tbody>{reports.map(report=><tr key={report.id}><td><strong>{report.description}</strong><small>{report.identifier||`GRD-${report.id.slice(0,8).toUpperCase()}`}</small></td><td>{report.category}</td><td>{report.report_type||'Unspecified'}<small>{report.channel||'No channel'}</small></td><td><Pill value={report.reporter}/></td><td><Pill value={report.review_status}/></td><td>{new Intl.DateTimeFormat('en-GH',{dateStyle:'medium',timeStyle:'short'}).format(new Date(report.created_at))}</td></tr>)}</tbody></table>{reports.length===0&&<div className="gi-empty"><Inbox size={28}/><strong>No public reports yet</strong><span>Reports submitted at /reports will appear here automatically.</span></div>}</section>}

    {section==='Review Queue'&&<section className="gi-review">{currentReview?<><div className="gi-review-copy"><span className="gi-kicker">{currentReview.source_type.replaceAll('_',' ')} · {currentReview.channel||'message'}</span><blockquote>{currentReview.content}</blockquote><dl><div><dt>Source</dt><dd>{currentReview.source}</dd></div><div><dt>Country</dt><dd>{currentReview.country_code||'Not set'}</dd></div><div><dt>Privacy</dt><dd>De-identified candidate</dd></div><div><dt>Status</dt><dd><Pill value={currentReview.verification_status}/></dd></div></dl></div><aside><span className="gi-kicker">Reviewer decision</span><div className="gi-decisions">{(['fraud','legitimate','uncertain'] as Label[]).map(label=><button key={label} className={decision===label?'active':''} onClick={()=>setDecision(label)}>{label}</button>)}</div><label>Fraud category<select value={categoryId} onChange={event=>setCategoryId(event.target.value)} disabled={decision!=='fraud'}><option value="">Choose category</option>{categories.map(item=><option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label>Review notes<textarea value={notes} onChange={event=>setNotes(event.target.value)} placeholder="Evidence and reasoning for the audit trail"/></label><button className="gi-primary" onClick={review} disabled={loading}><Check size={15}/>Approve and verify</button><small>Approval moves this item into the verified dataset. It does not retrain or deploy a model.</small></aside></>:<div className="gi-empty"><ShieldCheck size={28}/><strong>Review queue is clear</strong><span>New reports and imports will appear here.</span></div>}</section>}

    {section==='Dataset'&&<><div className="gi-toolbar"><div><select value={filter.label} onChange={e=>setFilter({...filter,label:e.target.value})}><option value="">All labels</option><option value="fraud">Fraud</option><option value="legitimate">Legitimate</option><option value="uncertain">Uncertain</option></select><select value={filter.source} onChange={e=>setFilter({...filter,source:e.target.value})}><option value="">All provenance</option>{['public_dataset','user_report','partner','authoritative_pattern','synthetic','manual'].map(x=><option key={x}>{x}</option>)}</select><select value={filter.verified} onChange={e=>setFilter({...filter,verified:e.target.value})}><option value="">All statuses</option><option value="verified">Verified</option><option value="pending">Pending</option></select><label><input type="checkbox" checked={filter.ghana} onChange={e=>setFilter({...filter,ghana:e.target.checked})}/>Ghana-specific</label></div><button className="gi-primary" onClick={()=>setShowAdd(!showAdd)}><Plus size={14}/>Add data</button></div>{showAdd&&<form className="gi-add" onSubmit={addManual}><label>Content<textarea required value={manual.content} onChange={e=>setManual({...manual,content:e.target.value})}/></label><label>Label<select value={manual.label} onChange={e=>setManual({...manual,label:e.target.value as Label})}><option>fraud</option><option>legitimate</option><option>uncertain</option></select></label><label>Source<select required value={manual.source_id} onChange={e=>setManual({...manual,source_id:e.target.value})}><option value="">Choose source</option>{sources.map(x=><option value={x.id} key={x.id}>{x.name}</option>)}</select></label><label>Category<select value={manual.category_id} onChange={e=>setManual({...manual,category_id:e.target.value})}><option value="">No category</option>{categories.map(x=><option value={x.id} key={x.id}>{x.name}</option>)}</select></label><button className="gi-primary" disabled={loading}>Add to review queue</button></form>}<div className="gi-import"><FileUp size={18}/><div><strong>Bulk import CSV, XLSX or JSON</strong><span>Expected fields: content/message, label, category, channel, country, ghana_specific.</span></div><select value={manual.source_id} onChange={e=>setManual({...manual,source_id:e.target.value})}><option value="">Choose provenance</option>{sources.map(x=><option value={x.id} key={x.id}>{x.name}</option>)}</select><input type="file" accept=".csv,.xlsx,.json" onChange={e=>setFile(e.target.files?.[0]||null)}/><button onClick={upload} disabled={!file||!manual.source_id||loading}>Import</button></div><div className="gi-table"><table><thead><tr><th>Content</th><th>Label</th><th>Category</th><th>Provenance</th><th>Ghana</th><th>Status</th></tr></thead><tbody>{filtered.map(row=><tr key={row.id}><td><strong>{row.content}</strong><small>{row.channel||'message'} · {row.country_code||'—'}</small></td><td><Pill value={row.label}/></td><td>{row.category||'—'}</td><td>{row.source}<small>{row.source_type.replaceAll('_',' ')}</small></td><td>{row.is_ghana_specific?'Yes':'No'}</td><td><Pill value={row.verification_status}/></td></tr>)}</tbody></table></div></>}

    {section==='Training'&&<><section className="gi-training-hero"><div><span className="gi-kicker">Governed model preparation</span><h2>Prepare reviewed intelligence for training</h2><p>Create an immutable dataset version from consented records that analysts have labelled fraud or legitimate. Pending and uncertain submissions are excluded.</p><div className="gi-training-facts"><span><strong>{overview.reports.training_ready}</strong> eligible records</span><span><strong>{overview.reports.training_labels.fraud}</strong> fraud labels</span><span><strong>{overview.reports.training_labels.legitimate}</strong> legitimate labels</span></div></div><button className="gi-primary" onClick={prepareTrainingDataset} disabled={loading||overview.reports.training_ready===0}><BrainCircuit size={16}/>{loading?'Preparing…':'Prepare training dataset'}</button></section><div className="gi-training-note"><ShieldCheck size={18}/><div><strong>Dataset preparation is not model deployment.</strong><span>This creates reproducible train, validation, test and holdout splits. A training runner and evaluation gate must be connected before Guard can train or release a model.</span></div></div><section className="gi-table"><table><thead><tr><th>Dataset version</th><th>Records</th><th>Status</th><th>Created</th></tr></thead><tbody>{trainingVersions.map(version=><tr key={version.id}><td><strong>{version.name}</strong><small>{version.version}</small></td><td>{version.item_count}</td><td><Pill value={version.status}/></td><td>{new Intl.DateTimeFormat('en-GH',{dateStyle:'medium',timeStyle:'short'}).format(new Date(version.created_at))}</td></tr>)}</tbody></table>{trainingVersions.length===0&&<div className="gi-empty"><BrainCircuit size={28}/><strong>No training dataset versions yet</strong><span>Review community reports, then prepare the first governed dataset version.</span></div>}</section></>}

    {section==='Sources'&&<section className="gi-directory">{sources.map(source=><article key={source.id}><Globe2 size={18}/><div><strong>{source.name}</strong><span>{source.description||'No description'}</span></div><Pill value={source.source_type}/>{source.authoritative&&<em>Authoritative</em>}</article>)}</section>}
    {section==='Brands'&&<Directory kind="brands" icon={Building2}/>}
    {section==='URLs'&&<Directory kind="urls" icon={Link2}/>}
    {section==='Phone Numbers'&&<Directory kind="phone-numbers" icon={Phone}/>}
  </div>;
}

function Directory({kind,icon:Icon}:{kind:'brands'|'urls'|'phone-numbers';icon:React.ElementType}){
  const [rows,setRows]=useState<Record<string,unknown>[]>([]);const [error,setError]=useState('');
  useEffect(()=>{api<Record<string,unknown>[]>(kind).then(setRows).catch(reason=>setError(reason.message))},[kind]);
  const examples:Record<string,unknown>[]=kind==='brands'?[{name:'MTN Ghana',country_code:'GH',verified:true,official_domains:['mtn.com.gh']}]:kind==='urls'?[{url:'mtn-support-example.net',verdict:'fraud',risk_score:94,reports:18,verified:true}]:[{sender_id:'+233 24 XXX XXXX',verdict:'uncertain',risk_score:62,reports:4,verified:false}];
  return <section className="gi-directory">{(rows.length?rows:examples).map((row,index)=><article key={String(row.id||index)}><Icon size={18}/><div><strong>{String(row.name||row.url||row.sender_id||'Unknown')}</strong><span>{kind==='brands'?`${String(row.country_code||'—')} · ${Array.isArray(row.official_domains)?row.official_domains.join(', '):''}`:`Risk ${String(row.risk_score||0)} · ${String(row.reports||0)} reports`}</span></div>{kind!=='brands'&&<Pill value={String(row.verdict||'uncertain')}/>}<em>{row.verified?'Verified':'Unverified'}</em></article>)}{error&&<p>{error}</p>}</section>;
}
