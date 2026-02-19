#!/usr/bin/env bash
set -euo pipefail

# TP Bot one-button deploy (GitHub-first) for Ubuntu VM.
# Intended bootstrap usage:
# curl -fsSL https://raw.githubusercontent.com/andyelka-creator/TelegramBotForSupport/main/scripts/deploy_tpbot.sh | sudo bash

PROJECT_DIR="/opt/tpbot"
POSTGRES_MOUNT="/var/lib/postgres-data"
DEFAULT_REPO="https://github.com/andyelka-creator/TelegramBotForSupport.git"
DEFAULT_REF="main"

SKIP_DOCKER_INSTALL=0
SKIP_BUILD=0
SKIP_MIGRATE=0

for arg in "$@"; do
  case "$arg" in
    --skip-docker-install) SKIP_DOCKER_INSTALL=1 ;;
    --skip-build) SKIP_BUILD=1 ;;
    --skip-migrate) SKIP_MIGRATE=1 ;;
    -h|--help)
      cat <<USAGE
Usage: deploy_tpbot.sh [--skip-docker-install] [--skip-build] [--skip-migrate]
USAGE
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown argument: $arg" >&2
      exit 1
      ;;
  esac
done

if [ "${EUID}" -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi

DOCKER_PREFIX=""

log() { echo "[INFO] $*"; }
warn() { echo "[WARN] $*"; }
fail() { echo "[ERROR] $*" >&2; exit 1; }

ensure_not_inside_project_dir() {
  local cwd
  cwd="$(pwd -P 2>/dev/null || echo '')"
  if [ -n "$cwd" ] && { [ "$cwd" = "$PROJECT_DIR" ] || [ "${cwd#"$PROJECT_DIR"}" != "$cwd" ]; }; then
    warn "Current directory is inside $PROJECT_DIR; switching to / for safe update operations."
    cd /
  fi
}

enter_project_dir() {
  cd "$PROJECT_DIR" || fail "Cannot enter $PROJECT_DIR"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

docker_cmd() {
  # shellcheck disable=SC2086
  ${DOCKER_PREFIX} docker "$@"
}

docker_compose_cmd() {
  # shellcheck disable=SC2086
  ${DOCKER_PREFIX} docker compose -f "$PROJECT_DIR/docker-compose.yml" "$@"
}

check_os() {
  [ -f /etc/os-release ] || fail "Cannot detect OS: /etc/os-release missing"
  # shellcheck disable=SC1091
  . /etc/os-release
  [ "${ID:-}" = "ubuntu" ] || fail "This script supports Ubuntu only"
  if [ "${VERSION_ID:-}" != "22.04" ]; then
    warn "Tested for Ubuntu 22.04, detected ${VERSION_ID:-unknown}"
  fi
}

ensure_mountpoint() {
  log "Checking second disk mountpoint: $POSTGRES_MOUNT"
  mountpoint -q "$POSTGRES_MOUNT" || fail "$POSTGRES_MOUNT is not a mountpoint. Mount second disk and retry."
}

sync_repo() {
  local repo_url ref
  repo_url="${GIT_REPO:-$DEFAULT_REPO}"
  ref="${GIT_REF:-$DEFAULT_REF}"

  if [ ! -d "$PROJECT_DIR" ]; then
    log "Project directory missing, cloning repository"
    require_cmd git
    $SUDO mkdir -p "$(dirname "$PROJECT_DIR")"
    # shellcheck disable=SC2086
    $SUDO git clone "$repo_url" "$PROJECT_DIR"
    # shellcheck disable=SC2086
    $SUDO git -C "$PROJECT_DIR" checkout "$ref"
    return
  fi

  if [ ! -d "$PROJECT_DIR/.git" ]; then
    if [ -z "$(ls -A "$PROJECT_DIR" 2>/dev/null || true)" ]; then
      warn "$PROJECT_DIR exists and is empty; replacing with fresh clone"
      $SUDO rm -rf "$PROJECT_DIR"
      $SUDO git clone "$repo_url" "$PROJECT_DIR"
      $SUDO git -C "$PROJECT_DIR" checkout "$ref"
      return
    fi

    if [ -f "$PROJECT_DIR/Dockerfile" ] && [ -f "$PROJECT_DIR/.env.example" ] && [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
      warn "$PROJECT_DIR is not a git repository. Proceeding with existing project files and skipping git sync."
      return
    fi

    fail "$PROJECT_DIR exists but is not a git repository and does not look like a TP Bot project directory."
  fi

  log "Updating repository in $PROJECT_DIR"
  local has_changes
  # shellcheck disable=SC2086
  has_changes="$($SUDO git -C "$PROJECT_DIR" status --porcelain)"
  if [ -n "$has_changes" ]; then
    warn "Local changes detected in $PROJECT_DIR. Skipping git update to avoid data loss."
    return
  fi

  # shellcheck disable=SC2086
  $SUDO git -C "$PROJECT_DIR" fetch --all --prune
  # shellcheck disable=SC2086
  $SUDO git -C "$PROJECT_DIR" checkout "$ref"
  # shellcheck disable=SC2086
  $SUDO git -C "$PROJECT_DIR" pull --ff-only origin "$ref"
}

validate_project_layout() {
  [ -f "$PROJECT_DIR/Dockerfile" ] || fail "Missing $PROJECT_DIR/Dockerfile"
  [ -f "$PROJECT_DIR/.env.example" ] || fail "Missing $PROJECT_DIR/.env.example"
  [ -f "$PROJECT_DIR/docker-compose.yml" ] || fail "Missing $PROJECT_DIR/docker-compose.yml"
  [ -f "$PROJECT_DIR/alembic.ini" ] || fail "Missing $PROJECT_DIR/alembic.ini"
}

install_docker() {
  if [ "$SKIP_DOCKER_INSTALL" -eq 1 ]; then
    log "Skipping Docker installation (--skip-docker-install)"
    return
  fi

  log "Installing Docker Engine and Compose plugin (official APT repo)"
  $SUDO apt-get update -y
  $SUDO apt-get install -y ca-certificates curl gnupg lsb-release

  $SUDO install -m 0755 -d /etc/apt/keyrings
  if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    $SUDO chmod a+r /etc/apt/keyrings/docker.gpg
  fi

  local arch codename
  arch="$(dpkg --print-architecture)"
  codename="$(. /etc/os-release && echo "$UBUNTU_CODENAME")"

  echo "deb [arch=${arch} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${codename} stable" \
    | $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null

  $SUDO apt-get update -y
  $SUDO apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  $SUDO systemctl enable docker
  $SUDO systemctl restart docker
}

detect_docker_access() {
  if [ "${EUID}" -eq 0 ]; then
    DOCKER_PREFIX=""
  elif id -nG "$USER" | grep -qw docker; then
    DOCKER_PREFIX=""
  else
    DOCKER_PREFIX="sudo"
    warn "User is not in docker group; docker commands will run via sudo"
  fi

  docker_cmd --version >/dev/null 2>&1 || fail "Docker is not available"
  docker_compose_cmd version >/dev/null 2>&1 || fail "Docker Compose plugin is not available"
}

prepare_pg_mount_permissions() {
  log "Ensuring permissions for $POSTGRES_MOUNT (uid:gid 999:999)"
  $SUDO mkdir -p "$POSTGRES_MOUNT"
  $SUDO mkdir -p "$POSTGRES_MOUNT/pgdata"

  if [ -z "$(ls -A "$POSTGRES_MOUNT" 2>/dev/null || true)" ]; then
    $SUDO chown -R 999:999 "$POSTGRES_MOUNT"
  else
    $SUDO chown 999:999 "$POSTGRES_MOUNT"
    $SUDO chown -R 999:999 "$POSTGRES_MOUNT/pgdata"
  fi
  $SUDO chmod 700 "$POSTGRES_MOUNT"
  $SUDO chmod 700 "$POSTGRES_MOUNT/pgdata"
}

ensure_env_gitignored() {
  local gitignore
  gitignore="$PROJECT_DIR/.gitignore"

  if [ ! -f "$gitignore" ]; then
    echo ".env" | $SUDO tee "$gitignore" >/dev/null
    return
  fi

  if ! grep -qE '^\.env$' "$gitignore"; then
    echo ".env" | $SUDO tee -a "$gitignore" >/dev/null
  fi
}

read_env_value() {
  local key file line
  key="$1"
  file="$2"

  line="$(grep -E "^${key}=" "$file" | tail -n 1 || true)"
  if [ -z "$line" ]; then
    echo ""
  else
    echo "${line#*=}"
  fi
}

set_env_if_missing_or_change_me() {
  local key value file current
  key="$1"
  value="$2"
  file="$3"

  current="$(read_env_value "$key" "$file")"

  if [ -z "$current" ]; then
    echo "${key}=${value}" | $SUDO tee -a "$file" >/dev/null
    return
  fi

  if [ "$current" = "CHANGE_ME" ]; then
    $SUDO sed -i "s|^${key}=.*|${key}=${value}|g" "$file"
  fi
}

ensure_env_file() {
  local env_file env_example
  env_file="$PROJECT_DIR/.env"
  env_example="$PROJECT_DIR/.env.example"

  if [ ! -f "$env_file" ]; then
    log "Creating $env_file from .env.example"
    umask 077
    $SUDO cp "$env_example" "$env_file"
    $SUDO chmod 600 "$env_file"
  else
    $SUDO chmod 600 "$env_file"
  fi

  set_env_if_missing_or_change_me "POSTGRES_DB" "tp_bot" "$env_file"
  set_env_if_missing_or_change_me "POSTGRES_USER" "tp_user" "$env_file"
  set_env_if_missing_or_change_me "POSTGRES_PASSWORD" "CHANGE_ME" "$env_file"
  set_env_if_missing_or_change_me "CONTROL_BOT_TOKEN" "CHANGE_ME" "$env_file"
  set_env_if_missing_or_change_me "INTAKE_BOT_TOKEN" "CHANGE_ME" "$env_file"
  set_env_if_missing_or_change_me "CONTROL_GROUP_CHAT_ID" "-5264627742" "$env_file"
  set_env_if_missing_or_change_me "CONTROL_GROUP_ID" "-5264627742" "$env_file"
  set_env_if_missing_or_change_me "LOG_LEVEL" "INFO" "$env_file"

  derive_database_url_if_needed "$env_file"
}

derive_database_url_if_needed() {
  local env_file p_user p_pass p_db db_url
  env_file="$1"

  p_user="$(read_env_value "POSTGRES_USER" "$env_file")"
  p_pass="$(read_env_value "POSTGRES_PASSWORD" "$env_file")"
  p_db="$(read_env_value "POSTGRES_DB" "$env_file")"
  db_url="$(read_env_value "DATABASE_URL" "$env_file")"

  if [ -z "$p_user" ] || [ "$p_user" = "CHANGE_ME" ]; then
    return
  fi
  if [ -z "$p_db" ] || [ "$p_db" = "CHANGE_ME" ]; then
    return
  fi
  if [ -z "$p_pass" ] || [ "$p_pass" = "CHANGE_ME" ]; then
    return
  fi

  if [ -z "$db_url" ] || echo "$db_url" | grep -q "CHANGE_ME"; then
    local derived
    derived="postgresql+asyncpg://${p_user}:${p_pass}@db:5432/${p_db}"
    if grep -qE '^DATABASE_URL=' "$env_file"; then
      $SUDO sed -i "s|^DATABASE_URL=.*|DATABASE_URL=${derived}|g" "$env_file"
    else
      echo "DATABASE_URL=${derived}" | $SUDO tee -a "$env_file" >/dev/null
    fi
  fi
}

required_app_env_ready() {
  local env_file db_url control_token intake_token
  env_file="$PROJECT_DIR/.env"

  db_url="$(read_env_value "DATABASE_URL" "$env_file")"
  control_token="$(read_env_value "CONTROL_BOT_TOKEN" "$env_file")"
  intake_token="$(read_env_value "INTAKE_BOT_TOKEN" "$env_file")"

  [ -n "$db_url" ] || return 1
  [ -n "$control_token" ] || return 1
  [ -n "$intake_token" ] || return 1

  [ "$db_url" != "CHANGE_ME" ] || return 1
  [ "$control_token" != "CHANGE_ME" ] || return 1
  [ "$intake_token" != "CHANGE_ME" ] || return 1

  echo "$db_url" | grep -q "CHANGE_ME" && return 1
  echo "$control_token" | grep -q "CHANGE_ME" && return 1
  echo "$intake_token" | grep -q "CHANGE_ME" && return 1

  return 0
}

wait_for_db_healthy() {
  log "Starting db service"
  docker_compose_cmd up -d db

  log "Waiting for db health"
  local cid i status
  cid="$(docker_compose_cmd ps -q db)"
  [ -n "$cid" ] || fail "Failed to get db container ID"

  for i in $(seq 1 90); do
    status="$(docker_cmd inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}starting{{end}}' "$cid" 2>/dev/null || true)"
    if [ "$status" = "healthy" ]; then
      log "db is healthy"
      return
    fi
    if [ "$status" = "unhealthy" ]; then
      fail "db became unhealthy. Check logs with: ${DOCKER_PREFIX:+$DOCKER_PREFIX }docker compose -f $PROJECT_DIR/docker-compose.yml logs db"
    fi
    sleep 2
  done

  fail "Timed out waiting for db health"
}

start_app_stack() {
  log "Starting api + control_bot + intake_bot"
  if [ "$SKIP_BUILD" -eq 1 ]; then
    docker_compose_cmd up -d api control_bot intake_bot
  else
    docker_compose_cmd up -d --build api control_bot intake_bot
  fi
}

run_migrations() {
  if [ "$SKIP_MIGRATE" -eq 1 ]; then
    log "Skipping migrations (--skip-migrate)"
    return
  fi

  log "Waiting for api container to be running before migrations"
  local cid i running
  cid=""
  for i in $(seq 1 60); do
    cid="$(docker_compose_cmd ps -q api 2>/dev/null || true)"
    if [ -n "$cid" ]; then
      running="$(docker_cmd inspect --format '{{.State.Running}}' "$cid" 2>/dev/null || true)"
      if [ "$running" = "true" ]; then
        break
      fi
    fi
    sleep 1
  done

  if [ -z "$cid" ]; then
    warn "api container not found; skipping migrations"
    echo "Manual command: ${DOCKER_PREFIX:+$DOCKER_PREFIX }docker compose -f $PROJECT_DIR/docker-compose.yml exec -T api alembic upgrade head"
    return
  fi

  running="$(docker_cmd inspect --format '{{.State.Running}}' "$cid" 2>/dev/null || true)"
  if [ "$running" != "true" ]; then
    warn "api container is not running; skipping migrations"
    echo "Manual command: ${DOCKER_PREFIX:+$DOCKER_PREFIX }docker compose -f $PROJECT_DIR/docker-compose.yml exec -T api alembic upgrade head"
    return
  fi

  if docker_compose_cmd exec -T api sh -lc 'command -v alembic >/dev/null 2>&1'; then
    log "Running alembic upgrade head"
    docker_compose_cmd exec -T api alembic upgrade head
  else
    warn "Alembic is not available in api container"
    echo "Manual command: ${DOCKER_PREFIX:+$DOCKER_PREFIX }docker compose -f $PROJECT_DIR/docker-compose.yml exec -T api alembic upgrade head"
  fi
}

print_next_steps() {
  echo
  echo "Next steps:"
  echo "1) Edit $PROJECT_DIR/.env and set values for:"
  echo "   - POSTGRES_PASSWORD"
  echo "   - CONTROL_BOT_TOKEN"
  echo "   - INTAKE_BOT_TOKEN"
  echo "2) Ensure CONTROL_GROUP_CHAT_ID=-5264627742"
  echo "3) In BotFather disable privacy (/setprivacy -> Disable) for:"
  echo "   - @tp19022026control_bot"
  echo "   - @tp19022026intake_bot"
  echo "4) Add @tp19022026control_bot to your private admin group"
  echo "5) Restart stack: ${DOCKER_PREFIX:+$DOCKER_PREFIX }docker compose -f $PROJECT_DIR/docker-compose.yml up -d"
  echo "6) Verify: curl http://localhost:8000/health"
  echo "7) Verify logs: ${DOCKER_PREFIX:+$DOCKER_PREFIX }docker compose -f $PROJECT_DIR/docker-compose.yml logs -f control_bot"
  echo
}

main() {
  ensure_not_inside_project_dir
  check_os
  ensure_mountpoint
  sync_repo
  validate_project_layout
  enter_project_dir
  install_docker
  detect_docker_access
  prepare_pg_mount_permissions
  ensure_env_gitignored
  ensure_env_file

  wait_for_db_healthy

  if ! required_app_env_ready; then
    warn "Required app vars are not configured yet (DATABASE_URL, CONTROL_BOT_TOKEN, INTAKE_BOT_TOKEN)."
    print_next_steps
    exit 0
  fi

  start_app_stack
  run_migrations
  print_next_steps
}

main "$@"
