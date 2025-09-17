#!/bin/sh

target_dir="../source/python/lib/python3.12/"

if [ ! -f Dockerfile ]; then
    echo "*** Dockerfile is not here, are you in the right place? ***"
else
    # Build for x86_64/amd64 platform to match Lambda runtime
    docker build --platform linux/amd64 -t jwcrypto .
    docker run --platform linux/amd64 --name jwc -dit jwcrypto
    docker cp jwc:site-packages/ $target_dir
    docker container stop jwc
    docker container rm jwc
fi
