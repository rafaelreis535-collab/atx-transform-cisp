#!/usr/bin/env python3
"""
Buildspec-based automation script for AI Cockpit Modernization API workflow.

This script reads configuration from buildspec.yml and automates:
1. Extract PROJECT_PATH from buildspec.yml
2. Derive project name from PROJECT_PATH
3. Create ZIP file from project directory
4. Create or get project in API
5. Upload and index project
6. Generate documentation
7. Download results

Usage:
    python automate_from_buildspec.py [--buildspec ./buildspec.yml]

Environment variables required:
    MODERNIZATION_API_URL         - API base URL
    MODERNIZATION_API_KEY         - API authentication key
    MODERNIZATION_ORG_ID          - Organization ID
    MODERNIZATION_LLM_PROVIDER    - (optional) LLM provider
    MODERNIZATION_LLM_MODEL       - (optional) LLM model
    MODERNIZATION_OUTPUT_LANGUAGE - (optional) Output language (default: en_US)
"""

import argparse
import json
import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is not installed. Install it with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# Import functions from mcp_client and automate_docs
import mcp_client
from automate_docs import (
    log,
    find_project_by_name,
    create_or_get_project,
    wait_for_indexing,
    poll_task_status,
    download_results
)


def read_buildspec(buildspec_path: str) -> Dict[str, Any]:
    """Read and parse buildspec.yml file.
    
    Args:
        buildspec_path: Path to buildspec.yml file
        
    Returns:
        Parsed buildspec dictionary
    """
    log(f"Reading buildspec from: {buildspec_path}")
    
    if not os.path.isfile(buildspec_path):
        log(f"Buildspec file not found: {buildspec_path}", "ERROR")
        sys.exit(1)
    
    try:
        with open(buildspec_path, 'r') as f:
            buildspec = yaml.safe_load(f)
        log("Buildspec loaded successfully")
        return buildspec
    except yaml.YAMLError as e:
        log(f"Invalid YAML in buildspec: {e}", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"Error reading buildspec: {e}", "ERROR")
        sys.exit(1)


def extract_project_path(buildspec: Dict[str, Any]) -> str:
    """Extract PROJECT_PATH from buildspec environment variables.
    
    Args:
        buildspec: Parsed buildspec dictionary
        
    Returns:
        PROJECT_PATH value
    """
    try:
        env_vars = buildspec.get("env", {}).get("variables", {})
        project_path = env_vars.get("PROJECT_PATH")
        
        if not project_path:
            log("PROJECT_PATH not found in buildspec.yml env.variables", "ERROR")
            sys.exit(1)
        
        log(f"Found PROJECT_PATH: {project_path}")
        return project_path
    except Exception as e:
        log(f"Error extracting PROJECT_PATH: {e}", "ERROR")
        sys.exit(1)


def derive_project_name(project_path: str) -> str:
    """Derive project name from PROJECT_PATH.
    
    Examples:
        ./banking-example -> banking-example
        ./src/my-project -> my-project
        /absolute/path/to/project -> project
        my-app/ -> my-app
    
    Args:
        project_path: PROJECT_PATH from buildspec
        
    Returns:
        Derived project name
    """
    # Remove leading ./ and trailing /
    clean_path = project_path.strip("./")
    
    # Get the last component (basename)
    project_name = os.path.basename(clean_path)
    
    log(f"Derived project name: {project_name}")
    return project_name


def create_zip_from_directory(source_dir: str, output_zip: str) -> bool:
    """Create a ZIP file from a directory.
    
    Args:
        source_dir: Directory to zip
        output_zip: Output ZIP file path
        
    Returns:
        True if successful, False otherwise
    """
    log(f"Creating ZIP file from: {source_dir}")
    
    if not os.path.isdir(source_dir):
        log(f"Source directory not found: {source_dir}", "ERROR")
        return False
    
    try:
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
                    log(f"  Added: {arcname}")
        
        file_size = os.path.getsize(output_zip)
        log(f"ZIP file created: {output_zip} ({file_size:,} bytes)")
        return True
    except Exception as e:
        log(f"Error creating ZIP file: {e}", "ERROR")
        return False


