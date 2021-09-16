#!/bin/sh

if [ ! -f Dockerfile ]; then
    echo "*** Dockerfile is not here, are you in the right place? ***"
else
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 279216907423.dkr.ecr.us-east-1.amazonaws.com
    docker build -t aws-virtual-waiting-room-webserver .
    docker tag aws-virtual-waiting-room-webserver:latest 279216907423.dkr.ecr.us-east-1.amazonaws.com/aws-virtual-waiting-room-webserver:latest
    docker push 279216907423.dkr.ecr.us-east-1.amazonaws.com/aws-virtual-waiting-room-webserver:latest
fi
