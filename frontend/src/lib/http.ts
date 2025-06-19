// Lightweight wrapper emulating minimal axios API using Fetch
// Provides axios-like get/post returning parsed JSON and throwing on HTTP error.
// Credentials (cookies) are included by default to allow auth.

export interface HttpResponse<T> {
  data: T;
}

async function request<T>(url: string, init: RequestInit): Promise<HttpResponse<T>> {
  const resp = await fetch(url, init);
  if (!resp.ok) {
    // Try to parse error JSON otherwise throw status text
    let detail: any = undefined;
    try {
      detail = await resp.json();
    } catch {
      /* ignore */
    }
    throw {
      response: {
        status: resp.status,
        data: detail ?? resp.statusText,
      },
    };
  }
  const data = (await resp.json()) as T;
  return { data };
}

export const http = {
  get<T = any>(url: string, init: RequestInit = {}) {
    return request<T>(url, {
      ...init,
      method: 'GET',
      credentials: init.credentials ?? 'include',
    });
  },
  post<T = any>(url: string, body?: any, init: RequestInit = {}) {
    const headers = { 'Content-Type': 'application/json', ...(init.headers || {}) } as Record<string, string>;
    return request<T>(url, {
      ...init,
      method: 'POST',
      headers,
      body: JSON.stringify(body ?? {}),
      credentials: init.credentials ?? 'include',
    });
  },
};

// Default export to allow `import axios from '@/lib/http'` if desired
export default http;
