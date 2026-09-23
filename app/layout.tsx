import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Guard — Stop fraud before it happens',
  description: 'Ghana-first fraud prevention and intelligence for everyday digital interactions.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
