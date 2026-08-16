# AGENTS.md

## Purpose

This file defines the working standards for coding agents modifying ChatML.

Treat ChatML as a serious, maintainable software project. Optimize for correctness, clarity, testability, security, and small reviewable changes rather than speed or cleverness.

## Tech Stack & Build
Python 3.11, FastAPI, LangChain, LangGraph

## Available Agent Skills (Router)
*Do not execute these workflows directly from this file. Load the specific skill from the `.agents/skills/` directory on demand:*
- `pydantic_and_fastapi_design`: Use when writing APIs and designing Pydantic models for request/response. Located in `.agents/skills/pydantic_and_fastapi_design/SKILL.md`.
- `design_conformance`: Use when auditing React components and CSS files for compliance with the design tokens in `design.md`. Located in `.agents/skills/design_conformance/SKILL.md`.

## 1. Understand Before Editing

Before changing code:

1. Read the relevant implementation and its callers.
2. Inspect nearby tests.
3. Search the repository for all usages of symbols, environment variables, configuration fields, and dependencies you plan to change.
4. Understand the existing architectural boundaries before introducing new ones.
5. Prefer extending an existing abstraction over creating a parallel system.

Do not infer repository behavior from filenames alone.

## 2. Scope Discipline

Implement only the requested task plus changes strictly necessary to make it correct.

Do not:

- perform unrelated refactors
- rename unrelated modules
- reformat the whole repository
- upgrade unrelated dependencies
- rewrite working components solely according to personal preference
- introduce a new framework without a concrete requirement

If you discover unrelated problems, document them instead of silently expanding scope.

## 3. Architecture

Respect existing separation of concerns.

Current code is organized around layers such as API, services, repositories, models, storage, core infrastructure, and LLM integrations.

General rules:

- API handlers should stay thin.
- Business logic belongs in services.
- Persistence logic belongs in repositories/storage adapters.
- Provider-specific LLM logic belongs in the LLM integration layer.
- Core/domain code should not depend unnecessarily on vendor SDK details.
- Prefer dependency injection over constructing external clients deep inside business logic.
- Keep interfaces narrow and explicit.
- Avoid circular imports and hidden global state.

When introducing orchestration frameworks such as LangGraph in future work, keep orchestration separate from domain services and provider implementations.

## 4. Preserve Contracts

Before modifying a public function, class, schema, endpoint, or interface, identify all callers.

Preserve backward compatibility unless the task explicitly requires a breaking change.

If a contract must change:

- update all call sites
- update tests
- update type annotations
- update documentation where relevant
- clearly state the breaking behavior in the final summary

Do not silently change API response shapes or persisted data formats.

## 5. Python Standards

Write clear, idiomatic Python.

Requirements:

- use type hints for new and modified functions
- use meaningful names
- keep functions focused
- prefer explicit control flow over clever abstractions
- avoid unnecessary inheritance
- avoid mutable global state
- avoid wildcard imports
- remove dead imports introduced by the change
- use `pathlib` for new filesystem code where practical
- use async APIs consistently in async execution paths
- do not block the event loop with heavy synchronous work

Use comments to explain non-obvious reasoning, not to restate the code.

## 6. Async Code

ChatML uses asynchronous application paths.

When working in async code:

- use native async client methods when available
- `await` network and database operations correctly
- do not call blocking model/network operations directly inside the event loop
- avoid unnecessary `asyncio.run()` inside application code
- propagate cancellation where possible
- use bounded retries and explicit timeouts for external services

Never implement an infinite retry loop.

## 7. Error Handling

Errors should be explicit and actionable.

- Catch exceptions only when you can add useful handling or context.
- Preserve the original exception through chaining where useful.
- Reuse project-specific exceptions when they already express the failure mode.
- Do not convert every internal failure into `HTTPException` inside low-level modules unless that is already an intentional project convention.
- Do not swallow exceptions.
- Avoid broad `except Exception` unless it is at a deliberate boundary and the behavior is justified.
- Error messages must not contain secrets.

Retry only errors that are plausibly transient.

## 8. Logging

Use Python logging rather than `print()` in application code.

Logs should include useful operational context such as:

- component
- model/provider where relevant
- retry attempt
- operation or document identifier where safe

Never log:

- API keys
- authorization headers
- complete secret-bearing environment variables
- sensitive raw credentials

Avoid logging entire large documents or prompts unless explicitly required for a controlled debugging mode.

## 9. Configuration and Secrets

Secrets belong in environment variables or an approved secret-management mechanism.

Rules:

- never hard-code credentials
- never commit `.env`
- never commit a real token to examples, tests, fixtures, or documentation
- use descriptive environment variable names
- validate required configuration early
- centralize configuration instead of calling `os.getenv()` throughout unrelated modules where practical
- example environment files must contain placeholders only

