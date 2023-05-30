#!/bin/bash

# Instructions:
# 1. Make sure kubectl has access to the Kubernetes cluster.
# 2. Run this script from anywhere inside the kitsune repo.
# 3. Commit the changes, if any, and file a PR.

set -euo pipefail

if ! git diff-index --quiet HEAD; then
    >&2 echo "Working directory is not clean. Please commit or stage your changes first."
    exit 1
fi

TARGET="$(git rev-parse --show-toplevel)/kitsune/sumo/db_strings.py"
if ! [ -e "$TARGET" ]; then
    >&2 echo "Cannot find $TARGET."
    >&2 echo "Is your current working directory inside the kitsune repo?"
    exit 1
fi

SELECTOR="${1:-app.kubernetes.io/component=web,app.kubernetes.io/name=sumo,env_code=prod}"
KUBECTL="${KUBECTL:-kubectl -n sumo-prod}"

POD="$($KUBECTL get pods --selector "$SELECTOR" -o json | jq -r '.items[0].metadata.name')"
$KUBECTL exec -ti "$POD" -- ./manage.py extract_db -o /tmp/db_strings.py
$KUBECTL cp ${POD}:/tmp/db_strings.py "$TARGET"

git status
