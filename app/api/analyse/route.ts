import { NextResponse } from 'next/server';
import { backendEndpoint } from '@/lib/backend-service';

type AnalyseKind = 'message' | 'screenshot' | 'link' | 'number' | 'whatsapp' | 'payment' | 'call';

type BackendResponse = {
  level: 'Low Risk' | 'Caution' | 'High Risk' | 'Unable to Determine';
  score: number;
  signals: string[];
  explanation: string;
  recommended_action: string;
  pattern: string;
};

export async function POST(request: Request) {
  const { kind, input = '' } = await request.json() as { kind: AnalyseKind; input?: string };
  const response = await fetch(backendEndpoint('v1/analyse'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kind, content: input }),
    cache: 'no-store',
  });
  const body = await response.json();

  if (!response.ok) {
    return NextResponse.json(body, { status: response.status });
  }

  const result = body as BackendResponse;
  return NextResponse.json({
    level: result.level,
    score: result.score,
    reason: result.explanation,
    signals: result.signals,
    action: result.recommended_action,
    pattern: result.pattern,
  });
}
