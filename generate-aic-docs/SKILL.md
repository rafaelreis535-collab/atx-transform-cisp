---
name: generate-aic-docs
description: Generate full documentation for legacy codebases (COBOL, VB6, Java, etc.) using the aic-modernization MCP. Produces HTML site, Markdown files, architecture overview, business analysis, user stories, and epics.
allowed-tools: Bash(zip *) Bash(curl *) Bash(mkdir *) Bash(unzip *) Bash(sleep *)
argument-hint: "[path-to-source-dir]"
---

Generate full documentation for a legacy codebase using the `aic-modernization` MCP.

## Prerequisites

- `aic-modernization` MCP server must be connected.
- Source code must be accessible locally.
- `zip` CLI must be available.

## Steps

### 1. Get project name

Extract the project name from the PROJECT_PATH environment variable (defined in buildspec.yml):

```bash
basename "$PROJECT_PATH"
```

This extracts the directory name from PROJECT_PATH (e.g., "banking-example" from "./banking-example").

### 2. Read the codebase

Read `README.md`, main source files, and config files to understand the project structure. Use this to write a meaningful project description in the next step.

### 3. Create a project

Call `create_project` using the project name from step 1:

```json
{
  "name": "<project-PROJECT_PATH>",
  "description": "Brief description of the system and its modules."
}
```

> Name must match `^[\w\s:\/_\-]*$` — no parentheses, dots, or special symbols.

Save the returned `id` — it is required for all subsequent steps.

### 4. Package source as ZIP

```bash
zip -r /tmp/project.zip *.cbl *.md src/ test/ -x "*.dll" -x "*.exe" -x "*.obj"
```

Exclude binaries and compiled artifacts. Include test and documentation files.

### 5. Upload the ZIP

Call `upload_project_zip`:

```json
{
  "project_id": "<project_id>",
  "file_path": "/tmp/project.zip"
}
```

Wait for project state to become `READY`. Verify with `get_project` if needed.

### 6. Trigger documentation generation

Call `generate_docs`:

```json
{
  "project_id": "<project_id>",
  "name": "<descriptive task name>"
}
```

Save the returned task `id`.

Pipeline steps (in order): `enrichment` → `overview` → `business_analysis` → `user_stories` → `epics` → `compile`.

### 7. Poll for completion

Call `get_docs_status` with `{ "task_id": "<task_id>" }` in a loop. Respect the `pollAfterMs` field as sleep interval.

Top-level `status` values:
- `PENDING` — not started
- `STARTED` — running
- `SUCCESS` — done
- `FAILURE` — check `error_message` on the failed step

### 8. Download and extract

Once `SUCCESS`, call `get_docs_results` with `{ "task_id": "<task_id>" }` to get a pre-signed `download_url` (expires in 3600s).

```bash
curl -L "<download_url>" -o /tmp/docs.zip
mkdir -p ./docs
unzip -o /tmp/docs.zip -d ./docs/
```

## Output structure
docs/
├── HTML/ # ignore — for browser use only
└── Markdown/
└── docs/
    ├── index.md
    ├── architecture.md
    ├── PROGRAM/
    ├── CODE/
    ├── DOCUMENT/
    ├── epics/
    └── user_stories/