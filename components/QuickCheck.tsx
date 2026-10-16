'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight } from 'lucide-react';
import { AnalysisScanner, type Kind } from './Checker';

export function QuickCheck() {
  const router = useRouter();
  const [value, setValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [placeholder, setPlaceholder] = useState('');
  const normalizedValue = value.trim();
  const currentKind: Kind = /^(\+?233|0)\d{8,}/.test(normalizedValue.replace(/[\s-]/g, '')) ? 'number' : /^(https?:\/\/|www\.)/i.test(normalizedValue) ? 'link' : 'payment';
  useEffect(() => {
    if (value) return;
    const phrases = ['Paste a suspicious message', 'Enter a phone number', 'Paste a suspicious link', 'Describe a payment request'];
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
      router.push(`/detect/${kind}?input=${encodeURIComponent(value.trim())}&auto=1`);
    } catch { setLoading(false); }
  };
  if (loading) return <div className="quick-check quick-check-analysis"><AnalysisScanner kind={currentKind} compact/></div>;
  return <div className="quick-check"><form onSubmit={check}><div className="quick-input-shell"><div className="quick-input"><input value={value} onChange={e => setValue(e.target.value)} placeholder={placeholder || 'Paste a message, link, phone number, or describe what happened'} aria-label="Enter a suspicious message, link, phone number, account, or payment request"/><button className="btn btn-primary" type="submit">Check <ArrowRight size={15}/></button></div></div></form><p className="quick-legal">Never submit a PIN, password, OTP, recovery code, or full card details. Guard checks this against its detection rules and reviewed intelligence.</p></div>;
}
