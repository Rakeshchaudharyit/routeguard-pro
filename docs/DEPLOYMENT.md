# Deployment notes

This repository is an assessment prototype. The following are deployment prerequisites, **not claims that a production deployment has been completed**.

1. Set `DJANGO_DEBUG=false` and export a unique `DJANGO_SECRET_KEY` of at least 50 characters.
2. Set `DJANGO_ALLOWED_HOSTS` to the real API hostnames and `CORS_ALLOWED_ORIGINS` to the exact HTTPS frontend origins.
3. Serve Django with a production WSGI/ASGI server behind TLS; do not use `runserver` for production.
4. Configure reverse-proxy trust, HTTPS redirects, HSTS, logging, monitoring, request limits and error reporting according to the host. Run `python manage.py check --deploy` under actual production settings and address warnings.
5. Set `VITE_API_BASE_URL` to the public HTTPS API **before** `npm run build`; Vite embeds it at build time. Deploy the generated `frontend/dist` as static assets.
6. Review external geocoding, routing and weather provider terms, limits, credentials and reliability; public demo endpoints are not suitable for sustained commercial use.
7. Review database choice and backups if persistent data is added. Current Django configuration uses SQLite.
8. Do not represent the app as commercial truck navigation. A real fleet product requires truck-aware routing, domain-specific validation and a separate safety review.

Sample settings: `backend/.env.example`, `frontend/.env.example`. Django does not automatically load `.env` files; configure environment variables in the deployment process.
