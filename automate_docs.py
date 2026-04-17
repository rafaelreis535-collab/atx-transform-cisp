#!/usr/bin/env python3
"""
Automation script for AI Cockpit Modernization API workflow.

This script automates the complete documentation generation workflow:
1. Check if project exists (or create it)
2. Upload project ZIP file
3. Wait for indexing to complete
4. Start documentation generation task
5. Poll task status until completion
6. Download results

Usage:
    python automate_docs.py --project-name "My Project" --zip-file ./project.zip

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
from pathlib import Path
from typing import Optional, Dict, Any

# Import functions from mcp_client
import mcp_client


def log(message: str, level: str = "INFO") -> None:
    """Print formatted log message."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def find_project_by_name(project_name: str) -> Optional[Dict[str, Any]]:
    """Search for a project by name in the organization.
    
    Args:
        project_name: Name of the project to find
        
    Returns:
        Project dict if found, None otherwise
    """
    log(f"Searching for project: {project_name}")
    
    offset = 0
    limit = 100
    
    while True:
        result_json = mcp_client.list_projects(limit=limit, offset=offset)
        result = json.loads(result_json)
        
        if "error" in result:
            log(f"Error listing projects: {result['error']}", "ERROR")
            return None
        
        items = result.get("items", [])
        
        # Search for project by name
        for project in items:
            if project.get("name") == project_name:
                log(f"Found project: {project.get('id')}")
                return project
        
        # Check if there are more pages
        if not result.get("has_more", False):
            break
            
        offset += limit
    
    log(f"Project '{project_name}' not found", "WARNING")
    return None


def create_or_get_project(project_name: str, description: Optional[str] = None) -> Optional[str]:
    """Create a new project or get existing one by name.
    
    Args:
        project_name: Name of the project
        description: Optional project description
        
    Returns:
        Project ID if successful, None otherwise
    """
    # First, try to find existing project
    existing_project = find_project_by_name(project_name)
    if existing_project:
        return existing_project.get("id")
    
    # Create new project
    log(f"Creating new project: {project_name}")
    result_json = mcp_client.create_project(name=project_name, description=description)
    result = json.loads(result_json)
    
    if "error" in result:
        log(f"Error creating project: {result['error']}", "ERROR")
        return None
    
    project_id = result.get("id")
    log(f"Project created successfully: {project_id}")
    return project_id


