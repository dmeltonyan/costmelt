// Dashboard API Route - Revoke a single API key
import { proxyBackendDelete } from '@/lib/backendProxy';

export async function DELETE(
  request: Request,
  { params }: { params: { id: string } }
) {
  return proxyBackendDelete(
    `/auth/api-keys/${encodeURIComponent(params.id)}`,
    'Failed to revoke API key',
    { admin: true }
  );
}
