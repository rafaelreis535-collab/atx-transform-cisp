# Buildspec-Based Automation for AI Cockpit Modernization

This document describes how to use the [`automate_from_buildspec.py`](automate_from_buildspec.py:1) script to automate documentation generation using configuration from [`buildspec.yml`](buildspec.yml:1).

## Overview

The [`automate_from_buildspec.py`](automate_from_buildspec.py:1) script automatically:

1. 📄 Reads [`buildspec.yml`](buildspec.yml:1) configuration
2. 🔍 Extracts `PROJECT_PATH` from environment variables
3. 🏷️ **Derives project name from `PROJECT_PATH`** (e.g., `./banking-example` → `banking-example`)
4. 📦 Creates ZIP file from the project directory
5. ✅ Creates or finds the project in the API
6. 📤 Uploads and indexes the project
7. 🚀 Generates documentation
8. 💾 Downloads results

## Key Feature: Automatic Project Naming

The script automatically derives the project name from the `PROJECT_PATH` defined in [`buildspec.yml`](buildspec.yml:1):

```yaml
env:
  variables:
    PROJECT_PATH: "./banking-example"
```

This will create a project named **`banking-example`** in the API.

### Project Name Derivation Rules

| PROJECT_PATH | Derived Project Name |
|--------------|---------------------|
| `./banking-example` | `banking-example` |
| `./src/my-project` | `my-project` |
| `/absolute/path/to/project` | `project` |
| `my-app/` | `my-app` |

## Prerequisites

### Required Environment Variables

```bash
export MODERNIZATION_API_URL="https://aic-modernization-api.compass.uol/"
export MODERNIZATION_API_KEY="your-api-key-here"
export MODERNIZATION_ORG_ID="686"
```

### Optional Environment Variables

```bash
export MODERNIZATION_LLM_PROVIDER="anthropic"
export MODERNIZATION_LLM_MODEL="us.anthropic.claude-haiku-4-5-20251001-v1:0"
export MODERNIZATION_OUTPUT_LANGUAGE="en_US"  # or pt_BR, es_ES
```

### Required Python Packages

```bash
pip install mcp requests pyyaml
```

## Usage

### Basic Usage (reads ./buildspec.yml)

```bash
python automate_from_buildspec.py
```

### Specify Custom Buildspec Path

```bash
python automate_from_buildspec.py --buildspec ./custom-buildspec.yml
```

### Skip ZIP Creation (if ZIP already exists)

```bash
python automate_from_buildspec.py --skip-zip
```

### Skip Upload (if project already indexed)

```bash
python automate_from_buildspec.py --skip-upload
```

### Full Command with All Options

```bash
python automate_from_buildspec.py \
  --buildspec ./buildspec.yml \
  --output-dir ./results \
  --skip-zip \
  --skip-upload
```

## Command-Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--buildspec` | ❌ No | `./buildspec.yml` | Path to buildspec.yml file |
| `--output-dir` | ❌ No | `./output` | Directory to save downloaded results |
| `--skip-zip` | ❌ No | `false` | Skip ZIP creation (use existing ZIP) |
| `--skip-upload` | ❌ No | `false` | Skip upload step (project already indexed) |

## Example: Banking Example Project

### Step 1: Ensure buildspec.yml is configured

```yaml
version: 0.2

env:
  variables:
    PROJECT_PATH: "./banking-example"

phases:
  build:
    commands:
      - echo "Running ATX transformation..."
      - atx custom def exec -n VisualAge-COBOL-to-Java-Modernization -p $PROJECT_PATH
```

### Step 2: Run automation script

```bash
python automate_from_buildspec.py
```

The script will:
- Read `PROJECT_PATH: "./banking-example"` from [`buildspec.yml`](buildspec.yml:1)
- Create project named **`banking-example`**
- Create `banking-example.zip` from the directory
- Upload and process the project
- Generate documentation
- Download results to `./output/`

## Script Workflow

```
┌─────────────────────────────────────┐
│ 1. Read buildspec.yml               │
│    - Parse YAML file                │
│    - Extract env.variables          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 2. Extract PROJECT_PATH             │
│    - Get from env.variables         │
│    - Example: "./banking-example"   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 3. Derive Project Name              │
│    - Remove ./ prefix               │
│    - Get basename                   │
│    - Result: "banking-example"      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 4. Create ZIP File                  │
│    - Zip PROJECT_PATH directory     │
│    - Name: {project-name}.zip       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 5. Create/Get Project               │
│    - Use derived project name       │
│    - Search or create in API        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 6. Upload & Index                   │
│    - Upload ZIP file                │
│    - Wait for READY state           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 7. Generate Documentation           │
│    - Start task                     │
│    - Poll until SUCCESS             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 8. Download Results                 │
│    - Get presigned URL              │
│    - Save to output directory       │
└─────────────────────────────────────┘
```

## Output Example

