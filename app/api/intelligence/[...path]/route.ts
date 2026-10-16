import { NextResponse } from 'next/server';
import { backendEndpoint } from '@/lib/backend-service';
import { backendAuthorization } from '@/lib/server-auth';

async function proxy(request: Request, path: string[]) {
  const headers = new Headers();
  const authorization = backendAuthorization(request);
  const contentType = request.headers.get('content-type');
  if (authorization) headers.set('authorization', authorization);
  if (contentType) headers.set('content-type', contentType);
  const url = backendEndpoint(`v1/intelligence/${path.join('/')}`);
  url.search = new URL(request.url).search;
  const response = await fetch(url, { method: request.method, headers, body: request.method === 'GET' ? undefined : await request.arrayBuffer(), cache: 'no-store' });
  return new NextResponse(response.body, { status: response.status, headers: { 'content-type': response.headers.get('content-type') ?? 'application/json' } });
}

type Context = { params: Promise<{ path: string[] }> };
export async function GET(request: Request, { params }: Context) { return proxy(request, (await params).path); }
export async function POST(request: Request, { params }: Context) { return proxy(request, (await params).path); }
export async function PATCH(request: Request, { params }: Context) { return proxy(request, (await params).path); }
