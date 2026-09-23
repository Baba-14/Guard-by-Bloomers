'use client';
import { useEffect } from 'react';
import Link from 'next/link';

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => { console.error(error); }, [error]);
  return <main className="page-shell"><div className="container" style={{maxWidth:640,textAlign:'center',paddingTop:100}}><div className="eyebrow">Guard recovery</div><h1>Something interrupted this page.</h1><p style={{color:'var(--muted)',lineHeight:1.6}}>The page did not load correctly. Try again or return to the detection experience.</p><div style={{display:'flex',justifyContent:'center',gap:10,flexWrap:'wrap',marginTop:24}}><button className="btn btn-primary" onClick={() => reset()}>Try again</button><Link href="/detect" className="btn btn-outline">Go to Detect Fraud</Link></div></div></main>;
}
