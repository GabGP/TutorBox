#!/usr/bin/env bash
# Utz'tutor — install what is needed to run the playbooks in this folder: uv and Ansible.
# Needs internet. Safe to run again.
#
#   ./infra/ansible/bootstrap.sh
#
# Everything goes under the current user's home (~/.local); nothing needs sudo.
set -euo pipefail

UV_VERSION=0.12.13
ANSIBLE_CORE_VERSION=2.19.14

export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null; then
    echo "Installing uv $UV_VERSION..."
    curl -LsSf "https://astral.sh/uv/$UV_VERSION/install.sh" | sh
fi

echo "Installing ansible-core $ANSIBLE_CORE_VERSION..."
uv tool install "ansible-core==$ANSIBLE_CORE_VERSION"

echo
ansible --version | head -1
echo "Next: cp kit.example.yml kit.yml, edit it, then ansible-playbook jetson.yml --check --diff"
