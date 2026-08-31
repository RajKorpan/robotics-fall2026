# Shared ROS 2 Course Environment

Set this environment up **once** and reuse it for every ROS-based lab:

- Week 1 — ROS foundations
- Week 3 — motion, frames, and AI-assisted development
- Week 6 — SLAM and localization
- Week 8 — computer vision and learned perception
- Week 9 — planning and navigation
- Week 11 — HRI evaluation

Weeks 4, 5, 10, 12, and 14 are self-contained Python labs and do not require this container.

## What the container provides

The course image contains Ubuntu 24.04, ROS 2 Jazzy, TurtleBot3 simulation, Gazebo, RViz, TF tools, SLAM Toolbox, Navigation2, OpenCV/image tools, colcon, and the shared Streamlit/Python environment.

ROS, Gazebo, RViz, and the terminal run in one Linux container. A browser-based Linux desktop avoids different X11 instructions on Windows, macOS, and Linux:

```text
Browser
├── http://localhost:6080  Linux desktop, terminals, Gazebo, RViz
└── http://localhost:8501 Active lab's Streamlit guide
                         ↓
              shared ROS 2 Jazzy container
                         ↓
              repository mounted at /workspace
```

The ports bind only to `127.0.0.1`; the noVNC desktop is not exposed to the local network.

## Requirements

- A 64-bit Windows, macOS, or Linux computer with hardware virtualization enabled
- At least 8 GB RAM; 16 GB is recommended for Gazebo + RViz
- Approximately 12 GB free disk space for Docker, the image, and build artifacts
- Git
- Docker Desktop on Windows/macOS, or Docker Engine plus the Compose plugin on Linux

Docker Desktop supports Windows and both Intel and Apple-silicon Macs. On Windows, use the WSL 2 Linux-container backend. See the official [Windows WSL setup](https://docs.docker.com/desktop/features/wsl/), [Windows installation guide](https://docs.docker.com/desktop/setup/install/windows-install/), and [macOS installation guide](https://docs.docker.com/desktop/setup/install/mac-install/).

The image begins with the official multi-architecture `ros:jazzy-ros-base-noble` image, which is published for AMD64 and ARM64. This avoids AMD64 emulation on Apple silicon. See the official [ROS image tags](https://hub.docker.com/_/ros/tags).

## 1. Install Docker once

### Windows 10/11

1. Install current Windows updates.
2. In an Administrator PowerShell window, run `wsl --install`, then restart if requested.
3. Install Docker Desktop for Windows.
4. In Docker Desktop, select **Use the WSL 2 based engine** and **Linux containers**.
5. Start Docker Desktop and wait for the engine to report that it is running.
6. Verify in PowerShell:

```powershell
wsl --version
docker version
docker compose version
```

### macOS — Intel or Apple silicon

1. Install the Docker Desktop download matching the Mac's chip.
2. Start Docker Desktop and finish its first-run prompts.
3. Verify in Terminal:

```bash
docker version
docker compose version
```

### Linux

Install Docker Engine and the Docker Compose plugin using Docker's instructions for the distribution. Complete Docker's Linux post-install steps if commands should run without `sudo`. Verify:

```bash
docker version
docker compose version
```

Use Docker Engine on Linux rather than Docker Desktop unless the institution specifically manages Docker Desktop.

## 2. Clone the course repository once

```bash
git clone https://github.com/RajKorpan/robotics-fall2026.git
cd robotics-fall2026
```

If the repository is already cloned, update it before setup:

```bash
git pull
```

## 3. Build the environment and all ROS workspaces once

The first run downloads/builds a large image and compiles all six workspaces. It can take 15–45 minutes depending on the computer and network.

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ros_course.ps1 setup
```

macOS/Linux:

```bash
chmod +x scripts/ros_course.sh
./scripts/ros_course.sh setup
```

Successful setup ends with:

```text
All six ROS lab workspaces built successfully.
```

Open the desktop at:

```text
http://localhost:6080/vnc.html?autoconnect=1&resize=remote
```

## 4. Start a lab

Windows:

```powershell
.\scripts\ros_course.ps1 lab week01_ros_foundations
```

macOS/Linux:

```bash
./scripts/ros_course.sh lab week01_ros_foundations
```

This starts the lab guide on <http://localhost:8501> and opens a correctly sourced terminal in the browser desktop. Run the lab's ROS launch command from that terminal.

Replace the directory with the current ROS lab:

```text
week01_ros_foundations
week03_motion_frames_ai
week06_slam_localization
week08_vision_perception
week09_planning_navigation
week11_hri_evaluation
```

Each launcher assigns the lab a stable ROS domain and sources its built workspace. Do not run two Gazebo-based labs simultaneously.

## Everyday commands

| Task | Windows | macOS/Linux |
|---|---|---|
| Start container | `.\scripts\ros_course.ps1 start` | `./scripts/ros_course.sh start` |
| Open a lab | `.\scripts\ros_course.ps1 lab LAB` | `./scripts/ros_course.sh lab LAB` |
| Rebuild workspaces | `.\scripts\ros_course.ps1 build` | `./scripts/ros_course.sh build` |
| Show status | `.\scripts\ros_course.ps1 status` | `./scripts/ros_course.sh status` |
| Stop container | `.\scripts\ros_course.ps1 stop` | `./scripts/ros_course.sh stop` |

Stopping the container does not delete source, submissions, maps, evidence, or workspace build output because the repository is mounted from the host.

## Updating during the semester

After `git pull`, rebuild when package metadata, interfaces, or Docker files changed:

```powershell
.\scripts\ros_course.ps1 setup
```

or:

```bash
./scripts/ros_course.sh setup
```

Pure Python source changes in a symlink-built workspace usually do not require a rebuild, but running `build` is always safe.

## Troubleshooting

### Docker command cannot connect

Start Docker Desktop and wait for the engine. On Windows, confirm Docker is using Linux containers and WSL 2.

### Port 6080 or 8501 is already in use

Stop another course container or local Streamlit process, then run the course `stop` and `start` commands.

### Gazebo or RViz is slow

The default uses Mesa software rendering for consistent behavior across platforms. Close other memory-intensive applications and allocate more CPU/RAM to Docker Desktop. Native Ubuntu with hardware acceleration remains the supported performance fallback.

### Browser desktop is blank

Run the `status` command. If the container is running, refresh the noVNC URL. Otherwise run `stop`, then `start`.

### Rebuild only after source changes

Run the course `build` command. If package dependencies changed, rerun `setup` so the image is rebuilt.

### Reset the container without deleting coursework

```bash
docker compose down
docker compose up -d
```

Do not add `--volumes`, and do not delete the repository. Student work lives in the mounted repository.

## Instructor: publish instead of local builds

The image can be published for both architectures so students pull identical layers:

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -f docker/Dockerfile \
  -t ghcr.io/OWNER/robotics-fall2026:jazzy-v1 \
  --push .
```

Set `COURSE_ROS_IMAGE` to that tag before `docker compose up`. Pin a semester tag or digest; do not use an unversioned `latest` image for graded work. Validate Gazebo, RViz, TurtleBot3, SLAM, Nav2, OpenCV, and noVNC on Windows/AMD64, macOS/ARM64, and Linux/AMD64 before release.

