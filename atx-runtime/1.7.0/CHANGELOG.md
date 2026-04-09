# Changelog

All notable changes to the AWS Transform CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - TBD

## [1.7.0] - 2026-04-02
- Fixed: `exec` command now exits with code 1 on input validation errors instead of code 0, making the CLI reliable in scripts and CI/CD pipelines
- Added: Display warning messages from the service (e.g., SLR creation status for customer-side metrics publishing)
- Added: MFA prompt support for AWS credential profiles — when a profile requires MFA, the CLI now prompts for the TOTP code instead of failing
- Added: Support for experimental skill-format transformation definitions (SKILL.md with YAML frontmatter + optional references/ directory) alongside the existing transformation_definition.md format
- Added: Propagate executionId from parent main agent to sub-agents so all agents in a execution share the same execution context to support BI Metrics
- Removed: `--advanced-java-mvn-debugger` CLI flag
- Changed: Defer creation of document_references/ directory until first use by document_manager tool, preventing empty directory from appearing in skill-format staging paths
- Fixed: STS credential calls (MFA, role assumption) now respect HTTP(S) proxy settings via shared ProxyAgent configuration
- Fixed: Redact pre-signed S3 URLs containing temporary AWS credentials (`X-Amz-Security-Token`, `X-Amz-Credential`, `X-Amz-Signature`) from `--json` output and debug logs. `publish --json` and `save-draft --json` now only emit the `completeTpUploadResponse` (name, version, metadata) instead of the raw pre-signed URL. Debug logs now show only the S3 hostname instead of the full URL with credentials.
- Fixed: Set log file permissions to `0o600` (owner-only read/write) for both `debug.log` and `error.log` to prevent other users on the machine from reading sensitive log content
- Added: MCP tool usage tracking per execution, persisted as mcp_usage.json alongside metadata.json on checkpoint advancement and conversation end

## [1.6.0] - 2026-03-18
- Fixed: Pre-prod endpoint region resolution for multi-region support
- Fixed: Log the initial user message in conversation logs
- Added --limit <minutes> Option: Set an Agent Minutes budget limit for both exec and interactive commands. Compares accumulated Agent Minutes against the limit after each ConversationEvent. When limit is reached, displays "⚠️ Budget limit reached: X.XX / N.NN Agent Minutes. Exiting." with resume instructions, then triggers graceful shutdown.
- Added: Pass `isCheckpointResume` flag in ConversationState to inform checkpoint-resume specific logic handling in agent
- Added: Optional `kwargs` parameter to the handoff tool to permit agents to pass key-value parameters to sub-agents. 
- Fixed: Strip undeclared fields from MCP tool input before forwarding to MCP servers, preventing validation errors on servers with strict schemas

## [1.5.0] - 2026-03-11

- Added: Support for parallel sub-agent execution via handoff tool, enabling the orchestrator agent to spawn multiple sub-agents concurrently for faster task completion
- Changed: Remove version from list_available_transformations_from_registry JSON response to prevent agent from picking wrong TD version
- Added: Agent Minutes Accumulation: 
  - Accumulate agentMinutes received in ConversationEvent throughout the conversation lifecycle and displayed as Agent Minutes used: X.XX at the end of conversation.
  - New interactive-mode command that displays accumulated agent minutes on demand. Type `/usage` at the input prompt to see `Agent Minutes used: X.XX`
- Fixed: Support MCP tools whose names contain the `___` delimiter

## [1.4.0] - 2026-03-02

- Fixed: Skip git instructions file generation when not on atx-result-staging branches
- Fixed: Improve error message when saving transformation definitions with unsupported files
- Added: Calculate git diff metrics when VCS control commit is invoked and include them in clientMetadata for backend analytics
- Fixed: shell tool interface simplified and properly terminates commands that spawn child processes
- Added: Track interrupt reason and time on conversation exit (ctrl+c or errors) for backend analytics and resume support
- Added: Timeout to FES calls which avoids CLI hanging if connection is interrupted
- Fixed: Remove requestTimeout from NodeHttpHandler — prevents ECONNRESET mid-stream and fixes process-not-exiting bug (requestTimeout timer kept event loop alive preventing CLI exit after conversation ends)
- Fixed: Validate region match when resuming conversations
- Fixed: CLI process hangs indefinitely after successful completion instead of exiting with code 0 — added explicit graceful shutdown after event loop finishes in both exec and interactive commands

## [1.3.0] - 2026-02-19

- Added: Use dedicated author identity (ATX Bot \<checkpoint@atx.bot\>) for checkpoint commits so CodeDefender can distinguish ATX-initiated --no-verify usage from user-initiated bypasses
- Added: Include campaignName in client metadata
- Changed: Use `transform-cli.awsstatic.com` URL for update checks
  - Fallback to legacy URL if this URL is not available/allowlisted
- Changed: Removed restriction for MCP paths and users may now specify any path for the `command` property in the MCP configuration.
- Changed: Made `code_repository_path` a required input for the vcs_control tool
- Fixed: Gracefully handle MCP servers that emit non-JSON to stdio and contain empty tool descriptions


## [1.2.0] - 2026-02-09

- Added: Respect client's proxy configuration environment variables (https_proxy, no_proxy, etc)
  - Ensure all proxy calls use HTTP CONNECT method
- Changed: Default Java advanced debugging agent off. Allow advanced debugger to be enabled via new `--advanced-java-mvn-debugger` flag.
- Fixed: Update vcs_control tool to output what the action and summary of what the agent is requesting.
- Fixed: Ensure hyperlink formatting only used in supported terminals.


## [1.1.1] - 2026-01-16

- Fixed: Remove dependency on STS for permission checking
- Fixed: Revert SDK library change causing end-of-conversation decode payload error


## [1.1.0] - 2026-01-13

- Added AWS CLI region configuration support, added early credential validation checks, fixed campaign resume functionality, other general improvements


## [1.0.1] - 2025-12-18

- Graceful shutdowns, cleaner error logs, and general improvements

## [1.0.0] - 2025-12-01

- Initial release of AWS Transform CLI

---

## Version Format

- **Major.Minor.Patch** (e.g., 1.2.3) for stable releases
- **Major.Minor.Patch-beta** (e.g., 1.2.3-beta.\<number\>) for beta releases  

## Links

- [License](LICENSE)
- [Notice](NOTICE)
