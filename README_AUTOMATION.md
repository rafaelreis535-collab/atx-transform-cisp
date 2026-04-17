# Automation Script for AI Cockpit Modernization

This document describes how to use the [`automate_docs.py`](automate_docs.py:1) script to automate the complete documentation generation workflow.

## Overview

The [`automate_docs.py`](automate_docs.py:1) script automates the entire process of:

1. ✅ Checking if a project exists (or creating it)
2. 📦 Uploading project source code as a ZIP file
3. ⏳ Waiting for indexing to complete
4. 🚀 Starting a documentation generation task
5. 🔄 Polling task status until completion
6. 💾 Downloading the generated documentation

## Prerequisites

### Required Environment Variables

Set these environment variables before running the script:

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
pip install mcp requests
```

## Usage

### Basic Usage

```bash
python automate_docs.py \
  --project-name "Banking System Modernization" \
  --zip-file ./banking-example.zip
```

### Full Command with All Options

```bash
python automate_docs.py \
  --project-name "Banking System Modernization" \
  --zip-file ./banking-example.zip \
  --task-name "Documentation Generation - 2024-01-15" \
  --description "COBOL banking system documentation" \
  --output-dir ./results
```

### Skip Upload (for already indexed projects)

If the project is already uploaded and indexed, you can skip the upload step:

```bash
python automate_docs.py \
  --project-name "Banking System Modernization" \
  --zip-file ./banking-example.zip \
  --skip-upload
