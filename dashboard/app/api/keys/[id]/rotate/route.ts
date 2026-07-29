// Dashboard API Route - Rotate a single API key
import { proxyBackendPost } from '@/lib/backendProxy';

export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  return proxyBackendPost(
    `/auth/api-keys/${encodeURIComponent(params.id)}/rotate`,
    undefined,
    'Failed to rotate API key',
    { admin: true }
  );
}