When removing a configuration value, search for all usages first.

## 10. External Providers

Wrap third-party APIs behind project-owned abstractions.

Provider SDK objects should not leak across unrelated layers.

For LLM integrations specifically:

```text
Application / Services
        |
        v
 project LLM abstraction
        |
        v
 provider adapter
        |
        v
 external SDK/API
```

This keeps provider changes localized and testable.

Normalize external responses and exceptions before exposing them to the rest of the application where practical.

## 11. Dependencies

Dependencies are part of the architecture.

Before adding one:

- verify it is actually required
- prefer the official/current package for the integration
- avoid overlapping libraries that solve the same problem without justification

Before removing one:

- search the entire repository
- verify tests, scripts, benchmarks, and auxiliary modules do not use it

Do not perform broad version upgrades as part of an unrelated task.

Keep dependency files reproducible and clean.

## 12. Testing

Every behavioral change should have appropriate tests.

At minimum:

- add a regression test for bugs
- add unit tests for new logic
- update tests when an intentional contract changes
- test error paths, not only success paths

For external APIs:

- mock network calls in normal unit tests
- tests must not require paid API access by default
- never put real credentials in tests
- keep integration tests clearly separated from unit tests

Prefer deterministic tests.

Do not make a test pass by weakening a meaningful assertion unless the expected behavior genuinely changed.

## 13. Verification

Before declaring work complete:

1. Run tests related to changed code.
2. Run the full test suite when practical.
3. Run available lint/type checks if configured.
4. Search for stale references after migrations/renames.
5. Check application imports/startup for obvious regressions.
6. Inspect the final diff.

Do not claim tests passed if they were not run.

If verification cannot be run, state exactly what was not verified and why.

## 14. Security

Treat all external input as untrusted.

Consider where relevant:

- path traversal
- unsafe file uploads
- injection into shell commands
- prompt/tool injection
- malformed structured input
- insecure deserialization
- credential exposure
- unrestricted network access
- overly permissive CORS/auth behavior

Never execute user-provided strings as shell commands or code without a deliberate sandbox/security boundary.

Avoid introducing `shell=True`.

## 15. Data and Persistence

Be cautious with MongoDB, Qdrant, filesystem storage, and other persistent state.

- do not silently delete user data
- migrations must preserve existing data unless explicitly specified
- keep IDs and relationships consistent
- validate schemas at boundaries
- make destructive operations explicit
- consider rollback/recovery for non-trivial migrations

Do not alter stored schemas as a side effect of an unrelated task.

## 16. RAG and LLM Behavior

For RAG or LLM changes:

- separate retrieval from generation
- keep prompts/configuration maintainable
- avoid provider-specific assumptions in business logic
- preserve source/document metadata when required
- do not silently truncate important context
- make token/context limits explicit where relevant
- handle model/provider failures predictably
- keep model selection configurable

A model migration should not implicitly change retrieval semantics.

## 17. Performance

Do not optimize blindly.

First identify whether the changed path is latency-, memory-, network-, CPU-, or GPU-sensitive.

Avoid:

- repeatedly constructing expensive clients/models
- loading large models at import time without justification
- unbounded concurrency
- unbounded queues
- repeated database/network calls that can be reused safely

Prefer simple measurable improvements.

## 18. Documentation

Update documentation when a change affects:

- setup
- environment variables
- commands
- architecture
- public APIs
- developer workflow

Documentation must match actual code.

Do not document functionality that has not been implemented.

## 19. Git Hygiene

Keep changes reviewable.

- inspect `git diff` before completion
- do not commit generated caches, local databases, virtual environments, model weights, or secrets
- do not modify unrelated files
- use focused commit messages when committing is part of the task
- never rewrite shared history unless explicitly requested
- do not force-push unless explicitly authorized

Do not discard existing user changes that are unrelated to the task.

## 20. Generated and Large Files

Do not commit:

- `.env`
- virtual environments
- Python cache files
- model checkpoints/weights unless explicitly intended
- temporary uploads
- local database files
- benchmark output generated only for debugging
- IDE-specific local state

Check `.gitignore` when introducing new generated artifacts.

## 21. Definition of Done

A task is complete only when:

- requested behavior is implemented
- architecture remains coherent
- affected callers are updated
- relevant tests exist
- relevant tests pass, or failures are explicitly reported
- obsolete code introduced by the migration is removed where safe
- documentation/configuration is updated where needed
- no secret was added
- final diff contains no unrelated changes

## 22. Final Agent Report

When finishing a coding task, report concisely:

1. What changed.
2. Important design decisions.
3. Tests/checks run and their results.
4. Any remaining risks, limitations, or follow-up work.

Do not claim success beyond what was actually verified.
