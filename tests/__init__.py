"""The test suite. Run inside the container, against real Postgres and Redis:

    docker compose exec -T backend python -m tests.test_chat_flow

A package rather than loose files for the same reason as scripts/: `-m` puts
the repository root on sys.path, so `import app...` resolves. Groq, the
classifier and retrieval are faked, so no token is spent."""
