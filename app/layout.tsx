import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Guard — Check before your money moves',
  description: 'Ghana-first Mobile Money and payment fraud prevention that helps people and businesses avoid financial loss.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
