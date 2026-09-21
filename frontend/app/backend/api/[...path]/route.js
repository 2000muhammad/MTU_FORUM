const djangoBackend = process.env.DJANGO_BACKEND_URL || "http://127.0.0.1:8000";

async function proxy(request, context) {
  const { path } = await context.params;
  const incoming = new URL(request.url);
  const target = new URL(`/api/${path.join("/")}/`, djangoBackend);
  target.search = incoming.search;
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");
  const method = request.method.toUpperCase();
  const upstream = await fetch(target, {
    method,
    headers,
    body: method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer(),
    redirect: "manual",
  });
  return new Response(upstream.body, {
    status: upstream.status,
    headers: upstream.headers,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
