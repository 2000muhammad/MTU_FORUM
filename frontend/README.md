# MTU FORUM frontend

Это единственный пользовательский интерфейс проекта. Он работает отдельным процессом Next.js на `/app` и обращается к Django только через `/api`, `/media` и `/static`.

```powershell
npm ci
npm run dev
```

Рабочая сборка:

```powershell
npm run build
npm start
```

Backend по умолчанию: `http://127.0.0.1:8000`. Для другого адреса задайте `DJANGO_BACKEND_URL` перед запуском или сборкой.
