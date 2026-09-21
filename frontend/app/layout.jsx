import "../src/styles.css";

export const metadata = {
  title: "MTU FORUM — новая платформа",
  description: "Новая версия MTU FORUM на React и Next.js",
  icons: { icon: "/static/img/favicon.svg" },
};

export default function RootLayout({ children }) {
  return (
    <html lang="ru">
      <head>
        <link
          rel="stylesheet"
          href="/static/css/mtu-loader.css?v=20260921-react"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
