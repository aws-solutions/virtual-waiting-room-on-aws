#!/bin/bash
#
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned
#
# This script should be run from the repo's deployment directory
# cd deployment
# ./run-unit-tests.sh
#

# Get reference for all important folders
template_dir="$PWD"
source_dir="$template_dir/../source"

echo "------------------------------------------------------------------------------"
echo " Test core API functions"
echo "------------------------------------------------------------------------------"
cd $source_dir/core-api/lambda_functions
coverage run lambda_functions_tests.py
coverage xml

echo "------------------------------------------------------------------------------"
echo " Test core API custom resources functions"
echo "------------------------------------------------------------------------------"
cd $source_dir/core-api/custom_resources
coverage run custom_resource_tests.py
coverage xml