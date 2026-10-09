#!/usr/bin/env bash
# Serve report.html + candidates/ on the home LAN: http://192.168.1.161:8765/report.html
cd "$(dirname "$0")/.." && exec python3 -m http.server 8765 --bind 0.0.0.0
