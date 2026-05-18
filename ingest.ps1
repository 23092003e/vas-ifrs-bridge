# VAS-IFRS Document Ingestion Script
# Run from repo root: .\ingest.ps1
# Prereq: Qdrant running (docker-compose or standalone)
#
# Document layout:
#   ingestion/raw/shared/vas/{standards,circulars,decisions,adoption}/
#   ingestion/raw/shared/ifrs/{standards,ias,ifric,sic,framework,taxonomy}/
#   ingestion/raw/tenant/<tenant-id>/{fs,audit,contracts,internal}/

param(
    [string]$Scope = "all",          # all | vas | ifrs | tenant
    [string]$TenantId = "dev-tenant",
    [switch]$Recreate,               # drop and recreate collections
    [switch]$DryRun                  # chunk only, skip embed+upsert
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Backend    = Join-Path $Root "apps\backend"
$Ingestion  = Join-Path $Root "ingestion"
$BatchEmbed = Join-Path $Ingestion "pipelines\embedders\batch_embed.py"

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

$RecreateFlag = if ($Recreate) { "--recreate" } else { "" }
$DryRunFlag   = if ($DryRun)   { "--dry-run"  } else { "" }

function Ingest-Collection {
    param($DocsDir, $Collection, $CollScope, $TId = $null)

    if (-not (Test-Path $DocsDir)) {
        Write-Host "[SKIP] $DocsDir not found"
        return
    }

    $files = Get-ChildItem $DocsDir -Recurse -File -Include "*.pdf","*.docx","*.doc","*.xlsx","*.xls","*.txt","*.md"
    if ($files.Count -eq 0) {
        Write-Host "[SKIP] No documents in $DocsDir"
        return
    }

    Write-Host "`n==> $($files.Count) docs  $DocsDir  →  $Collection"

    $cmd = @("python", $BatchEmbed, "--docs", $DocsDir, "--collection", $Collection, "--scope", $CollScope)
    if ($TId)           { $cmd += @("--tenant-id", $TId) }
    if ($RecreateFlag)  { $cmd += $RecreateFlag }
    if ($DryRunFlag)    { $cmd += $DryRunFlag }

    & $cmd[0] $cmd[1..($cmd.Length-1)]
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Ingestion failed for $Collection (exit $LASTEXITCODE)"
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
    default {
        Ingest-Collection "$Raw\shared\vas"        "kb_shared_vas"    "shared"
        Ingest-Collection "$Raw\shared\ifrs"       "kb_shared_ifrs"   "shared"
        Ingest-Collection "$Raw\tenant\$TenantId"  "tenant_$TenantId" "tenant" $TenantId
    }
}

Write-Host "`n[DONE] Ingestion complete."
