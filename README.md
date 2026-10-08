# Eon Plugin for Microsoft 365 Copilot

Connect Microsoft 365 Copilot to Eon. This Microsoft 365 app package connects Copilot to the Eon MCP server and adds an Eon agent for Copilot Chat and a Microsoft 365 recovery skill for Copilot Cowork, so people can find and restore Microsoft 365 and cloud data from their Eon backups in a conversation.

## Capabilities

- **Eon agent for Copilot Chat:** a declarative agent with recovery instructions and 24 pinned Eon tools: Microsoft 365 lookup and restore, backup and restore jobs, ransomware and malware findings, approval requests, and on-demand snapshots of cloud resources.
- **Eon connector for Copilot Cowork:** the Eon MCP server, with every Eon tool available to Cowork's multi-step work.
- **Microsoft 365 recovery skill:** a guided workflow from "I lost it" to a verified restore: find the user, site or team, pick the clean recovery point, search the items, confirm the plan, restore, and track the job.

## Skills

| Skill | Surface | Description |
|-------|---------|-------------|
| Microsoft 365 recovery | Copilot Cowork | Find lost or damaged emails, OneDrive files, SharePoint items, Teams conversations or a whole user in Eon backups and restore them under the user's confirmation, including recovery from the last snapshot with no ransomware findings. |

## Tools

The Eon agent in Copilot Chat uses these Eon MCP tools. Copilot runs the reads directly and asks the user to confirm each tool that changes state, with Eon's own confirmation text.

| Reads (no confirmation) | Changes state (Copilot asks first) |
|---|---|
| `list_projects`, `list_resources`, `get_resource`, `list_resource_snapshots` | `restore_microsoft365_user_mail_by_entity` |
| `list_saas_entities`, `list_saas_entity_snapshots` | `restore_microsoft365_user_drive_by_entity` |
| `search_saas_user_mail`, `search_saas_user_drive`, `search_saas_shared_drive`, `search_saas_team` | `restore_microsoft365_share_point_site_by_entity` |
| `list_restore_accounts`, `list_backup_jobs`, `list_restore_jobs`, `get_restore_job` | `restore_microsoft365_team_by_entity` |
| `list_infected_snapshots`, `list_security_findings` | `restore_microsoft365_user_by_entity` |
| `get_my_action_approval_request` | `take_snapshot`, `create_action_approval_request` |

Copilot Cowork discovers the Eon MCP server's tools at runtime, so it also sees Eon's other tools, such as backup posture and compliance reports. Every tool runs with the signed-in user's Eon role.

## Try it

The Eon agent starts with these prompts:

- "Find the email about the Q3 board deck in Dana's backups and restore it"
- "Restore the Finance folder in Alex's OneDrive from yesterday's backup"
- "Which of our backups have ransomware or malware findings?"
- "Show the restore jobs from the last 24 hours and their status"
- "Did any backup jobs fail this week?"
- "Take a snapshot of our production database now"

## Installation

Eon distributes the plugin through Microsoft Marketplace in the Microsoft 365 and Copilot program (listing coming soon). A Microsoft 365 administrator approves it once in the Microsoft 365 admin center, and users then find **Eon** under Agents in Copilot Chat and under **Sources & Skills > Plugins** in Copilot Cowork.

Requirements:

- A Microsoft 365 Copilot license.
- An Eon subscription with Microsoft 365 or cloud resources protected by Eon, and an Eon user account.

## MCP Server

The plugin connects to `https://mcp.eon.io/mcp` over streamable HTTP. Copilot signs each user in to Eon through OAuth with PKCE (Eon login or the customer's own identity provider), so every tool call runs with that user's Eon role. Copilot asks for confirmation before any tool that changes state, such as a restore or a snapshot, and restores protected by multi-party approval wait for an administrator. Backups stay in Eon: Copilot processes tool results only to answer the request in front of it.

## Building the package

Python 3.11 or later, standard library only.

```bash
python3 scripts/build_package.py --check
python3 scripts/build_package.py --oauth-config-id <registration ID>
```

The package lands in `build/eon-m365-copilot-<version>.zip`. `--check` fails when a state-changing tool lacks a confirmation, when `ai-plugin.json` and `mcp-tools.json` disagree, or when the app name differs across the manifest, the agent and the plugin. Add `--mcp-url https://mcp-testing.eon.io/mcp` with a testing registration ID for a testing build. Bump `version` in `appPackage/manifest.json` for every Partner Center resubmission.

### OAuth client registration

Created once per environment in the [Teams Developer Portal](https://dev.teams.microsoft.com/tools) under **Tools > OAuth client registration**:

| Field | Value |
|---|---|
| Base URL | `https://mcp.eon.io` |
| Restrict usage by org | Any Microsoft 365 organization |
| Restrict usage by app | Any Teams app (an app-bound registration makes every MCP call return 404) |
| Client ID | `microsoft-365-copilot` |
| Client secret | Any value; the client is public and secured by PKCE |
| Client password authentication method | Request body parameters |
| Authorization endpoint | `https://mcp.eon.io/authorize` |
| Token and refresh endpoint | `https://mcp.eon.io/token` |
| Scope | `openid email profile` |
| PKCE | Enabled |

The registration ID it produces goes to the build as `--oauth-config-id`; the source keeps a placeholder.

### Updating the pinned tools

`appPackage/mcp-tools.json` is a snapshot of the Eon MCP server's tool definitions for the functions listed in `appPackage/ai-plugin.json`. Eon maintainers refresh it from the Eon service source (`standalone-services/ai-agent` in `eon-io/eon-service`) whenever the server's tools change:

```bash
uv run --frozen python m365-copilot-plugin/export_tools.py --app-package <path to this repo>/appPackage
```

To pin another tool, add its `functions` entry (with a `confirmation` and `ResourceStateUpdate` when it changes state) and its name to `run_for_functions`, refresh the snapshot, and run `--check`.

### Testing in a tenant

The tenant needs Microsoft 365 Copilot licenses and custom app upload enabled.

```bash
npm install -g @microsoft/m365agentstoolkit-cli
atk auth login
atk install --file-path build/eon-m365-copilot-<version>.zip --scope Personal
```

Then open `https://m365.cloud.microsoft/chat`, pick **Eon** under Agents, and run the prompts above.

## Repository layout

| Path | Contents |
|---|---|
| `appPackage/manifest.json` | Microsoft 365 app manifest (schema 1.29): the agent, the Eon connector and the skill |
| `appPackage/declarativeAgent.json` | The Eon agent for Copilot Chat: instructions and conversation starters |
| `appPackage/ai-plugin.json` | Plugin manifest (schema 2.4): the pinned Eon MCP tools and their confirmations |
| `appPackage/mcp-tools.json` | Snapshot of the pinned tools' definitions from the Eon MCP server |
| `appPackage/skills/` | Agent Skills for Copilot Cowork |
| `scripts/build_package.py` | Validation and packaging |

## Links

- [Eon Platform](https://eon.io)
- [Documentation](https://docs.eon.io)
- [Eon Claude Code Plugin](https://github.com/eon-io/claude-code-eon-plugin)

## License

Licensed under the [Apache License, Version 2.0](LICENSE). See [NOTICE](NOTICE) for attribution and the scope of the license: the Eon service, API, and trademarks are not covered.
