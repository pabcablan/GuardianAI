$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Uvicorn = Join-Path $Root ".venv\Scripts\uvicorn.exe"

if (-not (Test-Path $Python)) {
    throw "Python virtual environment not found at $Python"
}

if (-not (Test-Path $Uvicorn)) {
    throw "Uvicorn executable not found at $Uvicorn"
}

function Start-GuardianService {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Title,

        [Parameter(Mandatory = $true)]
        [string] $WorkingDirectory,

        [Parameter(Mandatory = $true)]
        [string] $Executable,

        [Parameter(Mandatory = $true)]
        [string[]] $ExecutableArguments
    )

    $FullWorkingDirectory = Join-Path $Root $WorkingDirectory
    if (-not (Test-Path $FullWorkingDirectory)) {
        throw "Working directory not found: $FullWorkingDirectory"
    }

    $SafeTitle = $Title.Replace("'", "''")
    $SafeExecutable = $Executable.Replace("'", "''")
    $SafeArguments = ($ExecutableArguments | ForEach-Object {
        "'$($_.Replace("'", "''"))'"
    }) -join " "
    $Command = "Write-Host '$SafeTitle'; & '$SafeExecutable' $SafeArguments"

    Start-Process `
        -FilePath "powershell.exe" `
        -WorkingDirectory $FullWorkingDirectory `
        -ArgumentList @(
            "-NoProfile",
            "-NoExit",
            "-Command",
            $Command
        )
}

if (Test-Path (Join-Path $Root "model-provider\main.py")) {
    Start-GuardianService `
        -Title "GuardianAI model-provider - http://127.0.0.1:8006" `
        -WorkingDirectory "model-provider" `
        -Executable $Uvicorn `
        -ExecutableArguments @("main:app", "--host", "127.0.0.1", "--port", "8006")
} else {
    Write-Host "GuardianAI model-provider skipped: model-provider\main.py not found."
}

Start-GuardianService `
    -Title "GuardianAI privacy-shield - http://127.0.0.1:8002" `
    -WorkingDirectory "privacy-shield" `
    -Executable $Uvicorn `
    -ExecutableArguments @("main:app", "--host", "127.0.0.1", "--port", "8002")

Start-GuardianService `
    -Title "GuardianAI document-processor - http://127.0.0.1:8001" `
    -WorkingDirectory "document-processor" `
    -Executable $Uvicorn `
    -ExecutableArguments @("main:app", "--host", "127.0.0.1", "--port", "8001", "--reload")

Start-GuardianService `
    -Title "GuardianAI orchestrator - http://127.0.0.1:8003" `
    -WorkingDirectory "orchestrator" `
    -Executable $Uvicorn `
    -ExecutableArguments @("main:app", "--host", "127.0.0.1", "--port", "8003", "--reload")

Start-GuardianService `
    -Title "GuardianAI web-ui backend - http://127.0.0.1:8000" `
    -WorkingDirectory "web-ui" `
    -Executable $Uvicorn `
    -ExecutableArguments @("main:app", "--host", "127.0.0.1", "--port", "8000", "--reload")

Start-GuardianService `
    -Title "GuardianAI web-ui frontend - http://127.0.0.1:5173" `
    -WorkingDirectory "web-ui\infrastructure\adapters\frontend" `
    -Executable "npm.cmd" `
    -ExecutableArguments @("run", "dev")

Write-Host "GuardianAI services are starting in separate PowerShell windows."
Write-Host "Close those windows to stop each service."
