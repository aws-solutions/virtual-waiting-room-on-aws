#!/bin/bash
#
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned
#
# This script should be run from the repo's deployment directory
# cd deployment
# ./run-unit-tests.sh
#


# configure the environment
VENV=$(mktemp -d) && echo "$VENV"
python3 -m venv "$VENV"
source "$VENV"/bin/activate

# Install the common package into the virtual envronment before running
pip install ./pkg/virtual_waiting_room_on_aws_common-1.1.7-py3-none-any.whl || pip install -e ./../source/shared/virtual-waiting-room-on-aws-common
cd ./../deployment

# install dependencies
pip install -r requirements.txt

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
echo " Test shared custom resources functions"
echo "------------------------------------------------------------------------------"
cd $source_dir/shared/
coverage run shared_resources_tests.py
coverage xml
sed -i -- 's/filename\=\"/filename\=\"source\/shared\//g' coverage.xml

echo "------------------------------------------------------------------------------"
echo " Test shared common functions"
echo "------------------------------------------------------------------------------"
cd $source_dir/shared/virtual-waiting-room-on-aws-common
coverage run common_tests.py
coverage xml
sed -i -- 's/filename\=\"/filename\=\"source\/shared\/virtual-waiting-room-on-aws-common\//g' coverage.xml

echo "------------------------------------------------------------------------------"
echo " Test open-id API functions"
echo "------------------------------------------------------------------------------"
cd $source_dir/openid-waitingroom/chalice
coverage run openid_waitingroom_tests.py
coverage xml
sed -i -- 's/filename\=\"/filename\=\"source\/openid-waitingroom\/chalice\//g' coverage.xml

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

echo "------------------------------------------------------------------------------"
echo " Test sample API functions"
echo "------------------------------------------------------------------------------"
cd $source_dir/core-api-authorizers-sample/chalice
coverage run sample_api_tests.py
coverage xml
sed -i -- 's/filename\=\"/filename\=\"source\/core-api-authorizers-sample\/chalice\//g' coverage.xml
