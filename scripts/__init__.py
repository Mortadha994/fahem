"""One-off command-line tools, run as `python -m scripts.<name>`: promoting an
admin, seeding a demonstration account, extracting a chapter into chunks.json,
patching those chunks. A package rather than loose files so `-m` puts the
repository root on sys.path and `import app...` resolves; none of them is
imported by the application itself."""
