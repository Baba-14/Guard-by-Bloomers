const SESSION_COOKIE = 'guard_session';

export function backendAuthorization(request: Request): string | null {
  const header = request.headers.get('authorization');
  if (header?.startsWith('Bearer ')) return header;
  const cookie = request.headers.get('cookie')
    ?.split(';')
    .map(item => item.trim())
    .find(item => item.startsWith(`${SESSION_COOKIE}=`));
  const token = cookie ? decodeURIComponent(cookie.slice(SESSION_COOKIE.length + 1)) : '';
  return token ? `Bearer ${token}` : null;
}

export { SESSION_COOKIE };
