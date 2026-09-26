 'use client';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { Menu, X } from 'lucide-react';

export function Header({ overlay = false }: { overlay?: boolean }) {
  const [hidden, setHidden] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const previousY = useRef(0);
  useEffect(() => {
    const onScroll = () => {
      const currentY = window.scrollY;
      setScrolled(currentY > 24);
      if (currentY > 80 && currentY > previousY.current + 6) setHidden(true);
      else if (currentY < previousY.current - 6 || currentY < 24) setHidden(false);
      if (currentY > previousY.current + 12) setMenuOpen(false);
      previousY.current = currentY;
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  const headerClass = ['site-header', overlay ? 'site-header-overlay' : '', scrolled ? 'site-header-scrolled' : '', hidden ? 'site-header-hidden' : ''].filter(Boolean).join(' ');
  return <><header className={headerClass}><div className="container" style={{display:'flex',width:'100%',alignItems:'center',justifyContent:'space-between'}}>
    <Link href="/" className="brand"><span className="brand-mark brand-mark-image"><img src={overlay||scrolled?'/images/guard-white.png':'/images/guard-violet.png'} alt=""/></span><span>Guard</span></Link>
    <button type="button" className="mobile-nav-toggle" aria-label={menuOpen?'Close navigation':'Open navigation'} aria-expanded={menuOpen} aria-controls="primary-navigation" onClick={()=>setMenuOpen(open=>!open)}>{menuOpen?<X size={21}/>:<Menu size={21}/>}</button>
    <nav id="primary-navigation" className={'nav '+(!overlay?'nav-light':'')+(menuOpen?' nav-open':'')}><Link href="/" onClick={()=>setMenuOpen(false)}>Home</Link><Link href="/detect" onClick={()=>setMenuOpen(false)}>Check Fraud</Link><Link href="/community" onClick={()=>setMenuOpen(false)}>Community</Link><Link href="/business" onClick={()=>setMenuOpen(false)}>Business</Link><Link href="/login" className="btn btn-primary" onClick={()=>setMenuOpen(false)}>Login</Link></nav>
  </div></header></>;
}

export function Footer() { return <footer className="footer"><div className="container footer-grid"><div className="footer-intro"><Link href="/" className="brand"><span className="brand-mark brand-mark-image"><img src="/images/guard-violet.png" alt=""/></span><span>Guard</span></Link><p>Helping people and businesses check suspicious payments before money or goods leave their hands.</p><span className="footer-meta">Mobile Money fraud prevention built for Ghana.</span></div><div className="footer-column"><strong>Protect your money</strong><Link href="/detect">Check before you pay</Link><Link href="/learn">Learn fraud patterns</Link><Link href="/report">Report payment fraud</Link></div><div className="footer-column"><strong>Guard</strong><Link href="/business">For businesses</Link><Link href="/pricing">Pricing</Link><Link href="/about">About us</Link></div><div className="footer-column"><strong>Trust</strong><Link href="/faq">FAQ</Link><Link href="/privacy">Privacy Policy</Link><Link href="/terms">Terms &amp; Conditions</Link></div></div><div className="container footer-bottom"><span>© 2026 Guard. All rights reserved.</span><span>Guard supports safer payment decisions — never absolute certainty.</span></div></footer>; }
