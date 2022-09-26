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
echo "template_dir" $template_dir
source_dir="$template_dir/../source"
echo "source_dir" $source_dir

echo "------------------------------------------------------------------------------"
echo " Test core API lambda functions"
echo "------------------------------------------------------------------------------"
cd $source_dir/core-api/lambda_functions
coverage run lambda_functions_tests.py
coverage xml
sed -i -- 's/filename\=\"/filename\=\"source\/core-api\/lambda_functions\//g' coverage.xml

echo "------------------------------------------------------------------------------"
echo " Test core API custom resources functions"
echo "------------------------------------------------------------------------------"
cd $source_dir/core-api/custom_resources
coverage run custom_resource_tests.py
coverage xml
sed -i -- 's/filename\=\"/filename\=\"source\/core-api\/custom_resources\//g' coverage.xml

echo "------------------------------------------------------------------------------"

echo " Test shared resources functions"
echo "------------------------------------------------------------------------------"
cd $source_dir/shared/
coverage run shared_resources_tests.py
coverage xml
sed -i -- 's/filename\=\"/filename\=\"source\/shared\//g' coverage.xml

echo "------------------------------------------------------------------------------"
echo " Test open-id waitingroom custom resources functions"
echo "------------------------------------------------------------------------------"
cd $source_dir/openid-waitingroom/custom_resources
coverage run custom_resources_tests.py
coverage xml
sed -i -- 's/filename\=\"/filename\=\"source\/openid-waitingroom\/custom_resources\//g' coverage.xml

echo " Test inlet strategy Lambda functions"
echo "------------------------------------------------------------------------------"
cd $source_dir/sample-inlet-strategies
coverage run inlet_strategy_tests.py
coverage xml
sed -i -- 's/filename\=\"/filename\=\"source\/sample-inlet-strategies\//g' coverage.xml

echo "------------------------------------------------------------------------------"
echo " Test token authorizer Lambda functions"
echo "------------------------------------------------------------------------------"
cd $source_dir/token-authorizer/chalice
coverage run token_authorizer_tests.py
coverage xml
sed -i -- 's/filename\=\"/filename\=\"source\/token-authorizer\/chalice\//g' coverage.xml
