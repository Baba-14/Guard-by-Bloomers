import { NextResponse } from 'next/server';
import { backendEndpoint } from '@/lib/backend-service';
import { backendAuthorization } from '@/lib/server-auth';

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
  const allowedKinds = new Set<AnalyseKind>(['message','screenshot','link','number','whatsapp','payment','call']);
  let payload: { kind?: AnalyseKind; input?: string };
  try { payload = await request.json(); }
  catch { return NextResponse.json({detail:'Invalid request body'}, {status:400}); }
  const { kind, input = '' } = payload;
  if (!kind || !allowedKinds.has(kind)) return NextResponse.json({detail:'Unsupported check type'}, {status:422});
  if (!input.trim()) return NextResponse.json({detail:'Add something for Guard to check.'}, {status:422});
  if (input.length > 20000) return NextResponse.json({detail:'The submitted text is too long.'}, {status:413});
  const headers = new Headers({ 'Content-Type': 'application/json' });
  const authorization = backendAuthorization(request);
  if (authorization) headers.set('authorization', authorization);
  const forwardedFor = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim();
  if (forwardedFor) headers.set('x-guard-client-ip', forwardedFor);
  let response: Response;
  try {
    response = await fetch(backendEndpoint('v1/analyse'), {
      method: 'POST', headers, body: JSON.stringify({ kind, content: input.trim() }),
      cache: 'no-store', signal:AbortSignal.timeout(15000),
    });
  } catch {
    return NextResponse.json({detail:'Guard analysis is temporarily unavailable. Please try again.'}, {status:503});
  }
  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json') ? await response.json() : {detail:'Guard received an unexpected backend response.'};

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
