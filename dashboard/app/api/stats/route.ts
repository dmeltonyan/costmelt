// Dashboard API Route - Stats
import { proxyBackendGet } from '@/lib/backendProxy';

export async function GET() {
  return proxyBackendGet('/dashboard/stats', 'Failed to fetch stats');
}
