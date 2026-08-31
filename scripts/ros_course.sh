#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
command="${1:-start}"

case "$command" in
  setup)
    docker compose up -d --build
    docker compose exec course-ros course-build-workspaces
    docker compose exec course-ros course-doctor
    echo "Setup complete. Open http://localhost:6080/vnc.html?autoconnect=1&resize=remote"
    ;;
  start) docker compose up -d ;;
  build) docker compose exec course-ros course-build-workspaces ;;
  lab)
    lab="${2:-}"
    [[ -n "$lab" ]] || { echo "Provide a lab directory, for example: week01_ros_foundations" >&2; exit 2; }
    docker compose up -d
    docker compose exec course-ros course-lab "$lab"
    ;;
  stop) docker compose down ;;
  status) docker compose ps ;;
  *) echo "Usage: $0 {setup|start|build|lab LAB_DIRECTORY|stop|status}" >&2; exit 2 ;;
esac
