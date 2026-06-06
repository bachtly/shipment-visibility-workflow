#!/usr/bin/env bash
#
# Deploy the latest app build to Azure Container Apps.
#
#   ./deploy.sh            # deploy dev (default)
#   ./deploy.sh staging    # deploy staging
#   AUTO_APPROVE=1 ./deploy.sh   # skip the terragrunt apply confirmation
#
# What it does, in one shot:
#   1. builds the Docker image in ACR (cloud build — no local Docker required)
#   2. tags it with the git short SHA so every deploy creates a NEW revision
#      (re-pushing :latest would not change the digest and Container Apps would
#       skip creating a revision)
#   3. runs `terragrunt apply` with TF_VAR_container_image pointed at that image
#
set -euo pipefail

ENV="${1:-dev}"
RG="rg-shipvis-${ENV}"
IMAGE_REPO="shipvis"

# Resolve paths relative to this script, so it works from any cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
LIVE_DIR="$REPO_ROOT/infra/live/$ENV"

# --- preflight --------------------------------------------------------------
command -v az          >/dev/null || { echo "ERROR: az CLI not found";        exit 1; }
command -v terragrunt  >/dev/null || { echo "ERROR: terragrunt not found";    exit 1; }
az account show >/dev/null 2>&1   || { echo "ERROR: run 'az login' first";    exit 1; }
[ -d "$LIVE_DIR" ]                || { echo "ERROR: $LIVE_DIR not found";      exit 1; }

# NOTE: on this machine `az`/`git` are the Windows CLIs (run via WSL interop) and
# emit CRLF. Command substitution keeps the trailing \r, which corrupts any value
# later passed as an argument (e.g. an ACR name). Strip it from every capture.
SUB_NAME="$(az account show --query name -o tsv | tr -d '\r')"
SUB_ID="$(az account show --query id -o tsv | tr -d '\r')"
echo "==> Subscription: ${SUB_NAME}  /  ${SUB_ID}"
echo "==> Environment:  $ENV   (resource group: $RG)"

# --- image tag: git short SHA (+ -dirty), fallback to timestamp -------------
if TAG="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null | tr -d '\r')"; then
  [ -n "$(git -C "$REPO_ROOT" status --porcelain 2>/dev/null)" ] && TAG="${TAG}-dirty-$(date +%H%M%S)"
else
  TAG="$(date +%Y%m%d-%H%M%S)"
fi

# --- discover ACR -----------------------------------------------------------
ACR="$(az acr list -g "$RG" --query '[0].name' -o tsv | tr -d '\r')"
[ -n "$ACR" ] || { echo "ERROR: no ACR in $RG — has the infra been applied?"; exit 1; }
LOGIN="$(az acr show -n "$ACR" --query loginServer -o tsv | tr -d '\r')"
IMAGE="$LOGIN/$IMAGE_REPO:$TAG"

# --- build in ACR -----------------------------------------------------------
# The Windows `az` (run via WSL interop) needs a Windows path for the build
# context; a native Linux `az` keeps the WSL path. Detect and convert.
BUILD_CONTEXT="$REPO_ROOT"
case "$(command -v az)" in
  /mnt/*) BUILD_CONTEXT="$(wslpath -w "$REPO_ROOT")" ;;
esac

echo "==> Building $IMAGE  (cloud build in ACR '$ACR')"
echo "    context: $BUILD_CONTEXT"
az acr build --registry "$ACR" \
  --image "$IMAGE_REPO:$TAG" \
  --image "$IMAGE_REPO:latest" \
  "$BUILD_CONTEXT"

# --- deploy -----------------------------------------------------------------
echo "==> Deploying to Container App ($ENV)"
cd "$LIVE_DIR"
export TF_VAR_container_image="$IMAGE"
if [ "${AUTO_APPROVE:-0}" = "1" ]; then
  terragrunt apply -auto-approve
else
  terragrunt apply
fi

# --- report -----------------------------------------------------------------
FQDN="$(terragrunt output -raw container_app_fqdn 2>/dev/null | tr -d '\r' || true)"
echo "----------------------------------------------------------------------"
echo "Deployed image: $IMAGE"
[ -n "$FQDN" ] && echo "App URL:        https://$FQDN"
echo "Done."
