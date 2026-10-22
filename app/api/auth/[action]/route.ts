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

  let response: Response;
  try {
    response = await fetch(backendEndpoint(`v1/auth/${action}`), {
      method: request.method,
      headers,
      body: request.method === 'GET' ? undefined : await request.arrayBuffer(),
      cache: 'no-store',
      signal: AbortSignal.timeout(10000),
    });
  } catch {
    return NextResponse.json(
      { detail: 'The authentication service is temporarily unavailable. Please try again.' },
      { status: 503 },
    );
  }

  const responseText = await response.text();
  let body: Record<string, unknown>;
  try {
    body = responseText ? JSON.parse(responseText) : {};
  } catch {
    body = {};
  }

  if (!responseText || Object.keys(body).length === 0) {
    return NextResponse.json(
      { detail: 'The authentication service returned an unexpected response. Please try again.' },
      { status: response.ok ? 502 : response.status >= 500 ? 502 : response.status },
    );
  }

  if (action === 'login') {
    const { access_token: accessToken, ...safeBody } = body;
    const result = NextResponse.json(safeBody, { status:response.status });
    if (response.ok && typeof accessToken === 'string') {
      result.cookies.set(SESSION_COOKIE, accessToken, {
        httpOnly:true, sameSite:'lax', secure:process.env.NODE_ENV==='production',
        path:'/', maxAge:typeof body.expires_in === 'number' ? body.expires_in : undefined,
      });
    }
    return result;
  }
  return NextResponse.json(body, { status:response.status });
}

type Context = { params: Promise<{ action: string }> };

export async function GET(request: Request, context: Context) {
  return proxy(request, (await context.params).action);
}

export async function POST(request: Request, context: Context) {
  return proxy(request, (await context.params).action);
}
