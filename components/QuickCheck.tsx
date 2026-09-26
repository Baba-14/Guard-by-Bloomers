'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowRight, ShieldAlert } from 'lucide-react';
import { AnalysisScanner, type Kind } from './Checker';

export function QuickCheck() {
  const router = useRouter();
  const [value, setValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ level: string; reason: string } | null>(null);
  const [placeholder, setPlaceholder] = useState('');
  const normalizedValue = value.trim();
  const currentKind: Kind = /^(\+?233|0)\d{8,}/.test(normalizedValue.replace(/[\s-]/g, '')) ? 'number' : /^(https?:\/\/|www\.)/i.test(normalizedValue) ? 'link' : 'payment';
  useEffect(() => {
    if (value) return;
    const phrases = ['Describe a Mobile Money request', 'Enter the recipient number', 'Paste the payment message', 'Paste a suspicious link'];
    let phraseIndex = 0;
    let characterIndex = 0;
    let deleting = false;
    let timer: ReturnType<typeof setTimeout>;
    const type = () => {
      const phrase = phrases[phraseIndex];
      characterIndex = deleting ? characterIndex - 1 : characterIndex + 1;
      setPlaceholder(phrase.slice(0, characterIndex));
      if (!deleting && characterIndex === phrase.length) {
        deleting = true;
        timer = setTimeout(type, 1500);
        return;
      }
      if (deleting && characterIndex === 0) {
        deleting = false;
        phraseIndex = (phraseIndex + 1) % phrases.length;
      }
      timer = setTimeout(type, deleting ? 42 : 72);
    };
    timer = setTimeout(type, 350);
    return () => clearTimeout(timer);
  }, [value]);
  const check = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim()) return;
    setLoading(true);
    try {
      const kind = currentKind;
      router.push(`/detect/${kind}?input=${encodeURIComponent(value)}&auto=1`);
    } finally { setLoading(false); }
  };
  if (loading) return <div className="quick-check quick-check-analysis"><AnalysisScanner kind={currentKind} compact/></div>;
  return <div className="quick-check"><form onSubmit={check}><div className="quick-input-shell"><div className="quick-input"><input value={value} onChange={e => { setValue(e.target.value); setResult(null); }} placeholder={placeholder || 'Describe the payment request or paste its message'} aria-label="Describe a payment request or enter its phone number, URL, or message"/><button className="btn btn-primary" type="submit">Check before paying <ArrowRight size={15}/></button></div></div></form><p className="quick-legal">Never submit your Mobile Money PIN, password, or OTP. By continuing, you agree to Guard’s Terms and Privacy Policy.</p>{result && <div className="quick-result"><ShieldAlert size={16}/><span><strong>{result.level}</strong> — {result.reason}</span><Link href="/detect">View full check</Link></div>}</div>;
}
