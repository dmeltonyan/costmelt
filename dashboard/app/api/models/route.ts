// Dashboard API Route - Model Comparison
import { proxyBackendGet } from '@/lib/backendProxy';

export async function GET() {
  return proxyBackendGet('/dashboard/models', 'Failed to fetch model comparison');
}
