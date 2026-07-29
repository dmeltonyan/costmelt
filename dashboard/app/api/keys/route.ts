// Dashboard API Route - API key management (list, create)
// Uses COSTMELT_ADMIN_API_KEY, not the regular dashboard key - see
// lib/backendProxy.ts for why key management gets its own credential.
import { proxyBackendGet, proxyBackendPost } from '@/lib/backendProxy';

export async function GET() {
  return proxyBackendGet('/auth/api-keys', 'Failed to fetch API keys', { admin: true });
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  return proxyBackendPost('/auth/api-keys', body, 'Failed to create API key', { admin: true });
}
