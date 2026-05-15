export async function requestApi(baseUrl, path, { method = "GET", access, body } = {}) {
  const res = await fetch(`${baseUrl}/${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(access ? { Authorization: `Bearer ${access}` } : {})
    },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!res.ok) throw new Error(await res.text());
  if (res.status === 204) return null;
  return res.json();
}

export async function apiWithRefresh(baseUrl, path, opts, auth, setAuth, storageKey) {
  try {
    return await requestApi(baseUrl, path, { ...opts, access: auth?.access });
  } catch (e) {
    const msg = String(e).toLowerCase();
    if (!auth?.refresh || !(msg.includes("token") || msg.includes("not valid") || msg.includes("expired"))) throw e;
    const refreshed = await requestApi(baseUrl, "auth/token/refresh/", { method: "POST", body: { refresh: auth.refresh } });
    const next = { ...auth, access: refreshed.access };
    localStorage.setItem(storageKey, JSON.stringify(next));
    setAuth(next);
    return requestApi(baseUrl, path, { ...opts, access: next.access });
  }
}
