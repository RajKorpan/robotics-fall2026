param(
    [Parameter(Position=0)]
    [ValidateSet("setup", "start", "build", "lab", "stop", "status")]
    [string]$Command = "start",
    [Parameter(Position=1)]
    [string]$Lab = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $RepoRoot
try {
    switch ($Command) {
        "setup" {
            docker compose up -d --build
            docker compose exec course-ros course-build-workspaces
            docker compose exec course-ros course-doctor
            Write-Host "Setup complete. Open http://localhost:6080/vnc.html?autoconnect=1&resize=remote"
        }
        "start" { docker compose up -d }
        "build" { docker compose exec course-ros course-build-workspaces }
        "lab" {
            if ([string]::IsNullOrWhiteSpace($Lab)) { throw "Provide a lab directory, for example: week01_ros_foundations" }
            docker compose up -d
            docker compose exec course-ros course-lab $Lab
        }
        "stop" { docker compose down }
        "status" { docker compose ps }
    }
}
finally { Pop-Location }
