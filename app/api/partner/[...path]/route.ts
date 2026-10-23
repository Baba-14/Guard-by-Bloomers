import { NextResponse } from 'next/server';
import { backendEndpoint } from '@/lib/backend-service';
import { backendAuthorization } from '@/lib/server-auth';

type Context = { params: Promise<{ path: string[] }> };

async function proxy(request: Request, { params }: Context) {
  const authorization = backendAuthorization(request);
  if (!authorization) return NextResponse.json({ detail: 'Sign in required' }, { status: 401 });
  const path = (await params).path;
  const headers = new Headers({ authorization });
  const contentType = request.headers.get('content-type');
  if (contentType) headers.set('content-type', contentType);
  try {
    const response = await fetch(backendEndpoint(`v1/partner/${path.join('/')}`), {
      method: request.method,
      headers,
      body: request.method === 'GET' ? undefined : await request.arrayBuffer(),
      cache: 'no-store',
    });
    return new NextResponse(response.body, {
      status: response.status,
      headers: { 'content-type': response.headers.get('content-type') || 'application/json' },
    });
  } catch {
    return NextResponse.json({ detail: 'Partner workspace is temporarily unavailable.' }, { status: 503 });
  }
}

export async function GET(request: Request, context: Context) { return proxy(request, context); }
export async function POST(request: Request, context: Context) { return proxy(request, context); }
export async function PATCH(request: Request, context: Context) { return proxy(request, context); }
export async function DELETE(request: Request, context: Context) { return proxy(request, context); }
