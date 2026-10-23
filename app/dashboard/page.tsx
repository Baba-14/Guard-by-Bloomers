'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import {
  ArrowRight, Bell, Bookmark, CheckCircle2, ChevronRight, CircleAlert, LayoutDashboard,
  Clock3, FileText, Flag, Link2, MessageCircle, Phone, Plus, Search,
  ShieldCheck, Sparkles, TriangleAlert, WalletCards,
} from 'lucide-react';
import { Header, Footer } from '@/components/Header';
import styles from './dashboard.module.css';
import { authenticatedHeaders, responseJson } from '@/lib/client-api';
import { demoAuthEnabled } from '@/lib/demo-auth';

type Risk = 'High risk' | 'Caution' | 'Low risk' | 'Unable to determine';
type Filter = 'All' | 'High risk' | 'Caution' | 'Low risk';

type CheckItem = {type:string;subject:string;result:Risk;time:string;icon:typeof MessageCircle};
type HistoryItem = {id:string;check_type:string;risk_level:string|null;risk_score:number|null;pattern:string|null;created_at:string};

const sampleChecks: CheckItem[] = [
  { type:'WhatsApp message', subject:'Urgent request from a known contact', result:'High risk', time:'Today, 10:42', icon:MessageCircle },
  { type:'Phone number', subject:'+233 24 ••• ••18', result:'Caution', time:'Yesterday', icon:Phone },
  { type:'Payment request', subject:'Mobile Money recipient details', result:'Low risk', time:'22 Sep', icon:WalletCards },
  { type:'Website link', subject:'merchant-support-check.com', result:'Unable to determine', time:'18 Sep', icon:Link2 },
];

const reportItems = [
  { title:'Suspicious payment request', ref:'GRD-2026-1842', status:'Under review', date:'21 Sep' },
  { title:'WhatsApp impersonation', ref:'GRD-2026-1794', status:'Received', date:'12 Sep' },
];

const quickChecks = [
  { label:'Check a message', detail:'Paste suspicious text', icon:MessageCircle, href:'/detect/message' },
  { label:'Check a number', detail:'Review a caller or recipient', icon:Phone, href:'/detect/number' },
  { label:'Check a link', detail:'Inspect a suspicious website', icon:Link2, href:'/detect/link' },
  { label:'Check a payment', detail:'Review before money moves', icon:WalletCards, href:'/detect/payment' },
] as const;

function RiskBadge({result}:{result:Risk}) {
  const Icon = result === 'High risk' ? TriangleAlert : result === 'Low risk' ? CheckCircle2 : CircleAlert;
  return <span className={`${styles.riskBadge} ${styles[`risk${result.replaceAll(' ','')}`]}`}><Icon size={13}/>{result}</span>;
}

