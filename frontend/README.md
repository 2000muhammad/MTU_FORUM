# MTU FORUM React + Next.js frontend

The new platform is exported by Next.js and served by Django at `/app/`. It
uses the existing Django session, CSRF protection, permissions, and database.
The localized `/<language>/app/` addresses redirect to the canonical path.

## Development

```powershell
cd frontend
npm install
npm run dev
```

## Production build

```powershell
cd frontend
npm ci
npm run build
```

Next.js creates a static export and the build script copies it to
`static/next/`. Django serves the correct exported page for every `/app/`
route. The legacy Django interface remains available through the version
switch in the header. All authenticated platform sections are routed through
the Next.js workspace. Complex existing forms run in same-origin embedded
work areas so their Django permissions, CSRF handling, uploads, and actions
continue to work during the migration.
