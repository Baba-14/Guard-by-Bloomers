import { NextResponse } from 'next/server';
import { backendEndpoint } from '@/lib/backend-service';
import { backendAuthorization } from '@/lib/server-auth';

export async function GET(request: Request) {
  const authorization = backendAuthorization(request);
  if (!authorization) return NextResponse.json({ detail: 'Sign in required' }, { status: 401 });
  const url = backendEndpoint('v1/admin/checks');
  url.search = new URL(request.url).search;
  try {
    const response = await fetch(url, { headers: { authorization }, cache: 'no-store' });
    return new NextResponse(response.body, {
      status: response.status,
      headers: { 'content-type': response.headers.get('content-type') ?? 'application/json' },
    });
  } catch {
    return NextResponse.json({ detail: 'Fraud checks are temporarily unavailable.' }, { status: 503 });
  }
}
