'use client';

import { FormEvent, useMemo, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, Eye, Flag, Hash, Heart, Home, MessageCircle, Plus, Search, Send, ShieldCheck, TrendingUp, UsersRound } from 'lucide-react';
import { Header } from '@/components/Header';

const channels = [
  ['all','Feed','Everything the community is seeing'],
  ['momo','Mobile Money','Payment and reversal requests'],
  ['whatsapp','WhatsApp takeover','Compromised accounts asking for money'],
  ['links','Suspicious links','Phishing and fake login pages'],
  ['shops','Online shops','Sellers, delivery, and purchase scams'],
  ['verify','Help me verify','Ask the community before acting'],
] as const;

const starterPosts = [
  {id:1,channel:'momo',author:'Kojo N.',initials:'KN',time:'8 min ago',title:'“Wrong transfer” message followed by a phone call',body:'I received a message claiming money had been sent to me by mistake. The caller wanted me to send it to a different number before I checked my actual balance.',tag:'Mobile Money request',replies:18,likes:39,views:711},
  {id:2,channel:'whatsapp',author:'Ama K.',initials:'AK',time:'24 min ago',title:'My cousin’s WhatsApp asked me for emergency money',body:'The writing style felt different and the account refused a voice call. I called the normal phone number and confirmed the WhatsApp account had been taken over before sending anything.',tag:'Account takeover',replies:12,likes:31,views:486},
  {id:3,channel:'links',author:'Guard moderator',initials:'G',time:'1 hr ago',title:'Delivery messages using shortened links are increasing',body:'Several reports describe small delivery fees followed by a fake card or Mobile Money page. Open the courier’s official website yourself instead of using the message link.',tag:'Pattern update',replies:17,likes:46,views:924},
  {id:4,channel:'shops',author:'Esi A.',initials:'EA',time:'2 hrs ago',title:'Instagram seller stopped replying after full payment',body:'The page had many followers but comments were limited. They requested full payment to a personal MoMo number and disappeared after I paid.',tag:'Online shop',replies:15,likes:27,views:608},
] as const;

type CommunityPost = {id:number;channel:string;author:string;initials:string;time:string;title:string;body:string;tag:string;replies:number;likes:number;views:number};

