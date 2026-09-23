export default function Loading() {
  return <main className="page-shell"><div className="container" style={{minHeight:'55vh',display:'grid',placeItems:'center'}}><div style={{textAlign:'center'}}><div className="icon-box" style={{margin:'0 auto 16px',animation:'pulse 1.3s ease-in-out infinite'}}><span style={{fontWeight:800}}>G</span></div><p style={{color:'var(--muted)',fontSize:14}}>Loading Guard…</p></div></div></main>;
}
