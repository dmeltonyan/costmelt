/**
 * Cost Melt Dashboard - Server-side backend proxy helper
 *
 * app/api/* route handlers run on the Next.js server, not the browser, so
 * this is the only place it's safe to attach the backend API key: it reads
 * COSTMELT_DASHBOARD_API_KEY (deliberately NOT prefixed with NEXT_PUBLIC_,
 * which Next.js would otherwise inline into client-side bundles). The
 * dashboard's client components call these /api/* routes instead of the
 * backend directly (see lib/api.ts), so the key never reaches the browser.
 */

const BACKEND_URL =
  process.env.BACKEND_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

const BACKEND_API_KEY = process.env.COSTMELT_DASHBOARD_API_KEY;

export async function proxyBackendGet(path: string, errorMessage: string): Promise<Response> {
  const headers: Record<string, string> = {};
  if (BACKEND_API_KEY) {
    headers['Authorization'] = `Bearer ${BACKEND_API_KEY}`;
  }

  try {
    const response = await fetch(`${BACKEND_URL}${path}`, {
      cache: 'no-store',
      headers,
    });

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
