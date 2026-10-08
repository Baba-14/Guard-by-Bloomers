'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { LayoutDashboard, ShieldCheck, UserRound } from 'lucide-react';
import { Header, Footer } from '@/components/Header';

type DemoRole = 'admin' | 'user';

const accounts = {
  admin: { email:'admin@guard.test', password:'guard123', destination:'/admin' },
  user: { email:'user@guard.test', password:'guard123', destination:'/dashboard' },
} as const;

export default function Login() {
  const router = useRouter();
  const [email,setEmail] = useState('');
  const [password,setPassword] = useState('');
  const [error,setError] = useState('');
  const [loading,setLoading] = useState(false);

  const signIn = (role:DemoRole) => {
    sessionStorage.removeItem('guard-api-token');
    sessionStorage.setItem('guard-demo-auth',role);
    sessionStorage.setItem('guard-demo-role',role);
    router.push(accounts[role].destination);
  };

  const submit = async (event:React.FormEvent) => {
    event.preventDefault();
    const cleanEmail = email.trim().toLowerCase();
    const role = (Object.keys(accounts) as DemoRole[]).find(key=>accounts[key].email===cleanEmail&&accounts[key].password===password);
    if (role) { signIn(role); return; }
    setLoading(true); setError('');
    try {
      const form = new URLSearchParams({ username:cleanEmail, password });
      const response = await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:form});
      const body = await response.json();
      if(!response.ok) throw new Error(body.detail||'Sign in failed.');
      sessionStorage.setItem('guard-api-token',body.access_token);
      sessionStorage.setItem('guard-demo-role',body.user.role);
      router.push(['super_admin','fraud_analyst','support_admin'].includes(body.user.role)?'/admin':'/dashboard');
    } catch(reason) { setError(reason instanceof Error?reason.message:'Sign in failed.'); }
    finally { setLoading(false); }
  };

  const chooseAccount = (role:DemoRole) => {
    setError('');
    setEmail(accounts[role].email);
    setPassword(accounts[role].password);
  };

  return <>
    <Header/>
    <main className="page-shell">
      <div className="container" style={{maxWidth:620}}>
        <div className="page-title">
          <div className="eyebrow">Your Guard</div>
          <h1>Sign in to your workspace.</h1>
          <p>Use the user dashboard for personal checks and reports, or the admin dashboard for Guard operations.</p>
        </div>
        <form className="form-panel" onSubmit={submit}>
          <label className="label" htmlFor="login-email">Email address</label>
          <input id="login-email" className="input" type="email" placeholder="you@example.com" value={email} onChange={event=>{setEmail(event.target.value);setError('')}} required/>
          <label className="label" htmlFor="login-password">Password</label>
          <input id="login-password" className="input" type="password" placeholder="Your password" value={password} onChange={event=>{setPassword(event.target.value);setError('')}} required/>
          {error&&<p role="alert" style={{color:'#b14d46',fontSize:13,lineHeight:1.5,marginTop:14}}>{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={loading} style={{marginTop:22,width:'100%'}}>{loading?'Signing in…':'Sign in'} <ShieldCheck size={16}/></button>

          <div style={{marginTop:24,paddingTop:20,borderTop:'1px solid var(--line)'}}>
            <strong style={{display:'block',fontSize:13,color:'var(--navy)',marginBottom:10}}>Demo accounts</strong>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10}}>
              <button type="button" className="btn btn-outline" style={{borderRadius:10,padding:'13px 12px'}} onClick={()=>chooseAccount('user')}><UserRound size={16}/>User account</button>
              <button type="button" className="btn btn-outline" style={{borderRadius:10,padding:'13px 12px'}} onClick={()=>chooseAccount('admin')}><LayoutDashboard size={16}/>Admin account</button>
            </div>
            <p className="helper" style={{marginTop:12}}>Both demo accounts use the password <strong>guard123</strong>. Select an account, then choose Sign in.</p>
          </div>
          <p className="helper" style={{textAlign:'center',marginTop:20}}>New to Guard? <Link href="/register" className="small-link">Create an account</Link></p>
        </form>
      </div>
    </main>
    <Footer/>
  </>;
}
