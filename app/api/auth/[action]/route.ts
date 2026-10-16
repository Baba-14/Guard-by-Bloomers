import { NextResponse } from 'next/server';
import { backendEndpoint } from '@/lib/backend-service';
import { backendAuthorization, SESSION_COOKIE } from '@/lib/server-auth';

const allowedActions = new Set(['register', 'login', 'me', 'logout']);

async function proxy(request: Request, action: string) {
  if (!allowedActions.has(action)) {
    return NextResponse.json({ detail: 'Not found' }, { status: 404 });
  }
  if (action === 'logout') {
    const result = NextResponse.json({ ok: true });
    result.cookies.set(SESSION_COOKIE, '', { httpOnly:true, sameSite:'lax', secure:process.env.NODE_ENV==='production', path:'/', maxAge:0 });
    return result;
  }

  const headers = new Headers();
  const contentType = request.headers.get('content-type');
  const authorization = backendAuthorization(request);
  if (contentType) headers.set('content-type', contentType);
  if (authorization) headers.set('authorization', authorization);

  const response = await fetch(backendEndpoint(`v1/auth/${action}`), {
    method: request.method,
    headers,
    body: request.method === 'GET' ? undefined : await request.arrayBuffer(),
    cache: 'no-store',
  });

  if (action === 'login') {
    const body = await response.json();
    const { access_token: accessToken, ...safeBody } = body;
    const result = NextResponse.json(safeBody, { status:response.status });
    if (response.ok && accessToken) {
      result.cookies.set(SESSION_COOKIE, accessToken, {
        httpOnly:true, sameSite:'lax', secure:process.env.NODE_ENV==='production',
        path:'/', maxAge:body.expires_in,
      });
    }
    return result;
  }
  return new NextResponse(response.body, {
    status: response.status,
    headers: { 'content-type': response.headers.get('content-type') ?? 'application/json' },
  });
}

type Context = { params: Promise<{ action: string }> };

export async function GET(request: Request, context: Context) {
  return proxy(request, (await context.params).action);
}

export async function POST(request: Request, context: Context) {
  return proxy(request, (await context.params).action);
}
