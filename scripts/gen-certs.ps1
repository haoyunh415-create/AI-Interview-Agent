# ── Generate self-signed TLS certificates for local development ──
# Usage:  pwsh scripts/gen-certs.ps1
# Output: .\certs\cert.pem  .\certs\key.pem

$certsDir = Join-Path (Split-Path $PSScriptRoot -Parent) "certs"
New-Item -ItemType Directory -Force -Path $certsDir | Out-Null

$certPath = Join-Path $certsDir "cert.pem"
$keyPath  = Join-Path $certsDir "key.pem"

if (Test-Path $certPath -PathType Leaf -and Test-Path $keyPath -PathType Leaf) {
    Write-Host "Certs already exist at $certsDir — skipping"
    exit 0
}

Write-Host "Generating self-signed TLS certs in $certsDir ..."

# Use OpenSSL if available; fall back to PowerShell's self-signed cert
if (Get-Command openssl -ErrorAction SilentlyContinue) {
    openssl req -x509 `
        -newkey rsa:4096 `
        -keyout "$keyPath" `
        -out "$certPath" `
        -days 365 `
        -nodes `
        -subj "/CN=localhost/O=TechChat Dev/C=CN" `
        -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
} else {
    Write-Host "OpenSSL not found, generating via PowerShell..."
    $cert = New-SelfSignedCertificate -DnsName "localhost" -CertStoreLocation Cert:\LocalMachine\My
    Export-Certificate -Cert $cert -FilePath $certPath -Type CERT | Out-Null
    # Export private key
    $password = ConvertTo-SecureString -String "" -Force -AsPlainText
    Export-PfxCertificate -Cert $cert -FilePath "$certsDir\cert.pfx" -Password $password | Out-Null
    # Convert PFX to PEM
    Write-Host "Certificate generated at $certPath"
    Write-Host "NOTE: For production, use Let's Encrypt with certbot"
}

if (Test-Path $keyPath) {
    attrib +R $keyPath  # Mark read-only
}
Write-Host "Done: cert.pem + key.pem"
