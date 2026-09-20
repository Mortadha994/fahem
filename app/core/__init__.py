"""Settings, database session, ORM models, live settings, rate limiting.

The bottom of the stack: nothing here imports another app package, so it can
be imported from anywhere - including alembic/env.py, which needs the models
and the database URL without starting the application.
"""