export default function Dashboard() {
  const router = useRouter();
  const [filter,setFilter] = useState<Filter>('All');
  const [isAdmin,setIsAdmin] = useState(false);
  const [workspaceHref,setWorkspaceHref] = useState('/admin');
  const [workspaceLabel,setWorkspaceLabel] = useState('Admin dashboard');
  const [checks,setChecks] = useState<CheckItem[]>([]);
  const [demo,setDemo] = useState(false);
  const [historyError,setHistoryError] = useState('');
  const filteredChecks = useMemo(()=>filter==='All'?checks:checks.filter(check=>check.result===filter),[filter,checks]);
  useEffect(()=>{
    const demoRole=demoAuthEnabled?sessionStorage.getItem('guard-demo-auth'):null;
    if(demoRole){setDemo(true);setChecks(sampleChecks);setIsAdmin(demoRole==='admin');return}
    fetch('/api/auth/me')
      .then(response=>responseJson<{role:string}>(response))
      .then(async user=>{if(user.role==='super_admin'){setIsAdmin(true);setWorkspaceHref('/admin');setWorkspaceLabel('Admin dashboard')}else if(user.role==='fraud_analyst'){setIsAdmin(true)}else{const partner=await fetch('/api/partner/overview').catch(()=>null);if(partner?.ok){setIsAdmin(true);setWorkspaceHref('/partner');setWorkspaceLabel('Partner dashboard')}}return fetch('/api/history',{headers:authenticatedHeaders(false)})})
      .then(response=>responseJson<HistoryItem[]>(response))
      .then(rows=>setChecks(rows.map(row=>({
        type:row.check_type.replace(/^./,value=>value.toUpperCase()),
        subject:row.pattern||'Guard risk assessment',
        result:row.risk_level==='high'?'High risk':row.risk_level==='caution'?'Caution':row.risk_level==='low'?'Low risk':'Unable to determine',
        time:new Intl.DateTimeFormat('en-GH',{dateStyle:'medium',timeStyle:'short'}).format(new Date(row.created_at)),
        icon:row.check_type==='link'?Link2:row.check_type==='number'?Phone:row.check_type==='payment'?WalletCards:MessageCircle,
      }))))
      .catch(()=>router.replace('/login'));
  },[router]);

  return <>
    <Header/>
    <main className={styles.dashboard}>
      <section className={styles.hero}>
        <div className={`container ${styles.heroInner}`}>
          <div>
            <div className={styles.eyebrow}><ShieldCheck size={15}/> Your protection centre</div>
            <h1>Good to see you.</h1>
            <p>Check suspicious requests, revisit past decisions and keep track of every report in one place.</p>
            <div className={styles.heroActions}>
              <Link href="/detect" className={styles.primaryAction}><Search size={18}/>Start a new check</Link>
              <Link href="/reports" className={styles.secondaryAction}><Flag size={17}/>Report fraud</Link>
              {isAdmin&&<Link href={workspaceHref} className={styles.adminAction}><LayoutDashboard size={17}/>{workspaceLabel}</Link>}
            </div>
          </div>
          <div className={styles.heroSummary}>
            <div className={styles.heroSummaryTop}><span><Sparkles size={15}/> Your recent Guard activity</span>{demo&&<span className={styles.demoLabel}>Prototype data</span>}</div>
            <strong>{checks.filter(item=>item.result==='High risk'||item.result==='Caution').length} risky requests</strong>
            <p>Guard highlights requests that need more care before you act.</p>
            <div className={styles.summaryTrack}><span/></div>
            <div className={styles.summaryMeta}><span>{checks.length} recent checks</span><b>Safer decisions</b></div>
          </div>
        </div>
      </section>

      <div className={`container ${styles.content}`}>
        <section className={styles.metrics} aria-label="Account overview">
          <article><span className={styles.metricIcon}><Search size={18}/></span><div><small>Recent checks</small><strong>{checks.length}</strong><p>Latest saved history</p></div></article>
          <article><span className={styles.metricIcon}><TriangleAlert size={18}/></span><div><small>Warnings found</small><strong>{checks.filter(item=>item.result==='High risk'||item.result==='Caution').length}</strong><p>Across recent checks</p></div></article>
          <article><span className={styles.metricIcon}><Flag size={18}/></span><div><small>Reports submitted</small><strong>{demo?'3':'—'}</strong><p>{demo?'1 under review':'Report tracking is coming next'}</p></div></article>
          <article><span className={styles.metricIcon}><Bookmark size={18}/></span><div><small>Saved results</small><strong>{checks.length}</strong><p>Ready when needed</p></div></article>
        </section>

        <div className={styles.layout}>
          <div className={styles.mainColumn}>
            <section className={styles.panel}>
              <header className={styles.panelHeader}>
                <div><span className={styles.sectionLabel}>Recent activity</span><h2>Your latest checks</h2></div>
                <Link href="/detect" className={styles.textLink}>New check <Plus size={15}/></Link>
              </header>
              <div className={styles.filterTabs} role="tablist" aria-label="Filter recent checks">
                {(['All','High risk','Caution','Low risk'] as Filter[]).map(option=><button key={option} role="tab" aria-selected={filter===option} className={filter===option?styles.activeTab:''} onClick={()=>setFilter(option)}>{option}</button>)}
              </div>
              <div className={styles.checkList}>
                {filteredChecks.map(check=>{ const Icon=check.icon; return <article className={styles.checkRow} key={`${check.type}-${check.time}`}>
                  <span className={styles.checkIcon}><Icon size={18}/></span>
                  <div className={styles.checkCopy}><strong>{check.type}</strong><span>{check.subject}</span></div>
                  <RiskBadge result={check.result}/>
                  <time><Clock3 size={13}/>{check.time}</time>
                  <Link href="/detect" className={styles.rowAction} aria-label={`Check another ${check.type}`}><ChevronRight size={18}/></Link>
                </article>})}
                {filteredChecks.length===0&&<div className={styles.emptyState}>{historyError||'No checks match this filter yet.'}</div>}
              </div>
              <footer className={styles.panelFooter}><span>{demo?'Showing prototype activity':'Showing your saved checks'}</span><button type="button" onClick={()=>setFilter('All')}>View all checks <ArrowRight size={14}/></button></footer>
            </section>

            <section className={styles.panel}>
              <header className={styles.panelHeader}>
                <div><span className={styles.sectionLabel}>Follow-up</span><h2>Your fraud reports</h2></div>
                <Link href="/reports" className={styles.textLink}>Submit report <Plus size={15}/></Link>
              </header>
              <div className={styles.reportList}>{demo?reportItems.map(item=><article key={item.ref}>
                <span className={styles.reportIcon}><FileText size={17}/></span>
                <div><strong>{item.title}</strong><span>{item.ref} · {item.date}</span></div>
                <span className={item.status==='Under review'?styles.reviewStatus:styles.receivedStatus}>{item.status}</span>
                <ChevronRight size={17}/>
              </article>):<div className={styles.emptyState}>Report status tracking is not part of this MVP yet. Keep the reference shown after submission.</div>}</div>
            </section>
          </div>

          <aside className={styles.sideColumn}>
            <section className={`${styles.panel} ${styles.safetyCard}`}>
              <div className={styles.safetyTop}><span className={styles.sectionLabel}>Safety snapshot</span><Bell size={18}/></div>
              <div className={styles.safetyScore}>
                <div className={styles.scoreRing}><span><strong>78</strong><small>of 100</small></span></div>
                <div><strong>Strong habits</strong><p>You usually verify suspicious requests before responding.</p></div>
              </div>
              <div className={styles.safetyTip}><ShieldCheck size={19}/><div><strong>Keep it up</strong><span>Never share an OTP, PIN or password, even with someone you trust.</span></div></div>
            </section>

            <section className={`${styles.panel} ${styles.quickPanel}`}>
              <header><span className={styles.sectionLabel}>Quick actions</span><h2>What do you want to check?</h2></header>
              <div>{quickChecks.map(item=>{ const Icon=item.icon; return <Link key={item.label} href={item.href}><span><Icon size={17}/></span><div><strong>{item.label}</strong><small>{item.detail}</small></div><ChevronRight size={16}/></Link>})}</div>
            </section>

            <section className={styles.learnCard}>
              <span className={styles.learnIcon}><Sparkles size={21}/></span>
              <span className={styles.sectionLabel}>Recommended for you</span>
              <h2>Three signs a payment request needs a second look</h2>
              <p>Learn how urgency, unusual recipient details and requests for private codes often appear together.</p>
              <Link href="/learn">Read the safety guide <ArrowRight size={15}/></Link>
            </section>
          </aside>
        </div>
        {demo&&<div className={styles.dataNote}><CircleAlert size={15}/><span>This demo account uses sample data. Sign in with a registered account to see persisted check history.</span></div>}
      </div>
    </main>
    <Footer/>
  </>;
}
