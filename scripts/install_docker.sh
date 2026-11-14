#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$project_dir/results/setup"
log_file="$project_dir/results/setup/docker-install-$(date -u +%Y%m%dT%H%M%SZ).log"
exec > >(tee -a "$log_file") 2>&1
trap 'echo "Installer failed at line $LINENO; inspect $log_file"' ERR
echo "Started $(date -u --iso-8601=seconds)"
echo "Official instructions: https://docs.docker.com/engine/install/ubuntu/"
. /etc/os-release
if [[ "$ID" != ubuntu || "$VERSION_CODENAME" != resolute ]]; then
  echo "This reviewed installer expects Ubuntu Resolute; inspect instructions for this OS."; exit 1
fi
for package in docker.io docker-compose docker-compose-v2 docker-doc docker-buildx podman-docker containerd runc; do
  if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -qx 'install ok installed'; then
    echo "Existing potentially conflicting package: $package. Review before replacement."; exit 1
  fi
done
sudo -v
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o "$project_dir/results/setup/docker.asc"
sudo install -m 0644 "$project_dir/results/setup/docker.asc" /etc/apt/keyrings/docker.asc
arch="$(dpkg --print-architecture)"
source_file="$project_dir/results/setup/docker.sources"
printf 'Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: %s
Components: stable
Architectures: %s
Signed-By: /etc/apt/keyrings/docker.asc
' "$VERSION_CODENAME" "$arch" > "$source_file"
if [[ -f /etc/apt/sources.list.d/docker.sources ]] && ! cmp -s "$source_file" /etc/apt/sources.list.d/docker.sources; then
  echo 'Existing Docker source differs; review before overwriting.'; exit 1
fi
sudo install -m 0644 "$source_file" /etc/apt/sources.list.d/docker.sources
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl start docker
sudo docker version
sudo docker run --rm hello-world
echo "Completed $(date -u --iso-8601=seconds)"
echo 'Docker installed. Container image download/validation is a separate next step.'