export default function Community() {
  const [activeChannel,setActiveChannel]=useState('all');
  const [draft,setDraft]=useState('');
  const [query,setQuery]=useState('');
  const [posts,setPosts]=useState<CommunityPost[]>([...starterPosts]);
  const active=channels.find(channel=>channel[0]===activeChannel) || channels[0];
  const visiblePosts=useMemo(()=>{
    const channelPosts=activeChannel==='all'?posts:posts.filter(post=>post.channel===activeChannel);
    const term=query.trim().toLowerCase();
    return term?channelPosts.filter(post=>(post.title+' '+post.body+' '+post.tag).toLowerCase().includes(term)):channelPosts;
  },[activeChannel,posts,query]);
  const trending=[...posts].sort((a,b)=>(b.views+b.replies*10)-(a.views+a.replies*10)).slice(0,3);

  const submit=(event:FormEvent)=>{
    event.preventDefault();
    const message=draft.trim();
    if(!message)return;
    setPosts(current=>[{id:Date.now(),channel:activeChannel==='all'?'verify':activeChannel,author:'Community member',initials:'CM',time:'Just now',title:'A new experience shared with the community',body:message,tag:'Community report',replies:0,likes:0,views:1},...current]);
    setDraft('');
  };

  const startTopic=()=>document.getElementById('community-compose-input')?.focus();

  return <><Header/><main className="community-app"><div className="community-app-shell">
    <aside className="community-app-sidebar"><div className="community-app-brand"><img src="/images/guard-white.png" alt=""/><span><strong>Guard</strong><small>Community</small></span></div><label className="community-app-search"><Search size={16}/><input value={query} onChange={event=>setQuery(event.target.value)} placeholder="Search conversations"/></label><nav aria-label="Community navigation"><span className="community-nav-label">Community</span>{channels.map(([id,name,description])=><button key={id} className={activeChannel===id?'active':''} onClick={()=>setActiveChannel(id)}>{id==='all'?<Home size={16}/>:<Hash size={16}/>}<span><strong>{name}</strong><small>{description}</small></span></button>)}<span className="community-nav-label">Actions</span><Link href="/report"><Flag size={16}/><span><strong>Report fraud</strong><small>Submit evidence for formal review</small></span></Link><Link href="/learn"><ShieldCheck size={16}/><span><strong>Fraud guides</strong><small>Learn common warning patterns</small></span></Link></nav></aside>

    <section className="community-app-feed"><header><div><span>{activeChannel==='all'?<Home size={17}/>:<Hash size={17}/>}<strong>{active[1]}</strong></span><small>{active[2]}</small></div><button className="btn btn-primary" onClick={startTopic}><Plus size={15}/> Start new topic</button></header><div className="community-feed-scroll"><section className="community-app-welcome"><div><span className="eyebrow">Community protection against financial loss</span><h1>Share the warning before someone else pays.</h1><p>Discuss Mobile Money fraud, suspicious payment requests and the messages, calls, accounts or links behind them. A community post is a useful signal—not proof that a person or business committed fraud.</p></div><div className="community-welcome-actions"><button className="btn btn-primary" onClick={startTopic}>Share a warning <MessageCircle size={15}/></button><Link href="/report" className="btn btn-outline">Report payment fraud</Link></div></section><div className="community-topic-heading"><span><TrendingUp size={16}/> {activeChannel==='all'?'Payment and fraud warnings':active[1]}</span><b>{visiblePosts.length} topics</b></div><div className="community-topic-list">{visiblePosts.length?visiblePosts.map(post=><article className="community-topic" key={post.id}><div className={'community-avatar '+(post.initials==='G'?'moderator':'')}>{post.initials}</div><div className="community-topic-copy"><div className="community-post-meta"><strong>{post.author}</strong>{post.initials==='G'&&<b>Moderator</b>}<span>{post.time}</span></div><h2>{post.title}</h2><p>{post.body}</p><div className="community-topic-bottom"><span className="community-post-tag">{post.tag}</span><span><Eye size={13}/>{post.views}</span><span><MessageCircle size={13}/>{post.replies}</span><span><Heart size={13}/>{post.likes}</span></div></div></article>):<div className="community-empty"><MessageCircle size={28}/><strong>No conversations found</strong><span>Try another search or start the first topic.</span></div>}</div><form className="community-app-composer" onSubmit={submit}><div className="community-avatar">CM</div><div><textarea id="community-compose-input" aria-label="Start a community topic" placeholder={'Share a warning in '+active[1]+' — never post Mobile Money PINs, passwords, or OTPs.'} value={draft} onChange={event=>setDraft(event.target.value)}/><footer><small>Be factual, respectful, and remove unrelated personal information.</small><button className="btn btn-primary" disabled={!draft.trim()}>Post warning <Send size={14}/></button></footer></div></form></div></section>

    <aside className="community-app-right"><div className="community-right-welcome">💸 Check before your money moves</div><section className="community-right-card"><h2>Trending payment warnings</h2>{trending.map(post=><button key={post.id} onClick={()=>setActiveChannel(post.channel)}><span className="community-avatar">{post.initials}</span><span><strong>{post.title}</strong><small>{post.author} · {post.time}</small><i><Eye size={12}/>{post.views}<MessageCircle size={12}/>{post.replies}</i></span></button>)}</section><button className="community-start-topic" onClick={startTopic}><Plus size={17}/> Share a warning</button><section className="community-right-card community-member-card"><h2>Member statistics</h2><div><span><strong>2,941</strong><small>Community members</small></span><span><strong>{posts.length}</strong><small>Shared experiences</small></span></div><p><UsersRound size={16}/><span><strong>Community member</strong><small>Newest contributor · just now</small></span></p></section><section className="community-right-card community-safety-card"><h2>Community safety</h2><div><ShieldCheck size={18}/><span><strong>Share safely</strong><small>Never post Mobile Money PINs, passwords, OTPs, full card details, or private documents.</small></span></div><div><Flag size={18}/><span><strong>Need formal review?</strong><small>Use the report form when you have a payment route, number, account, link, or evidence.</small></span></div><Link href="/report">Report payment fraud <ArrowRight size={13}/></Link></section></aside>
  </div></main></>;
}
