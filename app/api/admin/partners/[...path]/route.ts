import { NextResponse } from 'next/server';
import { backendEndpoint } from '@/lib/backend-service';
import { backendAuthorization } from '@/lib/server-auth';

type Context = { params: Promise<{ path: string[] }> };

export async function POST(request: Request, { params }: Context) {
  const authorization = backendAuthorization(request);
  if (!authorization) return NextResponse.json({ detail: 'Sign in required' }, { status: 401 });
  const path = (await params).path;
  try {
    const response = await fetch(backendEndpoint(`v1/admin/partners/${path.join('/')}`), {
      method: 'POST',
      headers: {
        authorization,
        'content-type': request.headers.get('content-type') || 'application/json',
      },
      body: await request.arrayBuffer(),
      cache: 'no-store',
    });
    return new NextResponse(response.body, {
      status: response.status,
      headers: { 'content-type': response.headers.get('content-type') || 'application/json' },
    });
  } catch {
    return NextResponse.json({ detail: 'Partner key creation is temporarily unavailable.' }, { status: 503 });
  }
}
