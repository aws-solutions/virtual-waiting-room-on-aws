#!/bin/bash
# fail on medium or greater
# scan everything in the source folder
hawkeye scan -f medium -t /github/workspace/source
