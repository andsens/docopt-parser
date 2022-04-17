#!/usr/bin/env bash

set -e

pip --disable-pip-version-check --no-cache-dir install --user poetry

mkdir -p "$HOME/.config/pypoetry"
cp .devcontainer/poetry-config.toml "$HOME/.config/pypoetry/config.toml"

poetry install
