// Dashboard API Route - Usage
import { proxyBackendGet } from '@/lib/backendProxy';

export async function GET() {
  return proxyBackendGet('/dashboard/usage', 'Failed to fetch usage');
}
