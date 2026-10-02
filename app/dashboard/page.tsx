'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import {
  ArrowRight, Bell, Bookmark, CheckCircle2, ChevronRight, CircleAlert, LayoutDashboard,
  Clock3, FileText, Flag, Link2, MessageCircle, Phone, Plus, Search,
  ShieldCheck, Sparkles, TriangleAlert, WalletCards,
} from 'lucide-react';
import { Header, Footer } from '@/components/Header';
import styles from './dashboard.module.css';

type Risk = 'High risk' | 'Caution' | 'Low risk' | 'Unable to determine';
type Filter = 'All' | 'High risk' | 'Caution' | 'Low risk';

const checks: Array<{type:string; subject:string; result:Risk; time:string; icon:typeof MessageCircle}> = [
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
  const [filter,setFilter] = useState<Filter>('All');
  const [isAdmin,setIsAdmin] = useState(false);
  const filteredChecks = useMemo(()=>filter==='All'?checks:checks.filter(check=>check.result===filter),[filter]);
  useEffect(()=>setIsAdmin(sessionStorage.getItem('guard-demo-role')==='admin'),[]);

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
              <Link href="/report" className={styles.secondaryAction}><Flag size={17}/>Report fraud</Link>
              {isAdmin&&<Link href="/admin" className={styles.adminAction}><LayoutDashboard size={17}/>Admin dashboard</Link>}
            </div>
          </div>
          <div className={styles.heroSummary}>
            <div className={styles.heroSummaryTop}><span><Sparkles size={15}/> Your month with Guard</span><span className={styles.demoLabel}>Prototype data</span></div>
            <strong>4 risky requests</strong>
            <p>Guard highlighted four requests that needed more care before you acted.</p>
            <div className={styles.summaryTrack}><span/></div>
            <div className={styles.summaryMeta}><span>24 checks completed</span><b>Safer decisions</b></div>
          </div>
        </div>
      </section>

      <div className={`container ${styles.content}`}>
        <section className={styles.metrics} aria-label="Account overview">
          <article><span className={styles.metricIcon}><Search size={18}/></span><div><small>Total checks</small><strong>24</strong><p><b>+4</b> this month</p></div></article>
          <article><span className={styles.metricIcon}><TriangleAlert size={18}/></span><div><small>Warnings found</small><strong>7</strong><p>Across recent checks</p></div></article>
          <article><span className={styles.metricIcon}><Flag size={18}/></span><div><small>Reports submitted</small><strong>3</strong><p><b>1</b> under review</p></div></article>
          <article><span className={styles.metricIcon}><Bookmark size={18}/></span><div><small>Saved results</small><strong>8</strong><p>Ready when needed</p></div></article>
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
                {filteredChecks.length===0&&<div className={styles.emptyState}>No checks match this filter.</div>}
              </div>
              <footer className={styles.panelFooter}><span>Showing recent prototype activity</span><button type="button" onClick={()=>setFilter('All')}>View all checks <ArrowRight size={14}/></button></footer>
            </section>

            <section className={styles.panel}>
              <header className={styles.panelHeader}>
                <div><span className={styles.sectionLabel}>Follow-up</span><h2>Your fraud reports</h2></div>
                <Link href="/report" className={styles.textLink}>Submit report <Plus size={15}/></Link>
              </header>
              <div className={styles.reportList}>{reportItems.map(item=><article key={item.ref}>
                <span className={styles.reportIcon}><FileText size={17}/></span>
                <div><strong>{item.title}</strong><span>{item.ref} · {item.date}</span></div>
                <span className={item.status==='Under review'?styles.reviewStatus:styles.receivedStatus}>{item.status}</span>
                <ChevronRight size={17}/>
              </article>)}</div>
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
        <div className={styles.dataNote}><CircleAlert size={15}/><span>This dashboard currently uses sample data while account history and reporting services are connected.</span></div>
      </div>
    </main>
    <Footer/>
  </>;
}
