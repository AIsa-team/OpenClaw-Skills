#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <category> [--output <empty-directory>]" >&2
}

category="${1:-}"
shift || true

case "$category" in
  financial|search-research|social-media|ai-models|marketing|creative|platform) ;;
  *)
    usage
    echo "Unknown skill category: $category" >&2
    exit 2
    ;;
esac

if [[ ! -d "$category" ]]; then
  echo "Category directory does not exist: $category" >&2
  exit 3
fi

output_dir=""
if [[ $# -gt 0 ]]; then
  if [[ $# -ne 2 || "$1" != "--output" ]]; then
    usage
    exit 2
  fi
  output_dir="$2"
fi

export_category() {
  local destination="$1"
  mkdir -p "$destination"
  if [[ -n "$(find "$destination" -mindepth 1 -print -quit)" ]]; then
    echo "Output directory must be empty: $destination" >&2
    exit 4
  fi

  cp -a "$category"/. "$destination"/

  local skill_count
  skill_count="$(find "$destination" -mindepth 2 -maxdepth 2 -name SKILL.md -print | wc -l | tr -d ' ')"
  if [[ "$skill_count" == "0" ]]; then
    echo "Category export contains no skills: $category" >&2
    exit 5
  fi

  echo "Prepared $category release with $skill_count skills"
}

if [[ -n "$output_dir" ]]; then
  export_category "$output_dir"
  exit 0
fi

if [[ "${GITHUB_ACTIONS:-}" != "true" ]]; then
  echo "In-place export is restricted to GitHub Actions; use --output for local verification." >&2
  exit 6
fi

stage_dir="$(mktemp -d)"
trap 'rm -rf "$stage_dir"' EXIT
export_category "$stage_dir"

find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -a "$stage_dir"/. .
