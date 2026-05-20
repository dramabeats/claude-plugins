#!/usr/bin/env bash
# hooks/screenshot.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
LATEST_JSON="$REPO_DIR/latest.json"

prompt="$(cat)"

if grep -qi "screenshot" <<< "$prompt"; then
    if [[ -f "$LATEST_JSON" ]]; then
        path="$(sed 's/.*"path": "\([^"]*\)".*/\1/' "$LATEST_JSON")"
        if [[ -n "$path" && "$path" != *"{"* ]]; then
            printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"Latest screenshot: %s"}}\n' "$path"
        fi
    fi
fi
