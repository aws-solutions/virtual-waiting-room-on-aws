#!/bin/sh

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

DIR=/tmp/packages
mkdir -p $DIR
docker run -it -v $DIR:$DIR python:3.8 bash

# make sure you're pulling the x86/64 image
# cd /tmp/packages
# pip download jwcrypto
# unzip all whl files
# remove all whl files
# copy unzipped archives to vendor/ folder
