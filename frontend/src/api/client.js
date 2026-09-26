/**
 * Minimal API client for TechFlow.
 *
 * Session-cookie auth (Django sessions) + JSON. All endpoints are same-origin
 * in development (Vite proxy) and in production (Django serves the build).
 */

function getCookie(name) {
  const m = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return m ? decodeURIComponent(m[1]) : null;
}

async function request(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = {
    ...(options.body != null ? { "Content-Type": "application/json" } : {}),
    ...(options.headers || {}),
  };
  if (method !== "GET" && method !== "HEAD") {
    const csrf = getCookie("csrftoken");
    if (csrf) headers["X-CSRFToken"] = csrf;
  }
  const opts = {
    method,
    credentials: "same-origin",
    headers,
  };
  if (options.body != null) {
    opts.body = JSON.stringify(options.body);
  }
  const res = await fetch(path, opts);
  let data = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) {
    const detail =
      (data &&
        (data.detail || data.non_field_errors || Object.values(data)[0])) ||
      "خطایی رخ داد";
    const err = new Error(typeof detail === "string" ? detail : "خطای نامعتبر");
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  get: (path) => request(path),
  /** Like get(), but normalizes paginated responses ({results:[...]}) to a plain array. */
  list: (path) =>
    request(path).then((d) =>
      Array.isArray(d) ? d : d && Array.isArray(d.results) ? d.results : [],
    ),
  post: (path, body) => request(path, { method: "POST", body: body ?? {} }),
  patch: (path, body) => request(path, { method: "PATCH", body }),
  delete: (path) => request(path, { method: "DELETE" }),
  login: (username, password) =>
    request("/api/auth/login/", {
      method: "POST",
      body: { username, password },
    }),
  register: ({ username, password, full_name, email }) =>
    request("/api/auth/register/", {
      method: "POST",
      body: { username, password, full_name, email },
    }),
  logout: () => request("/api/auth/logout/", { method: "POST" }),
  me: () => request("/api/auth/me/"),
  /** Bootstrap the CSRF cookie (idempotent, safe on every load). */
  csrfToken: () => request("/api/auth/csrf/"),
};
