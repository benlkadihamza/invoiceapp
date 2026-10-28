# Cloudflare migration (work in progress)

This branch is NOT production-ready. Do not deploy it against production Neon until dependencies, database connections, file storage, PDF/Excel generation and authentication are tested.

## Safety changes
- The application no longer runs database creation, schema modifications, or seed data on every import. For a controlled one-off local bootstrap, set RUN_DB_BOOTSTRAP=1, but **never** use this flag against production Neon without review and backup.
- The database write debug endpoint was removed.
- Local upload/report directories are skipped with CLOUDFLARE_WORKER=1; upload routes still need R2 adaptation.

## Remaining blockers
- Verify Python Workers compatibility for psycopg, Flask-SQLAlchemy, Flask-Migrate, Pillow, fpdf2, and openpyxl.
- Adapt all upload/download and generated file paths to R2 or in-memory streams.
- Configure Neon credentials via Cloudflare secrets or Hyperdrive; never commit credentials.
- Audit authentication, session cookies, CSRF, and startup behavior.
- Test every route, PDF and Excel output, and database CRUD in a staging environment.
- Set up Cloudflare GitHub deployments only after tests pass.

The production branch main and existing Neon database have not been modified by this migration.
