#!/bin/bash

# Set the base directory for NVIDIA packages within the virtual environment using wildcard for Python version
NVIDIA_PACKAGE_DIR="$VIRTUAL_ENV/lib/python*/site-packages/nvidia"
# Export LD_LIBRARY_PATH for each lib directory found in the NVIDIA_PACKAGE_DIR
for dir in $NVIDIA_PACKAGE_DIR/*; do
    if [ -d "$dir/lib" ]; then
        export LD_LIBRARY_PATH="$dir/lib:$LD_LIBRARY_PATH"
    fi
done

