# VAS-IFRS Document Ingestion Script
# Run from repo root: .\ingest.ps1
# Prereq: Qdrant running (docker-compose or standalone)
#
# Document layout:
#   ingestion/raw/shared/vas/{standards,circulars,decisions,adoption}/
#   ingestion/raw/shared/ifrs/{standards,ias,ifric,sic,framework,taxonomy}/
#   ingestion/raw/tenant/<tenant-id>/{fs,audit,contracts,internal}/

param(
    [ValidateSet("all", "shared", "vas", "ifrs", "tenant")]
    [string]$Scope = "shared",
    [string]$TenantId,
    [string]$OllamaUrl = "http://localhost:11434",
    [string]$QdrantUrl = "http://localhost:6333",
    [switch]$Recreate,               # drop and recreate collections
    [switch]$DryRun                  # chunk only, skip embed+upsert
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Backend    = Join-Path $Root "apps/backend"
$Ingestion  = Join-Path $Root "ingestion"
$BatchEmbed = Join-Path $Ingestion "pipelines/embedders/batch_embed.py"

if ($Scope -in @("tenant", "all")) {
    $ParsedTenantId = [Guid]::Empty
    if (-not [Guid]::TryParse($TenantId, [ref]$ParsedTenantId)) {
        throw "-TenantId must be a valid UUID for scope '$Scope'"
    }
    $TenantId = $ParsedTenantId.ToString()
}

# Load .env for API keys
$EnvFile = Join-Path $Backend ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([^#=]+)=(.*)$") {
            [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
        }
    }
    Write-Host "[OK] Loaded .env"
}

# PYTHONPATH: backend app.* + ingestion pipelines.*
$env:PYTHONPATH = "$Backend;$Ingestion"

$PythonCandidates = @(
    (Join-Path $Backend ".venv/Scripts/python.exe"),
    (Join-Path $Backend ".venv/bin/python")
)
$Python = $PythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Python) {
    $Python = "python"
}

function Ingest-Collection {
    param($DocsDir, $Collection, $CollScope, $TId = $null)

    if (-not (Test-Path $DocsDir)) {
        Write-Host "[SKIP] $DocsDir not found"
        return
    }

    $files = Get-ChildItem $DocsDir -Recurse -File -Include "*.pdf","*.docx","*.xlsx","*.txt","*.md"
    if ($files.Count -eq 0) {
        Write-Host "[SKIP] No documents in $DocsDir"
        return
    }

    Write-Host "`n==> $($files.Count) docs  $DocsDir  →  $Collection"

    $cmd = @(
        $Python, $BatchEmbed,
        "--docs", $DocsDir,
        "--collection", $Collection,
        "--scope", $CollScope,
        "--ollama-url", $OllamaUrl,
        "--qdrant-url", $QdrantUrl
    )
    if ($TId)           { $cmd += @("--tenant-id", $TId) }
    if ($Recreate)      { $cmd += "--recreate" }
    if ($DryRun)        { $cmd += "--dry-run" }

    & $cmd[0] $cmd[1..($cmd.Length-1)]
    if ($LASTEXITCODE -ne 0) {
        throw "Ingestion failed for $Collection (exit $LASTEXITCODE)"
    }
}

$Raw = Join-Path $Ingestion "raw"

switch ($Scope) {
    "vas" {
        Ingest-Collection "$Raw\shared\vas" "kb_shared_vas" "shared"
    }
    "ifrs" {
        Ingest-Collection "$Raw\shared\ifrs" "kb_shared_ifrs" "shared"
    }
    "tenant" {
        Ingest-Collection "$Raw\tenant\$TenantId" "tenant_$TenantId" "tenant" $TenantId
    }
    "shared" {
        Ingest-Collection "$Raw\shared\vas"        "kb_shared_vas"  "shared"
        Ingest-Collection "$Raw\shared\ifrs"       "kb_shared_ifrs" "shared"
    }
    "all" {
        Ingest-Collection "$Raw\shared\vas"        "kb_shared_vas"    "shared"
        Ingest-Collection "$Raw\shared\ifrs"       "kb_shared_ifrs"   "shared"
        Ingest-Collection "$Raw\tenant\$TenantId"  "tenant_$TenantId" "tenant" $TenantId
    }
}

Write-Host "`n[DONE] Ingestion complete."
