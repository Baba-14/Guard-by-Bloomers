export default function Loading() {
  return <main className="page-shell"><div className="container" style={{minHeight:'55vh',display:'grid',placeItems:'center'}}><div style={{textAlign:'center'}}><img src="/images/guard-violet.png" alt="Guard" style={{width:48,height:48,objectFit:'contain',margin:'0 auto 16px',animation:'pulse 1.3s ease-in-out infinite'}}/><p style={{color:'var(--muted)',fontSize:14}}>Loading Guard…</p></div></div></main>;
}