```

## Command-Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--project-name` | ✅ Yes | Name of the project (will be created if doesn't exist) |
| `--zip-file` | ✅ Yes | Path to the ZIP file containing project sources |
| `--task-name` | ❌ No | Name for the documentation task (default: auto-generated with timestamp) |
| `--description` | ❌ No | Project description (only used when creating new project) |
| `--output-dir` | ❌ No | Directory to save downloaded results (default: `./output`) |
| `--skip-upload` | ❌ No | Skip upload step (use if project is already indexed) |

## Example: Banking Example Project

### Step 1: Create ZIP file

```bash
zip -r banking-example.zip banking-example/
```

### Step 2: Run automation script

```bash
python automate_docs.py \
  --project-name "Banking COBOL System" \
  --zip-file ./banking-example.zip \
  --description "Legacy COBOL banking system for modernization"
```

### Step 3: Check results

The script will:
- Create or find the project
- Upload the ZIP file
- Wait for indexing (typically 1-2 minutes)
- Start documentation generation
- Poll every 30 seconds until complete
- Download results to `./output/` directory

## Script Workflow

```
┌─────────────────────────────────────┐
│ 1. Check/Create Project             │
│    - Search by name                 │
│    - Create if not found            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 2. Upload ZIP File                  │
│    - Get presigned URL              │
│    - Upload to S3                   │
│    - Trigger indexing               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 3. Wait for Indexing                │
│    - Poll project status            │
│    - Wait for READY state           │
│    - Timeout: 10 minutes            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 4. Start Documentation Task         │
│    - Create full-documentation task │
│    - Get task ID                    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 5. Poll Task Status                 │
│    - Check every 30 seconds         │
│    - Display step progress          │
│    - Wait for SUCCESS status        │
│    - Timeout: 60 minutes            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 6. Download Results                 │
│    - Get presigned download URL     │
│    - Download ZIP file              │
│    - Save to output directory       │
└─────────────────────────────────────┘
```

## Output

The script provides detailed logging:

```
[2024-01-15 10:30:00] [INFO] ============================================================
[2024-01-15 10:30:00] [INFO] Starting automation workflow
[2024-01-15 10:30:00] [INFO] API URL: https://aic-modernization-api.compass.uol/
[2024-01-15 10:30:00] [INFO] Organization ID: 686
[2024-01-15 10:30:00] [INFO] Project name: Banking COBOL System
[2024-01-15 10:30:00] [INFO] ============================================================
[2024-01-15 10:30:01] [INFO] Searching for project: Banking COBOL System
[2024-01-15 10:30:02] [INFO] Found project: abc123
[2024-01-15 10:30:02] [INFO] Uploading ZIP file: ./banking-example.zip
[2024-01-15 10:30:05] [INFO] Upload status: indexed
[2024-01-15 10:30:05] [INFO] Waiting for project indexing to complete...
[2024-01-15 10:30:15] [INFO] Project state: INDEXING
[2024-01-15 10:30:25] [INFO] Project state: READY
[2024-01-15 10:30:25] [INFO] Project indexed successfully!
[2024-01-15 10:30:25] [INFO] Starting documentation task: Docs - 2024-01-15 10:30:25
[2024-01-15 10:30:26] [INFO] Task created: task123
[2024-01-15 10:30:26] [INFO] Polling task status: task123
[2024-01-15 10:30:56] [INFO] Task status: STARTED
[2024-01-15 10:30:56] [INFO]   Step 'enrichment': COMPLETED
[2024-01-15 10:30:56] [INFO]   Step 'overview': IN_PROGRESS
...
[2024-01-15 10:45:30] [INFO] Task status: SUCCESS
[2024-01-15 10:45:30] [INFO] Task completed successfully!
[2024-01-15 10:45:30] [INFO] Downloading results for task: task123
[2024-01-15 10:45:35] [INFO] Download completed: ./output/task_task123_results.zip (1,234,567 bytes)
[2024-01-15 10:45:35] [INFO] ============================================================
[2024-01-15 10:45:35] [INFO] Automation workflow completed successfully!
[2024-01-15 10:45:35] [INFO] ============================================================
```

## Error Handling

The script handles various error scenarios:

- **Missing environment variables**: Exits with error code 1
- **ZIP file not found**: Exits with error code 1
- **Project creation failure**: Exits with error code 1
- **Upload failure**: Exits with error code 1
- **Indexing timeout**: Exits with error code 1 (default: 10 minutes)
- **Task creation failure**: Exits with error code 1
- **Task timeout**: Exits with error code 1 (default: 60 minutes)
- **Download failure**: Exits with error code 1

## Timeouts

| Operation | Default Timeout | Configurable |
|-----------|----------------|--------------|
| Indexing | 10 minutes | No |
| Task completion | 60 minutes | No |
| HTTP requests | 60 seconds | No |
| File upload | 5 minutes | No |

## Integration with CI/CD

### Example: AWS CodeBuild

Add to your [`buildspec.yml`](buildspec.yml:1):

```yaml
phases:
  post_build:
    commands:
      - echo "Generating documentation..."
      - python automate_docs.py --project-name "$PROJECT_NAME" --zip-file ./project.zip
      - echo "Documentation generated successfully"
```

### Example: GitHub Actions

```yaml
- name: Generate Documentation
  env:
    MODERNIZATION_API_KEY: ${{ secrets.MODERNIZATION_API_KEY }}
    MODERNIZATION_ORG_ID: ${{ secrets.MODERNIZATION_ORG_ID }}
  run: |
    python automate_docs.py \
      --project-name "My Project" \
      --zip-file ./project.zip \
      --output-dir ./docs
```

## Troubleshooting

### Issue: "MODERNIZATION_API_KEY environment variable not set"

**Solution**: Set the required environment variables:
```bash
export MODERNIZATION_API_KEY="your-key"
export MODERNIZATION_ORG_ID="686"
```

### Issue: "ZIP file not found"

**Solution**: Verify the file path is correct and the file exists:
```bash
ls -lh ./banking-example.zip
```

### Issue: "Timeout waiting for project indexing"

**Solution**: 
- Check project size (large projects take longer)
- Verify API connectivity
- Check API logs for errors

### Issue: "Task failed with status: FAILURE"

**Solution**:
- Check task logs via API
- Verify project was indexed correctly
- Check LLM provider configuration

## Related Files

- [`mcp_client.py`](mcp_client.py:1) - MCP server with API tools
- [`mcp.json`](mcp.json:1) - MCP server configuration
- [`buildspec.yml`](buildspec.yml:1) - AWS CodeBuild configuration

## Support

For issues or questions, contact the AI Cockpit Modernization team.