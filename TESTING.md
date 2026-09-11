# Backend tests

Install the project's dependencies in a virtual environment, then run:

```bash
python manage.py test users shops tournaments --settings=tournament_info.test_settings
```

The explicit test settings use an in-memory SQLite database and in-memory file
storage. They do not use the configured MySQL database or S3 storage. The fast
password hasher and fixed secret key are for tests only; never use these settings
to run the deployed application.

## Coverage

- `users/tests.py`: signup, duplicate/missing fields, password hashing, JWT login,
  inactive users, profile access, shop name and balance charging.
- `shops/tests.py`: owner-scoped creation/update, authentication, role checks,
  one shop per owner and duplicate/missing names.
- `tournaments/tests.py`: multipart creation/editing, poker settings, schedule
  validation, images, list filtering/pagination, owner/player-scoped queries,
  entry/approval/rejection/bust/reentry/addon flows, limits, insufficient funds,
  refund bookkeeping and cancellation.

## Confirmed behavior changes

1. Editing a tournament with `status=CANCELED` returns HTTP 400 with a `status`
   field error. The existing dedicated status endpoint also rejects this value.
   Cancellation and refunds use the dedicated cancel endpoint. Other edit status
   transitions have not been changed.
2. An addon request while the entry has `approval_status=PENDING` returns HTTP 400
   without changing the balance, addon count or buy-in history. This includes
   pending entry/reentry approval. After approval or rejection, the ordinary addon
   status, limit and balance checks apply again.

## Limits

These are regression tests for the covered API flows, not exhaustive verification
of every possible input. SQLite does not reproduce MySQL row locking or its
conditional-constraint behavior. Concurrent requests must be tested against a
separate disposable MySQL database. Real S3 uploads, network failures and browser
integration have not been tested by this suite.

```bash
python manage.py makemigrations --check --dry-run --settings=tournament_info.test_settings
```

This command checks for model/migration drift without creating migration files.
