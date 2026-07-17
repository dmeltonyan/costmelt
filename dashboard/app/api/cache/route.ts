// Dashboard API Route - Cache Stats
import { proxyBackendGet } from '@/lib/backendProxy';

export async function GET() {
  return proxyBackendGet('/dashboard/cache', 'Failed to fetch cache stats');
}
