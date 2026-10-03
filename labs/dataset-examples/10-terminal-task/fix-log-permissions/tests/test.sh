#!/bin/bash
# Verifier entry point: run the checks and write the reward file the harness reads.
mkdir -p /logs/verifier
if python3 -m pytest -q "$(dirname "$0")/test_outputs.py"; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
