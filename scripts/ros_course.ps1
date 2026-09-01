param(
    [Parameter(Position=0)]
    [ValidateSet("setup", "start", "build", "lab", "stop", "status")]
    [string]$Command = "start",
    [Parameter(Position=1)]
    [string]$Lab = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Assert-DockerSuccess([string]$Action) {
    if ($LASTEXITCODE -ne 0) { throw "Docker failed while $Action (exit code $LASTEXITCODE)." }
}

Push-Location $RepoRoot
try {
    switch ($Command) {
        "setup" {
            docker compose up -d --build
            Assert-DockerSuccess "building and starting the course environment"
            docker compose exec course-ros course-build-workspaces
            Assert-DockerSuccess "building the ROS lab workspaces"
            docker compose exec course-ros course-doctor
            Assert-DockerSuccess "checking the course environment"
            Write-Host "Setup complete. Open http://localhost:6080/vnc.html?autoconnect=1&resize=remote"
        }
        "start" { docker compose up -d; Assert-DockerSuccess "starting the course environment" }
        "build" { docker compose exec course-ros course-build-workspaces; Assert-DockerSuccess "building the ROS lab workspaces" }
        "lab" {
            if ([string]::IsNullOrWhiteSpace($Lab)) { throw "Provide a lab directory, for example: week01_ros_foundations" }
            docker compose up -d
            Assert-DockerSuccess "starting the course environment"
            docker compose exec course-ros course-lab $Lab
            Assert-DockerSuccess "starting $Lab"
        }
        "stop" { docker compose down; Assert-DockerSuccess "stopping the course environment" }
        "status" { docker compose ps; Assert-DockerSuccess "reading course environment status" }
    }
}
finally { Pop-Location }
