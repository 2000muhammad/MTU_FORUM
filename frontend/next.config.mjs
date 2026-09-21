const djangoBackend = process.env.DJANGO_BACKEND_URL || "http://127.0.0.1:8000";

const nextConfig = {
  trailingSlash: true,
  basePath: "/app",
  images: { unoptimized: true },
  async rewrites() {
    return {
      beforeFiles: [
        { source: "/media/:path*", destination: `${djangoBackend}/media/:path*`, basePath: false },
        { source: "/static/:path*", destination: `${djangoBackend}/static/:path*`, basePath: false },
      ],
      afterFiles: [],
      fallback: [],
    };
  },
};

export default nextConfig;
