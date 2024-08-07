#!/bin/sh

target_dir="../source/python/lib/python3.12/"

if [ ! -f Dockerfile ]; then
    echo "*** Dockerfile is not here, are you in the right place? ***"
else
    docker build -t jwcrypto .
    docker run --name jwc --rm -dit jwcrypto
    docker cp jwc:site-packages/ $target_dir
    docker container stop jwc
fi
