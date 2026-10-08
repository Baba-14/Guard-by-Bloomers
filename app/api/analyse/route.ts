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
  confidence: number;
  sources: string[];
  check_id: string | null;
  stored: boolean;
  evidence: Array<{
    key: string;
    label: string;
    source: string;
    confidence: number;
    contribution: number;
    evidence: string;
  }>;
  provider_status: string;
  provider_model: string | null;
};

export async function POST(request: Request) {
  const { kind, input = '' } = await request.json() as { kind: AnalyseKind; input?: string };
  const headers = new Headers({ 'Content-Type': 'application/json' });
  const authorization = request.headers.get('authorization');
  if (authorization) headers.set('authorization', authorization);
  const response = await fetch(backendEndpoint('v1/analyse'), {
    method: 'POST',
    headers,
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
    confidence: result.confidence,
    sources: result.sources,
    checkId: result.check_id,
    stored: result.stored,
    evidence: result.evidence,
    providerStatus: result.provider_status,
    providerModel: result.provider_model,
  });
}
