"""Validate appPackage/ and build the Microsoft 365 app package (.zip) for the Eon plugin.

    python3 scripts/build_package.py --oauth-config-id <Teams Developer Portal registration ID>
    python3 scripts/build_package.py --check
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_PACKAGE = ROOT / "appPackage"
PLACEHOLDER_OAUTH = "${{EON_MCP_OAUTH_CONFIG_ID}}"
PLACEHOLDER_URL = "${{EON_MCP_URL}}"
PROD_MCP_URL = "https://mcp.eon.io/mcp"


def check() -> list[str]:
    """Problems that would fail the build or Microsoft 365 store validation.

    Copilot only prompts before a call when the tool says it isn't read-only, and store
    validation also wants a custom confirmation text and a ResourceStateUpdate
    attestation on those functions, so ai-plugin.json and mcp-tools.json must agree.
    """
    plugin = json.loads((APP_PACKAGE / "ai-plugin.json").read_text())
    tools = {t["name"]: t for t in json.loads((APP_PACKAGE / "mcp-tools.json").read_text())["tools"]}
    manifest = json.loads((APP_PACKAGE / "manifest.json").read_text())
    agent = json.loads((APP_PACKAGE / "declarativeAgent.json").read_text())
    errors: list[str] = []

    names = [f["name"] for f in plugin["functions"]]
    if plugin["runtimes"][0]["run_for_functions"] != names:
        errors.append("ai-plugin.json: run_for_functions must list exactly the functions, in order")
    if set(tools) != set(names):
        errors.append(f"mcp-tools.json and ai-plugin.json disagree: {sorted(set(tools) ^ set(names))}")
    for function in plugin["functions"]:
        name, tool = function["name"], tools.get(function["name"])
        if tool is None:
            continue
        read_only = tool.get("annotations", {}).get("readOnlyHint")
        capabilities = function.get("capabilities", {})
        handling = capabilities.get("security_info", {}).get("data_handling", [])
        if read_only is None:
            errors.append(f"{name}: tool carries no readOnlyHint")
        elif read_only is False:
            if "confirmation" not in capabilities:
                errors.append(f"{name}: changes state but has no confirmation")
            if "ResourceStateUpdate" not in handling:
                errors.append(f"{name}: changes state but lacks ResourceStateUpdate")
        elif "ResourceStateUpdate" in handling:
            errors.append(f"{name}: read-only tool declared as ResourceStateUpdate")

    # Store validation rejects a declarative agent whose names don't match across files.
    app_names = {manifest["name"]["short"], agent["name"], plugin["name_for_human"]}
    if len(app_names) != 1:
        errors.append(f"app name differs across manifest, agent and plugin: {sorted(app_names)}")
    return errors


def build(oauth_config_id: str, mcp_url: str, out: Path) -> Path:
    values = {PLACEHOLDER_OAUTH: oauth_config_id, PLACEHOLDER_URL: mcp_url}
    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "appPackage"
        shutil.copytree(APP_PACKAGE, staging)
        for name in ("manifest.json", "ai-plugin.json"):
            path = staging / name
            text = path.read_text()
            for placeholder, value in values.items():
                text = text.replace(placeholder, value)
            if "${{" in text:
                raise SystemExit(f"{name} still holds an unresolved placeholder")
            path.write_text(text)

        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in sorted(staging.rglob("*")):
                if file.is_file() and not file.name.startswith("."):
                    zf.write(file, file.relative_to(staging).as_posix())
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="Validate only; build nothing.")
    parser.add_argument("--oauth-config-id", help="OAuth client registration ID from the Teams Developer Portal.")
    parser.add_argument("--mcp-url", default=PROD_MCP_URL)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    errors = check()
    if errors:
        print("appPackage is invalid:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 1
    if args.check:
        print("appPackage OK")
        return 0
    if not args.oauth_config_id:
        parser.error("--oauth-config-id is required to build")

    version = json.loads((APP_PACKAGE / "manifest.json").read_text())["version"]
    out = args.out or ROOT / "build" / f"eon-m365-copilot-{version}.zip"
    print(build(args.oauth_config_id, args.mcp_url, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
