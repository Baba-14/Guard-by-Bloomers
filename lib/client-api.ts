export function authenticatedHeaders(json = true): Headers {
  const headers = new Headers();
  if (json) headers.set('Content-Type', 'application/json');
  return headers;
}

export async function responseJson<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json')
    ? await response.json()
    : { detail: 'Guard received an unexpected response. Please try again.' };
  if (!response.ok) {
    throw new Error(body?.detail || 'Guard could not complete the request.');
  }
  return body as T;
}