def wait_for_indexing(project_id: str, max_wait_seconds: int = 600) -> bool:
    """Wait for project to be indexed (READY state).
    
    Args:
        project_id: ID of the project
        max_wait_seconds: Maximum time to wait in seconds
        
    Returns:
        True if indexed successfully, False otherwise
    """
    log("Waiting for project indexing to complete...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        result_json = mcp_client.get_project(project_id)
        result = json.loads(result_json)
        
        if "error" in result:
            log(f"Error checking project status: {result['error']}", "ERROR")
            return False
        
        state = result.get("state", "UNKNOWN")
        log(f"Project state: {state}")
        
        if state == "READY":
            log("Project indexed successfully!")
            return True
        elif state in ["FAILED", "ERROR"]:
            log(f"Project indexing failed with state: {state}", "ERROR")
            return False
        
        # Wait before next check
        time.sleep(10)
    
    log("Timeout waiting for project indexing", "ERROR")
    return False


def poll_task_status(task_id: str, max_wait_seconds: int = 3600) -> bool:
    """Poll task status until completion.
    
    Args:
        task_id: ID of the documentation task
        max_wait_seconds: Maximum time to wait in seconds
        
    Returns:
        True if task completed successfully, False otherwise
    """
    log(f"Polling task status: {task_id}")
    start_time = time.time()
    poll_interval = 30  # seconds
    
    while time.time() - start_time < max_wait_seconds:
        result_json = mcp_client.get_docs_status(task_id)
        result = json.loads(result_json)
        
        if "error" in result:
            log(f"Error checking task status: {result['error']}", "ERROR")
            return False
        
        status = result.get("status", "UNKNOWN")
        log(f"Task status: {status}")
        
        # Log step progress
        steps = result.get("steps", [])
        for step in steps:
            step_name = step.get("name", "Unknown")
            step_status = step.get("status", "Unknown")
            log(f"  Step '{step_name}': {step_status}")
        
        if status == "SUCCESS":
            log("Task completed successfully!")
            return True
        elif status in ["FAILURE", "REVOKED"]:
            log(f"Task failed with status: {status}", "ERROR")
            return False
        
        # Wait before next poll
        suggested_wait = result.get("pollAfterMs", poll_interval * 1000) / 1000
        time.sleep(min(suggested_wait, poll_interval))
    
    log("Timeout waiting for task completion", "ERROR")
    return False


def download_results(task_id: str, output_dir: str = "./output") -> bool:
    """Download task results to local directory.
    
    Args:
        task_id: ID of the completed task
        output_dir: Directory to save the downloaded file
        
    Returns:
        True if download successful, False otherwise
    """
    log(f"Downloading results for task: {task_id}")
    
    result_json = mcp_client.get_docs_results(task_id)
    result = json.loads(result_json)
    
    if "error" in result:
        log(f"Error getting download URL: {result['error']}", "ERROR")
        return False
    
    download_url = result.get("download_url")
    filename = result.get("filename", f"task_{task_id}_results.zip")
    
    if not download_url:
        log("No download URL available", "ERROR")
        return False
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    # Download file
    log(f"Downloading to: {output_path}")
    try:
        import requests
        response = requests.get(download_url, timeout=300)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        file_size = len(response.content)
        log(f"Download completed: {output_path} ({file_size:,} bytes)")
        return True
        
    except Exception as e:
        log(f"Download failed: {e}", "ERROR")
        return False


def main() -> int:
    """Main automation workflow."""
    parser = argparse.ArgumentParser(
        description="Automate AI Cockpit Modernization documentation generation"
    )
    parser.add_argument(
        "--project-name",
        required=True,
        help="Name of the project (will be created if doesn't exist)"
    )
    parser.add_argument(
        "--zip-file",
        required=True,
        help="Path to the ZIP file containing project sources"
    )
    parser.add_argument(
        "--task-name",
        help="Name for the documentation task (default: auto-generated)"
    )
    parser.add_argument(
        "--description",
        help="Project description (only used when creating new project)"
    )
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Directory to save downloaded results (default: ./output)"
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
    
    # Validate ZIP file
    if not args.skip_upload and not os.path.isfile(args.zip_file):
        log(f"ZIP file not found: {args.zip_file}", "ERROR")
        return 1
    
    log("=" * 60)
    log("Starting automation workflow")
    log(f"API URL: {mcp_client.API_BASE_URL}")
    log(f"Organization ID: {mcp_client.ORG_ID}")
    log(f"Project name: {args.project_name}")
    log("=" * 60)
    
    # Step 1: Create or get project
    project_id = create_or_get_project(args.project_name, args.description)
    if not project_id:
        log("Failed to create or get project", "ERROR")
        return 1
    
    # Step 2: Upload ZIP file (if not skipped)
    if not args.skip_upload:
        log(f"Uploading ZIP file: {args.zip_file}")
        result_json = mcp_client.upload_project_zip(project_id, args.zip_file)
        result = json.loads(result_json)
        
        if "error" in result:
            log(f"Upload failed: {result['error']}", "ERROR")
            return 1
        
        log(f"Upload status: {result.get('status')}")
        
        # Step 3: Wait for indexing
        if not wait_for_indexing(project_id):
            log("Indexing failed or timed out", "ERROR")
            return 1
    else:
        log("Skipping upload step as requested")
    
    # Step 4: Start documentation task
    task_name = args.task_name or f"Docs - {time.strftime('%Y-%m-%d %H:%M:%S')}"
    log(f"Starting documentation task: {task_name}")
    
    result_json = mcp_client.generate_docs(project_id, task_name)
    result = json.loads(result_json)
    
    if "error" in result:
        log(f"Failed to start task: {result['error']}", "ERROR")
        return 1
    
    task_id = result.get("id")
    log(f"Task created: {task_id}")
    
    # Step 5: Poll until completion
    if not poll_task_status(task_id):
        log("Task failed or timed out", "ERROR")
        return 1
    
    # Step 6: Download results
    if not download_results(task_id, args.output_dir):
        log("Failed to download results", "ERROR")
        return 1
    
    log("=" * 60)
    log("Automation workflow completed successfully!")
    log("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())