#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd "$(dirname "$0")/.." && pwd)"
source_dir="$project_root/.cache/ff3-source"
source_commit="81f3bd921ffcb4ea84c19123d798fbcb830ee9e3"
if [ ! -d "$source_dir/.git" ]; then
  mkdir -p "$source_dir"
  git -C "$source_dir" init -q
  git -C "$source_dir" remote add origin https://github.com/bucheoncityboy/fama-french-integrated-research.git
  git -C "$source_dir" fetch --depth 1 origin "$source_commit"
  git -C "$source_dir" checkout --detach FETCH_HEAD
fi
cd "$project_root/korea-market/governance-extension"
python -m src.pipeline --source "$source_dir"
