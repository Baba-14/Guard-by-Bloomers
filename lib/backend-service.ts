const localBackendUrl = 'http://127.0.0.1:8000';

export function backendEndpoint(path: string) {
  const baseUrl = process.env.BACKEND_URL ?? localBackendUrl;
  return new URL(path, baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`);
}
