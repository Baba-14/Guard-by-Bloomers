import { NextResponse } from 'next/server';
import { backendEndpoint } from '@/lib/backend-service';
import { backendAuthorization } from '@/lib/server-auth';

export async function POST(request: Request) {
  const headers = new Headers({ 'Content-Type': 'application/json' });
  const authorization = backendAuthorization(request);
  if (authorization) headers.set('authorization', authorization);
  const forwardedFor = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim();
  if (forwardedFor) headers.set('x-guard-client-ip', forwardedFor);
  const response = await fetch(backendEndpoint('v1/contributions'), {
    method: 'POST', headers,
    body: await request.text(), cache: 'no-store',
  });
  return new NextResponse(response.body, { status: response.status, headers: { 'content-type': response.headers.get('content-type') ?? 'application/json' } });
}
