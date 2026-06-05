#!/usr/bin/env bash
# ── Generate self-signed TLS certificates for local development ──
# Usage:  bash scripts/gen-certs.sh
# Output: ./certs/cert.pem  ./certs/key.pem

set -euo pipefail

DIR="$(cd "$(dirname "$0")/../certs" && pwd)"
mkdir -p "$DIR"

if [[ -f "$DIR/cert.pem" && -f "$DIR/key.pem" ]]; then
    echo "Certs already exist at $DIR/ — skipping"
    exit 0
fi

echo "Generating self-signed TLS certs in $DIR/ ..."
openssl req -x509 \
    -newkey rsa:4096 \
    -keyout "$DIR/key.pem" \
    -out "$DIR/cert.pem" \
    -days 365 \
    -nodes \
    -subj "/CN=localhost/O=TechChat Dev/C=CN" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$DIR/key.pem"
echo "Done: cert.pem + key.pem"
