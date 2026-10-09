#!/usr/bin/env bash
# Workers finish their current star, then wait. ./resume.sh to continue.
touch "$(dirname "$0")/PAUSE" && echo "paused (workers idle after their current star)"
