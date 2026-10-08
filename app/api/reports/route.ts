import { NextResponse } from 'next/server';
import { backendEndpoint } from '@/lib/backend-service';

export async function POST(request: Request) {
  const response = await fetch(backendEndpoint('v1/contributions'), {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: await request.text(), cache: 'no-store',
  });
  return new NextResponse(response.body, { status: response.status, headers: { 'content-type': response.headers.get('content-type') ?? 'application/json' } });
}
