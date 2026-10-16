'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ShieldCheck } from 'lucide-react';
import { Header, Footer } from '@/components/Header';
import { responseJson } from '@/lib/client-api';

export default function Register() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setLoading(true); setError('');
    try {
      const response = await fetch('/api/auth/register', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({full_name:fullName,email,password}) });
      await responseJson(response);
      const form = new URLSearchParams({username:email.trim().toLowerCase(),password});
      const loginResponse = await fetch('/api/auth/login', {method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:form});
      await responseJson<{user:{role:string}}>(loginResponse);
      router.push('/dashboard');
    } catch(reason) { setError(reason instanceof Error?reason.message:'Your account could not be created.'); }
    finally { setLoading(false); }
  };

  return <><Header/><main className="page-shell"><div className="container" style={{maxWidth:560}}><div className="page-title"><div className="eyebrow">Create your Guard</div><h1>Keep your decisions in one place.</h1><p>An account lets you save analysis history and return to previous results.</p></div><form className="form-panel" onSubmit={submit}><label className="label" htmlFor="register-name">Name</label><input id="register-name" className="input" placeholder="Your name" minLength={2} maxLength={120} value={fullName} onChange={event=>setFullName(event.target.value)} required/><label className="label" htmlFor="register-email">Email address</label><input id="register-email" className="input" type="email" placeholder="you@example.com" value={email} onChange={event=>setEmail(event.target.value)} required/><label className="label" htmlFor="register-password">Password</label><input id="register-password" className="input" type="password" placeholder="At least 8 characters" minLength={8} maxLength={128} value={password} onChange={event=>setPassword(event.target.value)} required/>{error&&<p role="alert" style={{color:'#b14d46',fontSize:13,marginTop:14}}>{error}</p>}<button className="btn btn-primary" disabled={loading} style={{marginTop:22,width:'100%'}}>{loading?'Creating account…':'Create account'} <ShieldCheck size={16}/></button><p className="helper" style={{textAlign:'center',marginTop:18}}>Already registered? <Link href="/login" className="small-link">Sign in</Link></p></form></div></main><Footer/></>;
}
