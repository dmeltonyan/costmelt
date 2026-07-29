/**
 * Cost Melt Dashboard - Server-side backend proxy helper
 *
 * app/api/* route handlers run on the Next.js server, not the browser, so
 * this is the only place it's safe to attach a backend API key: it reads
 * COSTMELT_DASHBOARD_API_KEY (deliberately NOT prefixed with NEXT_PUBLIC_,
 * which Next.js would otherwise inline into client-side bundles). The
 * dashboard's client components call these /api/* routes instead of the
 * backend directly (see lib/api.ts), so the key never reaches the browser.
 *
 * Two separate backend keys are supported on purpose:
 * - COSTMELT_DASHBOARD_API_KEY: a "read"-role key, used for every /dashboard/*
 *   metrics route. This is the key documented in .env.local.example as
 *   sufficient for the whole app.
 * - COSTMELT_ADMIN_API_KEY: an "admin"-role key, used ONLY for the
 *   /auth/api-keys* routes (creating/listing/revoking/rotating API keys).
 *   Those backend endpoints require admin per backend/security/rbac.py, and
 *   minting/revoking keys is meaningfully more sensitive than viewing
 *   metrics, so it gets its own credential instead of upgrading the main
 *   dashboard key to admin. If it's unset, key-management calls fail with a
 *   clear "not configured" error rather than silently reusing a lower-role
 *   key (which would just 403 anyway).
 */

const BACKEND_URL =
  process.env.BACKEND_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

const BACKEND_API_KEY = process.env.COSTMELT_DASHBOARD_API_KEY;
const ADMIN_API_KEY = process.env.COSTMELT_ADMIN_API_KEY;

interface ProxyOptions {
  method?: 'GET' | 'POST' | 'DELETE';
  body?: unknown;
  apiKey?: string;
  emptyResponseStatus?: number;
}

async function proxyBackend(
  path: string,
  errorMessage: string,
  options: ProxyOptions = {}
): Promise<Response> {
  const { method = 'GET', body, apiKey = BACKEND_API_KEY } = options;

  if (!apiKey) {
    return Response.json(
      { error: `${errorMessage}: backend API key not configured` },
      { status: 503 }
    );
  }

  const headers: Record<string, string> = {
    Authorization: `Bearer ${apiKey}`,
  };
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(`${BACKEND_URL}${path}`, {
      method,
      cache: 'no-store',
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    // 204 No Content has no body to parse.
    if (response.status === 204) {
      return new Response(null, { status: 204 });
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      console.error(`${errorMessage}: backend returned ${response.status}`, data);
      return Response.json(
        data ?? { error: errorMessage },
        { status: response.status }
      );
    }

    return Response.json(data);
  } catch (error) {
    console.error(errorMessage, error);
    // 502: the backend itself is unreachable, distinct from a 4xx/5xx it returned.
    return Response.json({ error: errorMessage }, { status: 502 });
  }
}

export async function proxyBackendGet(
  path: string,
  errorMessage: string,
  options: { admin?: boolean } = {}
): Promise<Response> {
  return proxyBackend(path, errorMessage, {
    method: 'GET',
    apiKey: options.admin ? ADMIN_API_KEY : BACKEND_API_KEY,
  });
}

export async function proxyBackendPost(
  path: string,
  body: unknown,
  errorMessage: string,
  options: { admin?: boolean } = {}
): Promise<Response> {
  return proxyBackend(path, errorMessage, {
    method: 'POST',
    body,
    apiKey: options.admin ? ADMIN_API_KEY : BACKEND_API_KEY,
  });
}

export async function proxyBackendDelete(
  path: string,
  errorMessage: string,
  options: { admin?: boolean } = {}
): Promise<Response> {
  return proxyBackend(path, errorMessage, {
    method: 'DELETE',
    apiKey: options.admin ? ADMIN_API_KEY : BACKEND_API_KEY,
  });
}
