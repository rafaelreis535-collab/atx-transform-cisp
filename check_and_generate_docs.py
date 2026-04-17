#!/usr/bin/env python3
"""
Script para verificar se projeto já existe e gerar documentação.
Se o projeto já existir, apenas faz upload e gera documentação.
Se não existir, retorna código 1 para que o ATX seja executado.
"""

import json
import os
import sys
import time
from pathlib import Path

# Import functions from mcp_client and automate_docs
import mcp_client
from automate_docs import (
    log,
    find_project_by_name,
    wait_for_indexing,
    poll_task_status,
    download_results
)


def get_project_name_from_path(project_path: str) -> str:
    """Deriva o nome do projeto do PROJECT_PATH.
    
    Examples:
        ./banking-example -> banking-example
        ./src/my-project -> my-project
        /absolute/path/to/project -> project
    """
    clean_path = project_path.strip("./")
    project_name = os.path.basename(clean_path)
    return project_name


def create_zip_from_directory(source_dir: str, output_zip: str) -> bool:
    """Create a ZIP file from a directory."""
    import zipfile
    
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


def find_project_by_partial_name(partial_name: str) -> Optional[Dict[str, Any]]:
    """Search for a project by partial name match.
    
    Args:
        partial_name: Partial name to search for (e.g., "banking")
        
    Returns:
        Project dict if found, None otherwise
    """
    log(f"Searching for projects containing: {partial_name}")
    
    offset = 0
    limit = 100
    
    while True:
        result_json = mcp_client.list_projects(limit=limit, offset=offset)
        result = json.loads(result_json)
        
        if "error" in result:
            log(f"Error listing projects: {result['error']}", "ERROR")
            return None
        
        items = result.get("items", [])
        
        # Search for project by partial name (case-insensitive)
        partial_lower = partial_name.lower()
        for project in items:
            project_name = project.get("name", "")
            if partial_lower in project_name.lower():
                log(f"Found project with matching name: {project_name} (ID: {project.get('id')})")
                return project
        
        # Check if there are more pages
        if not result.get("has_more", False):
            break
            
        offset += limit
    
    log(f"No project found containing '{partial_name}'", "WARNING")
    return None


def main() -> int:
    """Main workflow."""
    # Get PROJECT_PATH from environment
    project_path = os.environ.get("PROJECT_PATH")
    if not project_path:
        log("PROJECT_PATH environment variable not set", "ERROR")
        return 1
    
    # Validate environment
    if not mcp_client.API_KEY:
        log("MODERNIZATION_API_KEY environment variable not set", "ERROR")
        return 1
    
    if mcp_client.ORG_ID is None:
        log("MODERNIZATION_ORG_ID environment variable not set", "ERROR")
        return 1
    
    # Derive project name
    project_name = get_project_name_from_path(project_path)
    log(f"Project name derived from PROJECT_PATH: {project_name}")
    
    log("=" * 60)
    log("Checking if project already exists...")
    log(f"API URL: {mcp_client.API_BASE_URL}")
    log(f"Organization ID: {mcp_client.ORG_ID}")
    log(f"Project name: {project_name}")
    log("=" * 60)
    
    # Check if project exists by exact name first
    existing_project = find_project_by_name(project_name)
    
    # If not found by exact name, try partial match
    if not existing_project:
        log(f"Exact match not found, trying partial match...")
        existing_project = find_project_by_partial_name(project_name)
    
    if not existing_project:
        log(f"Project '{project_name}' does not exist yet", "INFO")
        log("ATX transformation will be executed to create the project")
        return 1  # Exit code 1 = project doesn't exist, run ATX
    
    # Project exists, proceed with upload and documentation
    project_id = existing_project.get("id")
    log(f"Project '{project_name}' already exists with ID: {project_id}")
    log("Skipping ATX transformation, proceeding with documentation generation only")
    
    # Create ZIP file
    zip_filename = f"{project_name}.zip"
    if not create_zip_from_directory(project_path, zip_filename):
        log("Failed to create ZIP file", "ERROR")
        return 2
    
    # Upload ZIP file
    log(f"Uploading ZIP file: {zip_filename}")
    result_json = mcp_client.upload_project_zip(project_id, zip_filename)
    result = json.loads(result_json)
    
    if "error" in result:
        log(f"Upload failed: {result['error']}", "ERROR")
        return 2
    
    log(f"Upload status: {result.get('status')}")
    
    # Wait for indexing
    if not wait_for_indexing(project_id):
        log("Indexing failed or timed out", "ERROR")
        return 2
    
    # Start documentation task
    task_name = f"{project_name} - Docs - {time.strftime('%Y-%m-%d %H:%M:%S')}"
    log(f"Starting documentation task: {task_name}")
    
    result_json = mcp_client.generate_docs(project_id, task_name)
    result = json.loads(result_json)
    
    if "error" in result:
        log(f"Failed to start task: {result['error']}", "ERROR")
        return 2
    
    task_id = result.get("id")
    log(f"Task created: {task_id}")
    
    # Poll until completion
    if not poll_task_status(task_id):
        log("Task failed or timed out", "ERROR")
        return 2
    
    # Download results
    output_dir = "./output"
    if not download_results(task_id, output_dir):
        log("Failed to download results", "ERROR")
        return 2
    
    log("=" * 60)
    log("Documentation generation completed successfully!")
    log("ATX transformation was skipped (project already exists)")
    log("=" * 60)
    return 0  # Exit code 0 = success, don't run ATX


if __name__ == "__main__":
    sys.exit(main())