#!/bin/bash
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
# get_freerouting.sh : download Freerouting 1.9.0 (GPL-3.0, not part of this repo) to tools/freerouting.jar
# route.py uses tools/freerouting.jar, or the path in $FREEROUTING_JAR.
set -e
D="$(cd "$(dirname "$0")" && pwd)"
curl -fL -o "$D/freerouting.jar" https://github.com/freerouting/freerouting/releases/download/v1.9.0/freerouting-1.9.0.jar
ls -la "$D/freerouting.jar"
