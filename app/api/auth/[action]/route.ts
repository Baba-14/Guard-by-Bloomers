import { NextResponse } from 'next/server';
import { backendEndpoint } from '@/lib/backend-service';

const allowedActions = new Set(['register', 'login', 'me']);

async function proxy(request: Request, action: string) {
  if (!allowedActions.has(action)) {
    return NextResponse.json({ detail: 'Not found' }, { status: 404 });
  }

  const headers = new Headers();
  const contentType = request.headers.get('content-type');
  const authorization = request.headers.get('authorization');
  if (contentType) headers.set('content-type', contentType);
  if (authorization) headers.set('authorization', authorization);

  const response = await fetch(backendEndpoint(`v1/auth/${action}`), {
    method: request.method,
    headers,
    body: request.method === 'GET' ? undefined : await request.arrayBuffer(),
    cache: 'no-store',
  });

  return new NextResponse(response.body, {
    status: response.status,
    headers: { 'content-type': response.headers.get('content-type') ?? 'application/json' },
  });
}

export async function GET(request: Request, context: { params: { action: string } }) {
  return proxy(request, context.params.action);
}

export async function POST(request: Request, context: { params: { action: string } }) {
  return proxy(request, context.params.action);
}
