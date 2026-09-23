 'use client';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { ArrowRight, ShieldCheck } from 'lucide-react';

export function Header({ overlay = false }: { overlay?: boolean }) {
  const [hidden, setHidden] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const previousY = useRef(0);
  useEffect(() => {
    const onScroll = () => {
      const currentY = window.scrollY;
      setScrolled(currentY > 24);
      if (currentY > 80 && currentY > previousY.current + 6) setHidden(true);
      else if (currentY < previousY.current - 6 || currentY < 24) setHidden(false);
      previousY.current = currentY;
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  const headerClass = ['site-header', overlay ? 'site-header-overlay' : '', scrolled ? 'site-header-scrolled' : '', hidden ? 'site-header-hidden' : ''].filter(Boolean).join(' ');
  return <><header className={headerClass}><div className="container" style={{display:'flex',width:'100%',alignItems:'center',justifyContent:'space-between'}}>
    <Link href="/" className="brand"><span className="brand-mark"><ShieldCheck size={19}/></span><span>Guard</span></Link>
    <nav className="nav"><Link href="/detect">Detect Fraud</Link><Link href="/business">Business</Link><Link href="/login">Login</Link><Link href="/detect" className="btn btn-primary">Check Fraud <ArrowRight size={15}/></Link></nav>
  </div></header></>;
}

export function Footer() { return <footer className="footer"><div className="container footer-grid"><div className="footer-intro"><Link href="/" className="brand"><span className="brand-mark"><ShieldCheck size={17}/></span><span>Guard</span></Link><p>Helping people pause, understand risk, and make safer digital decisions.</p><span className="footer-meta">Built for Ghana’s everyday digital life.</span></div><div className="footer-column"><strong>Protect</strong><Link href="/detect">Check for fraud</Link><Link href="/learn">Learn about fraud</Link><Link href="/report">Report suspicious activity</Link></div><div className="footer-column"><strong>Guard</strong><Link href="/business">For businesses</Link><Link href="/pricing">Pricing</Link><Link href="/about">About us</Link></div><div className="footer-column"><strong>Trust</strong><Link href="/faq">FAQ</Link><Link href="/privacy">Privacy Policy</Link><Link href="/terms">Terms &amp; Conditions</Link></div></div><div className="container footer-bottom"><span>© 2026 Guard. All rights reserved.</span><span>Guard provides guidance — never absolute certainty.</span></div></footer>; }