```
[2024-01-15 10:30:00] [INFO] ============================================================
[2024-01-15 10:30:00] [INFO] Starting buildspec-based automation workflow
[2024-01-15 10:30:00] [INFO] API URL: https://aic-modernization-api.compass.uol/
[2024-01-15 10:30:00] [INFO] Organization ID: 686
[2024-01-15 10:30:00] [INFO] ============================================================
[2024-01-15 10:30:01] [INFO] Reading buildspec from: ./buildspec.yml
[2024-01-15 10:30:01] [INFO] Buildspec loaded successfully
[2024-01-15 10:30:01] [INFO] Found PROJECT_PATH: ./banking-example
[2024-01-15 10:30:01] [INFO] Derived project name: banking-example
[2024-01-15 10:30:01] [INFO] Creating ZIP file from: ./banking-example
[2024-01-15 10:30:02] [INFO]   Added: BKACCOUN.cpy
[2024-01-15 10:30:02] [INFO]   Added: BKCONTRL.cpy
[2024-01-15 10:30:02] [INFO]   Added: BKCUSTOM.cpy
[2024-01-15 10:30:02] [INFO]   Added: BKTRANSC.cpy
[2024-01-15 10:30:02] [INFO] ZIP file created: banking-example.zip (12,345 bytes)
[2024-01-15 10:30:02] [INFO] Creating/getting project with name: banking-example
[2024-01-15 10:30:03] [INFO] Searching for project: banking-example
[2024-01-15 10:30:04] [INFO] Found project: abc123
[2024-01-15 10:30:04] [INFO] Uploading ZIP file: banking-example.zip
[2024-01-15 10:30:07] [INFO] Upload status: indexed
[2024-01-15 10:30:07] [INFO] Waiting for project indexing to complete...
[2024-01-15 10:30:17] [INFO] Project state: READY
[2024-01-15 10:30:17] [INFO] Project indexed successfully!
[2024-01-15 10:30:17] [INFO] Starting documentation task: banking-example - Docs - 2024-01-15 10:30:17
[2024-01-15 10:30:18] [INFO] Task created: task123
[2024-01-15 10:30:18] [INFO] Polling task status: task123
...
[2024-01-15 10:45:30] [INFO] Task status: SUCCESS
[2024-01-15 10:45:30] [INFO] Task completed successfully!
[2024-01-15 10:45:35] [INFO] Download completed: ./output/task_task123_results.zip (1,234,567 bytes)
[2024-01-15 10:45:35] [INFO] ============================================================
[2024-01-15 10:45:35] [INFO] Buildspec-based automation workflow completed successfully!
[2024-01-15 10:45:35] [INFO] Project name used: banking-example
[2024-01-15 10:45:35] [INFO] Derived from: ./banking-example
[2024-01-15 10:45:35] [INFO] ============================================================
```

## Integration with CI/CD

### AWS CodeBuild

Update your [`buildspec.yml`](buildspec.yml:1):

```yaml
version: 0.2

env:
  variables:
    PROJECT_PATH: "./banking-example"
  secrets-manager:
    MODERNIZATION_API_KEY: "aic-modernization:api-key"
    MODERNIZATION_ORG_ID: "aic-modernization:org-id"

phases:
  install:
    runtime-versions:
      python: 3.11
    commands:
      - pip install mcp requests pyyaml

  build:
    commands:
      - echo "Running ATX transformation..."
      - atx custom def exec -n VisualAge-COBOL-to-Java-Modernization -p $PROJECT_PATH

  post_build:
    commands:
      - echo "Generating documentation..."
      - python automate_from_buildspec.py
      - echo "Documentation generated successfully"

artifacts:
  files:
    - 'output/**/*'
```

### GitHub Actions

```yaml
name: Generate Documentation

on:
  push:
    branches: [main]

jobs:
  document:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install mcp requests pyyaml
      
      - name: Generate Documentation
        env:
          MODERNIZATION_API_KEY: ${{ secrets.MODERNIZATION_API_KEY }}
          MODERNIZATION_ORG_ID: ${{ secrets.MODERNIZATION_ORG_ID }}
          MODERNIZATION_API_URL: "https://aic-modernization-api.compass.uol/"
        run: python automate_from_buildspec.py
      
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: documentation
          path: output/
```

## Comparison with automate_docs.py

| Feature | [`automate_docs.py`](automate_docs.py:1) | [`automate_from_buildspec.py`](automate_from_buildspec.py:1) |
|---------|--------------------------|--------------------------------|
| Project name | Manual via `--project-name` | **Automatic from `PROJECT_PATH`** |
| ZIP file | Manual path via `--zip-file` | **Auto-created from `PROJECT_PATH`** |
| Configuration | Command-line arguments | **Reads from [`buildspec.yml`](buildspec.yml:1)** |
| Use case | Manual/ad-hoc runs | **CI/CD integration** |

## Error Handling

The script handles various error scenarios:

- **Missing [`buildspec.yml`](buildspec.yml:1)**: Exits with error code 1
- **Invalid YAML**: Exits with error code 1
- **Missing `PROJECT_PATH`**: Exits with error code 1
- **Project directory not found**: Exits with error code 1
- **Missing environment variables**: Exits with error code 1
- **Upload/indexing failures**: Exits with error code 1
- **Task failures**: Exits with error code 1

## Troubleshooting

### Issue: "PROJECT_PATH not found in buildspec.yml"

**Solution**: Ensure your [`buildspec.yml`](buildspec.yml:1) has the correct structure:
```yaml
env:
  variables:
    PROJECT_PATH: "./your-project-directory"
```

### Issue: "Source directory not found"

**Solution**: Verify the `PROJECT_PATH` points to an existing directory:
```bash
ls -la ./banking-example
```

### Issue: "Invalid YAML in buildspec"

**Solution**: Validate your YAML syntax:
```bash
python -c "import yaml; yaml.safe_load(open('buildspec.yml'))"
```

## Related Files

- [`automate_from_buildspec.py`](automate_from_buildspec.py:1) - Main buildspec-based automation script
- [`automate_docs.py`](automate_docs.py:1) - Manual automation script
- [`mcp_client.py`](mcp_client.py:1) - MCP server with API tools
- [`buildspec.yml`](buildspec.yml:1) - AWS CodeBuild configuration
- [`README_AUTOMATION.md`](README_AUTOMATION.md:1) - Manual automation documentation

## Support

For issues or questions, contact the AI Cockpit Modernization team.