#!/bin/bash
#
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned
#
# This script should be run from the repo's deployment directory
# cd deployment
# ./build-s3-dist.sh source-bucket-base-name solution-name version-code
#
# Paramenters:
#  - source-bucket-base-name: Name for the S3 bucket location where the template will source the Lambda
#    code from. The template will append '-[region_name]' to this bucket name.
#    For example: ./build-s3-dist.sh solutions v1.0.0
#    The template will then expect the source code to be located in the solutions-[region_name] bucket
#
#  - solution-name: name of the solution for consistency
#
#  - version-code: version of the package

set -euo pipefail

# only option h is allowed to display help message
while getopts ':h' OPTION; do
  case "$OPTION" in
    h)
      echo
      echo "script usage: $(basename $0) DIST_OUTPUT_BUCKET SOLUTION_NAME VERSION"
      echo "example usage: ./$(basename $0) mybucket aws-virtual-waiting-room v1.0.0"
      echo
      echo "If no arguments are passed in, the following default values are used:"
      echo "DIST_OUTPUT_BUCKET=rodeolabz"
      echo "SOLUTION_NAME=aws-virtual-waiting-room"
      echo "VERSION=v1.0.0"
      echo
      echo "You may export export these variables in your environment and call the script using those variables:"
      echo "./$(basename $0) \$DIST_OUTPUT_BUCKET \$SOLUTION_NAME \$VERSION"
      echo 
      exit 1
      ;;
    ?)
      echo "script usage: $(basename $0) DIST_OUTPUT_BUCKET SOLUTION_NAME VERSION"
      exit 1
      ;;
  esac
done

ORIGIN=`pwd`
DIST_OUTPUT_BUCKET="$1" 
SOLUTION_NAME="$2"
VERSION="$3"
TIMESTAMP=`date +'%s'`

# Set defaults if variables are not set:
if [ -z "$1" ]
  then
    echo "Setting default base source bucket name to rodeolabz."
    DIST_OUTPUT_BUCKET='rodeolabz'
fi
if [ -z "$2" ] 
  then
    echo "Setting default solution name to aws-virtual-waiting-room."
    SOLUTION_NAME='aws-virtual-waiting-room'
fi

if [ -z "$3" ]
  then
    echo "Setting default version to v1.0.0"
    VERSION='v1.0.0'
fi

template_dir="$PWD" # /deployment
template_dist_dir="$template_dir/global-s3-assets"
build_dist_dir="$template_dir/regional-s3-assets"
pkg_dir="$template_dir/pkg"
source_dir="$template_dir/../source"

echo "------------------------------------------------------------------------------"
echo "[Init] Clean old dist, node_modules and bower_components folders"
echo "------------------------------------------------------------------------------"
echo "rm -rf $template_dist_dir"
rm -rf $template_dist_dir
echo "mkdir -p $template_dist_dir"
mkdir -p $template_dist_dir
echo "rm -rf $build_dist_dir"
rm -rf $build_dist_dir
echo "mkdir -p $build_dist_dir"
mkdir -p $build_dist_dir
echo "rm -rf $pkg_dir"
rm -rf $pkg_dir
echo "mkdir -p $pkg_dir"
mkdir -p $pkg_dir


echo "------------------------------------------------------------------------------"
echo "aws-virtual-waiting-room-common package"
echo "------------------------------------------------------------------------------"
cd $source_dir/shared/aws-virtual-waiting-room-common
python -m build -o $pkg_dir


echo "------------------------------------------------------------------------------"
echo "Redis layer"
echo "------------------------------------------------------------------------------"
# build the redis layer Zip file
layer_dir=$source_dir/python/lib/python3.8/site-packages/
mkdir -p $layer_dir
cd $source_dir
rm -rf error.txt
pip install --upgrade --force-reinstall -t $layer_dir redis 2> error.txt
RETVAL=$?
if [ "$RETVAL" -ne "0" ]; then
    echo "ERROR: System package installation failed."
    cat error.txt
    exit $RETVAL
