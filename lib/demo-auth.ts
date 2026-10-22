/**
 * Demo accounts are convenient in local development, but must never become an
 * implicit production authentication path. An explicit environment value wins;
 * otherwise demo auth defaults on only for the development build.
 */
export const demoAuthEnabled = process.env.NEXT_PUBLIC_ENABLE_DEMO_AUTH !== undefined
  ? process.env.NEXT_PUBLIC_ENABLE_DEMO_AUTH === 'true'
  : process.env.NODE_ENV === 'development';