def main() -> int:
    """Main buildspec-based automation workflow."""
    parser = argparse.ArgumentParser(
        description="Automate AI Cockpit Modernization documentation from buildspec.yml"
    )
    parser.add_argument(
        "--buildspec",
        default="./buildspec.yml",
        help="Path to buildspec.yml file (default: ./buildspec.yml)"
    )
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Directory to save downloaded results (default: ./output)"
    )
    parser.add_argument(
        "--skip-zip",
        action="store_true",
        help="Skip ZIP creation (use existing ZIP file)"
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip upload step (use if project is already indexed)"
    )
    
    args = parser.parse_args()
    
    # Validate environment
    if not mcp_client.API_KEY:
        log("MODERNIZATION_API_KEY environment variable not set", "ERROR")
        return 1
    
    if mcp_client.ORG_ID is None:
        log("MODERNIZATION_ORG_ID environment variable not set", "ERROR")
        return 1
    
    log("=" * 60)
    log("Starting buildspec-based automation workflow")
    log(f"API URL: {mcp_client.API_BASE_URL}")
    log(f"Organization ID: {mcp_client.ORG_ID}")
    log("=" * 60)
    
    # Step 1: Read buildspec
    buildspec = read_buildspec(args.buildspec)
    
    # Step 2: Extract PROJECT_PATH
    project_path = extract_project_path(buildspec)
    
    # Step 3: Derive project name
    project_name = derive_project_name(project_path)
    
    # Step 4: Create ZIP file (if not skipped)
    zip_filename = f"{project_name}.zip"
    
    if not args.skip_zip:
        if not create_zip_from_directory(project_path, zip_filename):
            log("Failed to create ZIP file", "ERROR")
            return 1
    else:
        log(f"Skipping ZIP creation, using existing: {zip_filename}")
        if not os.path.isfile(zip_filename):
            log(f"ZIP file not found: {zip_filename}", "ERROR")
            return 1
    
    # Step 5: Create or get project
    log(f"Creating/getting project with name: {project_name}")
    project_id = create_or_get_project(project_name, f"Auto-generated from {project_path}")
    if not project_id:
        log("Failed to create or get project", "ERROR")
        return 1
    
    # Step 6: Upload ZIP file (if not skipped)
    if not args.skip_upload:
        log(f"Uploading ZIP file: {zip_filename}")
        result_json = mcp_client.upload_project_zip(project_id, zip_filename)
        result = json.loads(result_json)
        
        if "error" in result:
            log(f"Upload failed: {result['error']}", "ERROR")
            return 1
        
        log(f"Upload status: {result.get('status')}")
        
        # Step 7: Wait for indexing
        if not wait_for_indexing(project_id):
            log("Indexing failed or timed out", "ERROR")
            return 1
    else:
        log("Skipping upload step as requested")
    
    # Step 8: Start documentation task
    task_name = f"{project_name} - Docs - {time.strftime('%Y-%m-%d %H:%M:%S')}"
    log(f"Starting documentation task: {task_name}")
    
    result_json = mcp_client.generate_docs(project_id, task_name)
    result = json.loads(result_json)
    
    if "error" in result:
        log(f"Failed to start task: {result['error']}", "ERROR")
        return 1
    
    task_id = result.get("id")
    log(f"Task created: {task_id}")
    
    # Step 9: Poll until completion
    if not poll_task_status(task_id):
        log("Task failed or timed out", "ERROR")
        return 1
    
    # Step 10: Download results
    if not download_results(task_id, args.output_dir):
        log("Failed to download results", "ERROR")
        return 1
    
    log("=" * 60)
    log("Buildspec-based automation workflow completed successfully!")
    log(f"Project name used: {project_name}")
    log(f"Derived from: {project_path}")
    log("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())