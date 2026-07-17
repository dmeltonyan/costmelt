// Dashboard API Route - Savings Over Time
import { proxyBackendGet } from '@/lib/backendProxy';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const days = searchParams.get('days') || '30';

  return proxyBackendGet(`/dashboard/savings?days=${days}`, 'Failed to fetch savings');
}
