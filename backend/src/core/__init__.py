"""TutorBox Core Platform Infrastructure.

Provides foundational services shared across all appliance operating modes:
- config: Centralized typed configuration dataclasses & environment loader.
- db: SQLite connection pool, schema migrations, and entity repositories.
- llm: Abstract LLM client protocol, local SLM HTTP client, and mock client.
- math_engine: Deterministic SymPy AST parsing, arithmetic, and equation solving.
- security: PIN hashing, session authentication, and rate limiting.
"""
