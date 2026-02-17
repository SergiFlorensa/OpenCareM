param(
    [switch]$InstallRequirements,
    [switch]$RunAllFiles
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$PythonExe = Join-Path $RepoRoot 'venv\Scripts\python.exe'
if (-not (Test-Path $PythonExe)) {
    $PythonExe = 'python'
}

function Invoke-Step {
    param(
        [string]$Label,
        [scriptblock]$Command
    )

    Write-Host "==> $Label"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Label (exit code $LASTEXITCODE)"
    }
}

if ($InstallRequirements) {
    Invoke-Step 'pip install -r requirements.txt' {
        & $PythonExe -m pip install -r requirements.txt
    }
}

if (-not (Test-Path '.pre-commit-config.yaml')) {
    throw '.pre-commit-config.yaml not found. Configure hooks before running setup.'
}

Invoke-Step 'install pre-commit tool' {
    & $PythonExe -m pip install pre-commit
}

Invoke-Step 'install pre-commit hook' {
    & $PythonExe -m pre_commit install
}

Invoke-Step 'install pre-commit hook environments' {
    & $PythonExe -m pre_commit install-hooks
}

Invoke-Step 'validate pre-commit config' {
    & $PythonExe -m pre_commit validate-config
}

if ($RunAllFiles) {
    Invoke-Step 'run pre-commit on all files' {
        & $PythonExe -m pre_commit run --all-files
    }
}