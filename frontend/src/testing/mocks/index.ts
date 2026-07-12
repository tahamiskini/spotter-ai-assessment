import { env } from '@/config/env';

/**
 * Start the in-browser MSW worker when API mocking is enabled
 * (VITE_APP_ENABLE_API_MOCKING=true). Lets the frontend run fully
 * standalone against sample trip data, no backend required.
 */
export const enableMocking = async () => {
  if (!env.ENABLE_API_MOCKING) return;
  const { worker } = await import('./browser');
  return worker.start({ onUnhandledRequest: 'bypass' });
};
