import { NextResponse } from 'next/server';
import { backendEndpoint } from '@/lib/backend-service';

export async function POST(request: Request) {
  const authorization = request.headers.get('authorization');
  if (!authorization) {
    return NextResponse.json({ detail: 'A valid Guard API key is required' }, { status: 401 });
  }

  const headers = new Headers({
    authorization,
    'content-type': request.headers.get('content-type') || 'application/json',
  });
  const idempotencyKey = request.headers.get('idempotency-key');
  if (idempotencyKey) headers.set('idempotency-key', idempotencyKey);

  let response: Response;
  try {
    response = await fetch(backendEndpoint('v1/checks'), {
      method: 'POST',
      headers,
      body: await request.text(),
      cache: 'no-store',
      signal: AbortSignal.timeout(15_000),
    });
  } catch {
    return NextResponse.json({ detail: 'Guard API is temporarily unavailable.' }, { status: 503 });
  }

  const outgoingHeaders = new Headers({
    'content-type': response.headers.get('content-type') || 'application/json',
  });
  for (const name of ['x-guard-request-id', 'x-guard-ratelimit-limit', 'x-guard-ratelimit-remaining', 'idempotent-replayed', 'retry-after']) {
    const value = response.headers.get(name);
    if (value) outgoingHeaders.set(name, value);
  }
  return new NextResponse(response.body, { status: response.status, headers: outgoingHeaders });
}
