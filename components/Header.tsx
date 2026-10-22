 'use client';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { ChevronDown, Menu, X } from 'lucide-react';
import { demoAuthEnabled } from '@/lib/demo-auth';

export function Header({ overlay = false }: { overlay?: boolean }) {
  const [hidden, setHidden] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [checkMenuOpen, setCheckMenuOpen] = useState(false);
  const [role, setRole] = useState<'admin' | 'user' | null>(null);
  const previousY = useRef(0);
  useEffect(() => {
    const demoRole = demoAuthEnabled ? sessionStorage.getItem('guard-demo-auth') : null;
    if (demoRole === 'admin' || demoRole === 'user') setRole(demoRole);
    else fetch('/api/auth/me').then(async response=>{
      if(!response.ok)return;
      const user=await response.json();
      setRole(['super_admin','fraud_analyst'].includes(user.role)?'admin':'user');
    }).catch(()=>{});
    const onScroll = () => {
      const currentY = window.scrollY;
      setScrolled(currentY > 24);
      if (currentY > 80 && currentY > previousY.current + 6) setHidden(true);
      else if (currentY < previousY.current - 6 || currentY < 24) setHidden(false);
      if (currentY > previousY.current + 12) { setMenuOpen(false); setCheckMenuOpen(false); }
      previousY.current = currentY;
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  const closeNavigation=()=>{setMenuOpen(false);setCheckMenuOpen(false);};
  const signOut=async()=>{await fetch('/api/auth/logout',{method:'POST'}).catch(()=>{});sessionStorage.removeItem('guard-demo-auth');setRole(null);window.location.assign('/')};
  const headerClass = ['site-header', overlay ? 'site-header-overlay' : '', scrolled ? 'site-header-scrolled' : '', hidden ? 'site-header-hidden' : ''].filter(Boolean).join(' ');
  return <><header className={headerClass}><div className="container" style={{display:'flex',width:'100%',alignItems:'center',justifyContent:'space-between'}}>
    <Link href="/" className="brand"><span className="brand-mark brand-mark-image"><img src={overlay||scrolled?'/images/guard-white.png':'/images/guard-violet.png'} alt=""/></span><span>Guard</span></Link>
    <button type="button" className="mobile-nav-toggle" aria-label={menuOpen?'Close navigation':'Open navigation'} aria-expanded={menuOpen} aria-controls="primary-navigation" onClick={()=>setMenuOpen(open=>!open)}>{menuOpen?<X size={21}/>:<Menu size={21}/>}</button>
    <nav id="primary-navigation" className={'nav '+(!overlay?'nav-light':'')+(menuOpen?' nav-open':'')}><Link href="/" onClick={closeNavigation}>Home</Link><div className={'nav-dropdown'+(checkMenuOpen?' open':'')}><button type="button" className="nav-dropdown-trigger" aria-expanded={checkMenuOpen} aria-controls="check-fraud-menu" onClick={()=>setCheckMenuOpen(open=>!open)}>Check Fraud <ChevronDown size={15}/></button><div id="check-fraud-menu" className="nav-dropdown-menu"><Link href="/detect" onClick={closeNavigation}>Check</Link><Link href="/learn" onClick={closeNavigation}>Learn</Link><Link href="/contribute" onClick={closeNavigation}>Contribute</Link><Link href="/reports" onClick={closeNavigation}>Reports</Link></div></div><Link href="/community" onClick={closeNavigation}>Community</Link><Link href="/business" onClick={closeNavigation}>Business</Link><Link href={role==='admin'?'/admin':role==='user'?'/dashboard':'/login'} className="btn btn-primary" onClick={closeNavigation}>{role==='admin'?'Admin':role==='user'?'Dashboard':'Login'}</Link>{role&&<button type="button" onClick={signOut} style={{border:0,background:'transparent',color:'inherit',cursor:'pointer'}}>Sign out</button>}</nav>
  </div></header></>;
}

export function Footer() { return <footer className="footer"><div className="container footer-grid"><div className="footer-intro"><Link href="/" className="brand"><span className="brand-mark brand-mark-image"><img src="/images/guard-violet.png" alt=""/></span><span>Guard</span></Link><p>Helping people and businesses check suspicious messages, links, calls, accounts, and payments before acting.</p><span className="footer-meta">Fraud intelligence and practical guidance built for Ghana.</span></div><div className="footer-column"><strong>Protect yourself</strong><Link href="/detect">Run a fraud check</Link><Link href="/learn">Learn fraud patterns</Link><Link href="/reports">Report fraud</Link><Link href="/contribute">Contribute safely</Link></div><div className="footer-column"><strong>Guard</strong><Link href="/business">For businesses</Link><Link href="/pricing">Pricing</Link><Link href="/about">About us</Link></div><div className="footer-column"><strong>Trust</strong><Link href="/faq">FAQ</Link><Link href="/privacy">Privacy Policy</Link><Link href="/terms">Terms &amp; Conditions</Link></div></div><div className="container footer-bottom"><span>© 2026 Guard. All rights reserved.</span><span>Guard supports safer decisions — never absolute certainty.</span></div></footer>; }
