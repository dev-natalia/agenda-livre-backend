# Agenda Livre Backend Constitution

## Core Principles

### I. Django Admin as the Management Interface
All creation, editing and deletion of CEUs, courses and activities MUST go through the built-in
Django Admin, protected by Django's native authentication and permissions. Custom admin screens
or a parallel auth system MUST NOT be built. Public read endpoints MUST work without login;
every write operation MUST require an authenticated admin user.
Rationale: Django was chosen mainly for its ready-made admin area (low effort, secure).

### II. Django ORM on PostgreSQL (AWS RDS)
All persistence MUST use the Django ORM with schema changes expressed as Django migrations.
The database is PostgreSQL hosted on AWS RDS. SQLAlchemy MUST NOT be used, because Django Admin
only works with Django ORM models. Credentials and connection settings MUST come from environment
variables and MUST NOT be committed to the repository.
Rationale: the report's SQLite/ORM description is superseded by this decision.

### III. Tested Code, 90% Coverage (NON-NEGOTIABLE)
Unit tests MUST be written with pytest and pytest-django. Total coverage MUST be at least 90%
and MUST be measured with coverage tooling. Every user story and public endpoint MUST have tests
before the feature is considered done. Tests MUST NOT depend on the shared RDS instance
unless a documented, isolated test database is used.

### IV. REST API with Public, Filterable Catalog
The backend MUST expose a REST API through Django REST Framework consumed by the HTML/CSS/
JavaScript frontend. The public API MUST support listing and filtering courses and activities
by neighborhood and date, and MUST return consistent JSON errors with correct HTTP status codes.
Endpoint contracts MUST be documented in the feature spec before implementation.

### V. Accessibility, Security and Simplicity
Data returned to the public MUST support an accessible frontend (WCAG, Lei nº 13.146/2015):
text alternatives and clear, structured fields. Secrets, personal data and admin credentials MUST
NOT be exposed or logged. Implementations MUST follow YAGNI: no features beyond the report's
scope (catalog, search, about, contact, admin login) without a spec.

## Stack & Constraints

- Language and framework: Python 3.14, Django, Django REST Framework.
- Database: PostgreSQL on AWS RDS (see Principle II).
- Execution: local only. The project MUST NOT be deployed to production; no production
  infrastructure, CI/CD deploy steps or production hardening work is in scope.
- Delivery: the source MUST be published on GitHub, and a video demonstrating the working site
  MUST be recorded as part of the academic deliverable.
- Scope: pilot for the UniCEU Navegantes polo; multi-unit expansion is future work.
- Dependencies MUST be pinned in a requirements file so the project runs on a clean machine.

## Development Workflow & Quality Gates

- Work MUST follow the Spec Kit flow: specify → plan → tasks → implement.
- Git MUST be used for version control, with small, descriptive commits.
- Before merging into main, the test suite MUST pass and coverage MUST be at least 90%.
- Code MUST follow PEP 8 and pass the project's configured linter.
- Each team member's change MUST be reviewed by at least one other member via pull request.
- The README MUST document local setup, environment variables and how to run tests.

## Governance

This constitution supersedes other practices in this repository. Amendments MUST be proposed by
pull request, explain the reason, and be approved by at least one other team member. Versioning
follows semantic versioning: MAJOR for removed or redefined principles, MINOR for added or
materially expanded guidance, PATCH for wording clarifications. Every spec, plan and pull request
MUST be checked for compliance with these principles; deviations MUST be justified in writing.
Compliance is reviewed before each academic deliverable.

**Version**: 1.0.0 | **Ratified**: 2026-10-11 | **Last Amended**: 2026-10-11
