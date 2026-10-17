const BASE = "/api";

async function request(path, options = {}) {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* non-JSON error body */
    }
    throw new Error(`${resp.status}: ${detail}`);
  }
  return resp.status === 204 ? null : resp.json();
}

export const api = {
  listItems: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    return request(`/items${qs ? `?${qs}` : ""}`);
  },
  stats: () => request("/items/stats"),
  categories: () => request("/categories"),
  health: () => request("/health"),
  createItem: (item) => request("/items", { method: "POST", body: JSON.stringify(item) }),
  updateItem: (id, patch) => request(`/items/${id}`, { method: "PUT", body: JSON.stringify(patch) }),
  deleteItem: (id) => request(`/items/${id}`, { method: "DELETE" }),
};
