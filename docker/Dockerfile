FROM ros:jazzy-ros-base-noble

SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=jazzy \
    TURTLEBOT3_MODEL=burger \
    DISPLAY=:1 \
    QT_X11_NO_MITSHM=1 \
    LIBGL_ALWAYS_SOFTWARE=1 \
    GALLIUM_DRIVER=llvmpipe \
    PATH=/opt/course-venv/bin:$PATH \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    dbus-x11 \
    fluxbox \
    git \
    mesa-utils \
    novnc \
    python3-colcon-common-extensions \
    python3-numpy \
    python3-opencv \
    python3-pip \
    python3-rosdep \
    python3-venv \
    ros-jazzy-cv-bridge \
    ros-jazzy-desktop \
    ros-jazzy-image-publisher \
    ros-jazzy-image-view \
    ros-jazzy-nav2-bringup \
    ros-jazzy-navigation2 \
    ros-jazzy-rmw-fastrtps-cpp \
    ros-jazzy-rosidl-default-generators \
    ros-jazzy-slam-toolbox \
    ros-jazzy-tf2-tools \
    ros-jazzy-turtlebot3-gazebo \
    ros-jazzy-turtlebot3-navigation2 \
    ros-jazzy-turtlebot3-teleop \
    websockify \
    x11vnc \
    x11-utils \
    xterm \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY docker/requirements.txt /tmp/course-requirements.txt
RUN python3 -m venv --system-site-packages /opt/course-venv \
    && /opt/course-venv/bin/python -m pip install --no-cache-dir --upgrade pip \
    && /opt/course-venv/bin/python -m pip install --no-cache-dir -r /tmp/course-requirements.txt

RUN existing_user="$(getent passwd 1000 | cut -d: -f1)" \
    && if [[ -n "$existing_user" && "$existing_user" != "student" ]]; then \
         usermod --login student --home /home/student --move-home "$existing_user"; \
       elif [[ -z "$existing_user" ]]; then \
         useradd --create-home --uid 1000 --shell /bin/bash student; \
       fi \
    && mkdir -p /workspace /home/student/.fluxbox \
    && chown -R "student:$(id -gn student)" /workspace /home/student

COPY docker/scripts/course-desktop /usr/local/bin/course-desktop
COPY docker/scripts/course-build-workspaces /usr/local/bin/course-build-workspaces
COPY docker/scripts/course-doctor /usr/local/bin/course-doctor
COPY docker/scripts/course-lab /usr/local/bin/course-lab
RUN chmod +x /usr/local/bin/course-desktop /usr/local/bin/course-build-workspaces /usr/local/bin/course-doctor /usr/local/bin/course-lab

USER student
WORKDIR /workspace
EXPOSE 6080 8501
ENTRYPOINT ["/usr/local/bin/course-desktop"]
