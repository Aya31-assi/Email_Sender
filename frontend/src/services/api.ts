const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

type RequestOptions = RequestInit & { body?: BodyInit | null };

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { ...options, credentials: 'include', headers: { 'Content-Type': 'application/json', ...options.headers } });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? 'Something went wrong. Please try again.');
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

export const api = {
  me: () => request<{ email: string }>('/api/auth/me'),
  login: (email: string, password: string) => request<{ email: string }>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  logout: () => request<void>('/api/auth/logout', { method: 'POST' }),
  sendEmail: (payload: object) => request<{ message: string }>('/api/emails/send', { method: 'POST', body: JSON.stringify(payload) }),
};
