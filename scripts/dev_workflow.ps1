param(
    [ValidateSet('dev', 'build', 'check', 'test', 'test-e2e', 'all')]
    [string]$Action = 'check'
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

function Run-Check {
    Invoke-Step 'ruff check' { & $PythonExe -m ruff check app mcp_server }
    Invoke-Step 'black --check' { & $PythonExe -m black --check app mcp_server }
    Invoke-Step 'mypy' { & $PythonExe -m mypy app mcp_server }
}

function Run-Test {
    Invoke-Step 'pytest -q' { & $PythonExe -m pytest -q }
}

function Run-TestE2E {
    Invoke-Step 'pytest chat e2e' {
        & $PythonExe -m pytest -q app/tests/test_clinical_chat_operational.py app/tests/test_care_tasks_api.py -k chat
    }
}

function Run-Build {
    $FrontendPath = Join-Path $RepoRoot 'frontend'
    if (-not (Test-Path (Join-Path $FrontendPath 'package.json'))) {
        throw 'frontend/package.json not found. Cannot run build.'
    }

    Invoke-Step 'frontend build' {
        Push-Location $FrontendPath
        try {
            npm run build
        }
        finally {
            Pop-Location
        }
    }
}

switch ($Action) {
    'dev' {
        Invoke-Step 'uvicorn dev server' { & $PythonExe -m uvicorn app.main:app --reload }
    }
    'build' {
        Run-Build
    }
    'check' {
        Run-Check
    }
    'test' {
        Run-Test
    }
    'test-e2e' {
        Run-TestE2E
    }
    'all' {
        Run-Check
        Run-Test
        Run-TestE2E
        Run-Build
    }
}