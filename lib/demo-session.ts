export function signOut() {
  sessionStorage.removeItem('guard-demo-auth');
  sessionStorage.removeItem('guard-demo-role');
}