fi
zip -r aws-virtual-waiting-room-redis-layer-$TIMESTAMP.zip python/
mv aws-virtual-waiting-room-redis-layer-$TIMESTAMP.zip $build_dist_dir
rm -rf $layer_dir/*

echo "------------------------------------------------------------------------------"
echo "JWCrypto layer"
echo "------------------------------------------------------------------------------"
cd $template_dir
./docker_build.sh
cd $source_dir
zip -r aws-virtual-waiting-room-jwcrypto-layer-$TIMESTAMP.zip python/
mv aws-virtual-waiting-room-jwcrypto-layer-$TIMESTAMP.zip $build_dist_dir

# clean up the entire site-packages/layer dir
rm -rf python

echo "------------------------------------------------------------------------------"
echo "Core API"
echo "------------------------------------------------------------------------------"
# dependencies for custom lambda
cd $source_dir/core-api/custom_resources
rm -rf error.txt package
mkdir package
pip install --upgrade --force-reinstall --target ./package -r requirements.txt 2> error.txt
RETVAL=$?
if [ "$RETVAL" -ne "0" ]; then
    echo "ERROR: System package installation failed."
    cat error.txt
    exit $RETVAL
fi
cd package
zip -r9 ../aws-virtual-waiting-room-custom-resources-$TIMESTAMP.zip .
cd ../
zip -g aws-virtual-waiting-room-custom-resources-$TIMESTAMP.zip *.py
mv aws-virtual-waiting-room-custom-resources-$TIMESTAMP.zip $build_dist_dir

# zip up all the lambdas and copy them over to the build_dist_dir
cd $source_dir/core-api/lambda_functions
rm -rf error.txt package
mkdir package
pip install $pkg_dir/aws_virtual_waiting_room_common-1.0.0-py3-none-any.whl --target ./package
cd package
zip -r9 ../deployment.zip .
cd ../
zip -g deployment.zip *.py
mv deployment.zip $build_dist_dir/aws-virtual-waiting-room-$TIMESTAMP.zip

echo "------------------------------------------------------------------------------"
echo "Open ID adapter"
echo "------------------------------------------------------------------------------"
# OPEN ID LAMBDAS and TEMPLATES
# build custom resources
cd $source_dir/openid-waitingroom/custom_resources
rm -rf error.txt package tmp
mkdir -p package
mkdir -p tmp
pip install --upgrade --force-reinstall --target ./package -r requirements.txt 2> error.txt
RETVAL=$?
if [ "$RETVAL" -ne "0" ]; then
    echo exit code $RETVAL
    cat error.txt
    exit $RETVAL
fi
cd package
zip -r9 ../tmp/aws-virtual-waiting-room-openid-custom-resources.zip .
cd ..
zip -g tmp/aws-virtual-waiting-room-openid-custom-resources.zip generate_client_secret.py generate_redirect_uris_secret.py
# add shared custom resources
cd $source_dir/shared/custom_resources
zip -g $source_dir/openid-waitingroom/custom_resources/tmp/aws-virtual-waiting-room-openid-custom-resources.zip cfn_bucket_loader.py
# add Open ID web content to custom resource zip
cd $source_dir/openid-waitingroom
zip -g $source_dir/openid-waitingroom/custom_resources/tmp/aws-virtual-waiting-room-openid-custom-resources.zip www/*

cd $source_dir/openid-waitingroom/custom_resources
# copy the zip file to the build directory
cp tmp/aws-virtual-waiting-room-openid-custom-resources.zip $build_dist_dir/aws-virtual-waiting-room-openid-custom-resources-$TIMESTAMP.zip

# build chalice resources
cd $source_dir/openid-waitingroom/chalice
rm -rf tmp
mkdir -p tmp
# install the common package into vendor
rm -rf vendor
mkdir -p vendor
pip install $pkg_dir/aws_virtual_waiting_room_common-1.0.0-py3-none-any.whl --target vendor
# generate the template and zip
chalice package --merge-template merge_template.json tmp/
RETVAL=$?
if [ "$RETVAL" != "0" ]; then
    echo exit code $RETVAL
    exit $RETVAL
fi

# move build artifacts
mv -f tmp/sam.json $template_dir/aws-virtual-waiting-room-openid.json
mv -f tmp/deployment.zip $build_dist_dir/aws-virtual-waiting-room-openid-$TIMESTAMP.zip


echo "------------------------------------------------------------------------------"
echo "API Gateway authorizers"
echo "------------------------------------------------------------------------------"
# API GATEWAY AUTHORIZERS
# create SAM package
cd $source_dir/token-authorizer/chalice
rm -rf tmp
mkdir -p tmp/
# install the common package into vendor
rm -rf vendor
mkdir -p vendor
pip install $pkg_dir/aws_virtual_waiting_room_common-1.0.0-py3-none-any.whl --target vendor
# generate the template and zip
chalice package --merge-template merge_template.json tmp/
RETVAL=$?
if [ "$RETVAL" != "0" ]; then
    echo exit code $RETVAL
    exit $RETVAL
fi

# move build artifacts
mv -f tmp/sam.json $template_dir/aws-virtual-waiting-room-authorizers.json
mv -f tmp/deployment.zip $build_dist_dir/aws-virtual-waiting-room-authorizers-$TIMESTAMP.zip


echo "------------------------------------------------------------------------------"
echo "Core API and API Gateway sample code"
echo "------------------------------------------------------------------------------"
# SAMPLE CODE for CORE and API GATEWAY
# build custom resources
cd $source_dir/core-api-authorizers-sample/custom_resources
rm -rf error.txt package tmp
mkdir -p package
mkdir -p tmp
pip install --upgrade --force-reinstall --target ./package -r requirements.txt 2> error.txt
RETVAL=$?
if [ "$RETVAL" -ne "0" ]; then
    echo exit code $RETVAL
    cat error.txt
    exit $RETVAL
fi
cd package
zip -r9 ../tmp/aws-virtual-waiting-room-sample-custom-resources.zip .
# add shared custom resources
cd $source_dir/shared/custom_resources
zip -g $source_dir/core-api-authorizers-sample/custom_resources/tmp/aws-virtual-waiting-room-sample-custom-resources.zip cfn_bucket_loader.py
# add sample web content to custom resource zip
cd $source_dir/core-api-authorizers-sample
zip -r -g $source_dir/core-api-authorizers-sample/custom_resources/tmp/aws-virtual-waiting-room-sample-custom-resources.zip www/*

# build vue control panel and package into dist
cd $source_dir/control-panel
rm -rf dist/ node_modules/
npm install
npm run build
# add dist files to the custom resources zip 
cd dist/
zip -r -g $source_dir/core-api-authorizers-sample/custom_resources/tmp/aws-virtual-waiting-room-sample-custom-resources.zip www/*


cd $source_dir/core-api-authorizers-sample/custom_resources/tmp
# copy the zip file to the build directory
cp aws-virtual-waiting-room-sample-custom-resources.zip $build_dist_dir/aws-virtual-waiting-room-sample-custom-resources-$TIMESTAMP.zip


# create SAM package
cd $source_dir/core-api-authorizers-sample/chalice
rm -rf tmp
mkdir -p tmp/
chalice package --merge-template merge_template.json tmp/
RETVAL=$?
if [ "$RETVAL" != "0" ]; then
    echo exit code $RETVAL
    exit $RETVAL
fi

# move build artifacts
cd $source_dir/core-api-authorizers-sample/chalice
mv -f tmp/sam.json $template_dir/aws-virtual-waiting-room-sample.json
mv -f tmp/deployment.zip $build_dist_dir/aws-virtual-waiting-room-sample-$TIMESTAMP.zip


echo "------------------------------------------------------------------------------"
echo "Sample inlet strategies"
echo "------------------------------------------------------------------------------"
cd $source_dir/sample-inlet-strategies
rm -rf error.txt package
mkdir -p package
pip install --upgrade --force-reinstall --target ./package -r requirements.txt 2> error.txt
RETVAL=$?
if [ "$RETVAL" -ne "0" ]; then
    echo exit code $RETVAL
    cat error.txt
    exit $RETVAL
fi
cd package
zip -r9 ../aws-virtual-waiting-room-sample-inlet-strategies.zip .
cd ..
zip -g aws-virtual-waiting-room-sample-inlet-strategies.zip periodic_inlet.py max_size_inlet.py
mv aws-virtual-waiting-room-sample-inlet-strategies.zip $build_dist_dir/aws-virtual-waiting-room-sample-inlet-strategies-$TIMESTAMP.zip


echo "------------------------------------------------------------------------------"
echo "[Packing] Templates"
echo "------------------------------------------------------------------------------"

# copy all *.json to *.template
cd $template_dir
for f in *aws-virtual-waiting-room*.json; do
    cp -- "$f" "$template_dist_dir/${f%.json}.template"
done
# cp swagger files to regional assets
cp aws-virtual-waiting-room-swagger-*.json $build_dist_dir
# clean up
rm -f $template_dist_dir/aws-virtual-waiting-room-swagger-*.template

# update symbols in templates
echo "updating template symbols"
cd $template_dist_dir
TEMPLATES=`find . -name '*.template' -type f `

echo $TEMPLATES | \
    xargs -n 1 sed -i -e "s/%%TIMESTAMP%%/$TIMESTAMP/g"

echo $TEMPLATES | \
    xargs -n 1 sed -i -e "s/%%BUCKET_NAME%%/$DIST_OUTPUT_BUCKET/g"

echo $TEMPLATES | \
    xargs -n 1 sed -i -e "s/%%SOLUTION_NAME%%/$SOLUTION_NAME/g"

echo $TEMPLATES | \
    xargs -n 1 sed -i -e "s/%%VERSION%%/$VERSION/g"

# clean up
rm -f $template_dist_dir/*.template-e
