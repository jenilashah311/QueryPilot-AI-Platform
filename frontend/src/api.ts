const base = "";

export async function api<T>(
  path: string,
  opts: RequestInit & { token?: string | null } = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  };
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`;
  const { token, ...rest } = opts;
  const r = await fetch(`${base}${path}`, { ...rest, headers });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || r.statusText);
  }
  return r.json() as Promise<T>;
}
