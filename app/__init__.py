"""Fahem's backend.

The modules used to sit flat at the repository root, where `import auth` and
`import models` worked because everything was one directory. They are grouped
now, by what a module depends on rather than by what it is called:

  core      config, the database session, the ORM models, the live settings
            and the rate limiter. Imports nothing else in here.
  auth      who the caller is: sessions, passwords, and the mails that carry
            a confirmation or a reset link.
  llm       everything that reaches Groq - the queue in front of it, the
            streaming call, the prompts, the gatekeeper, usage accounting.
  rag       the curriculum itself: chunking, retrieval, the pinned context,
            the stored chapters.
  grading   what happens to an answer after it exists: the syntax checker,
            the answer verdict, the notation rules, the session memory.
  routes    the HTTP surface; the admin console's routers in routes/admin.

The direction is one-way - core knows nothing about routes - so an import
that needs to go backwards is a design problem showing itself, not a reason
to add a package.
"""
