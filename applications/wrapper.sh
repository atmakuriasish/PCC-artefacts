#!/bin/bash


CPUS=(0 2)  # Cores to use
APPS=("bfs")
DATASET="Kronecker_25/"

for cpu in "${CPUS[@]}"; do
  for app in "${APPS[@]}"; do
    # Launch in background with CPU-specific output
    sudo python3 go.py -x single_thread_pcc -cpu "$cpu" &
  done
done

