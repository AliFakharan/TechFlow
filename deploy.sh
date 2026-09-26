#!/usr/bin/env bash
# TechFlow — one-command deploy (run on the server, inside the project dir).
# Equivalent to: git pull && docker compose up -d --build
set -euo pipefail

echo "==> Pulling latest code"
git pull origin main

echo "==> Rebuilding and restarting containers"
docker compose up -d --build

echo "==> Cleaning up dangling images"
docker image prune -f

echo "==> Deployment finished"
docker compose ps
