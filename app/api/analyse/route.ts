import { NextResponse } from 'next/server';
export async function POST(req:Request){
 const {kind,input=''}=await req.json(); const text=String(input).toLowerCase();
 const checks:[string,string][]=[['otp','OTP requested'],['pin','PIN or secret code requested'],['password','Password requested'],['urgent','Urgency or pressure to act'],['immediately','Urgency or pressure to act'],['click','Link or click-through request'],['pay','Payment request'],['fee','Advance fee or delivery charge'],['guarantee','Guaranteed return or reward'],['suspend','Account-suspension threat'],['remote','Remote-access request']];
 const signals=Array.from(new Set(checks.filter(([term])=>text.includes(term)).map(([,label])=>label)));
 if(kind==='screenshot' && input) signals.push('Image submitted for contextual review');
 if(kind==='number') signals.push('Reputation data is moderated and does not identify a person as a fraudster');
 const suspiciousHostedBrand = kind === 'link' && /vercel\.app|netlify\.app|pages\.dev/.test(text) && /(bank|bnk|gcb|momo|mtn|ecobank|login|verify|secure|account)/.test(text);
 if (suspiciousHostedBrand) signals.push('Brand-like name on a hosted subdomain');
 const score=Math.min(90,signals.length*18+(text.includes('http')?15:0)+(suspiciousHostedBrand?28:0));
 const level=score>=60?'High Risk':score>=30?'Caution':'Unable to Determine';
 const reason=level==='High Risk'?'Strong fraud indicators were detected in the information submitted.':level==='Caution'?'Some suspicious or unverifiable signals were detected.':'Not enough information was available to make a confident assessment.';
 const action=level==='High Risk'?'Do not share OTPs, PINs or more money. Pause contact and verify through an official channel.':level==='Caution'?'Pause before responding. Verify the sender or recipient using a trusted, independent contact method.':'Do not treat this as proof of safety. Gather more context and verify before acting.';
 const pattern = suspiciousHostedBrand ? 'Possible brand impersonation' : kind==='number' ? 'Phone reputation lookup' : kind==='link' ? 'Suspicious link assessment' : 'Contextual fraud assessment';
 return NextResponse.json({level,reason,signals:signals.length?signals:['No deterministic warning signal was found in the submitted content.'],action,pattern});
}
