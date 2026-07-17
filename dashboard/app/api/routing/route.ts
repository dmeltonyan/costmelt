// Dashboard API Route - Routing Stats
import { proxyBackendGet } from '@/lib/backendProxy';

export async function GET() {
  return proxyBackendGet('/dashboard/routing', 'Failed to fetch routing stats');
}
