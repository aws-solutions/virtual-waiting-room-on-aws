# AWS Virtual Waiting Room
Site wrapper to absorb and control user traffic flowing into smaller web sites.

<a name="prerequisites-for-customization"></a>
## Prerequisites for Customization
[//]: # (Add any prerequisites for customization steps. e.g. Prerequisite: Node.js>10)

* Install/update to Python 3.x
* Install the AWS Command Line Interface (CLI)
* Create a Python [virtual environment](https://docs.python.org/3.8/library/venv.html) using [requirements.txt](deployment/requirements.txt) and activate it
* Configure the bucket name of your target Amazon S3 distribution bucket


## Building distributable for customization
* Configure the bucket name of your target Amazon S3 distribution bucket
```
export DIST_OUTPUT_BUCKET=<MY-BUCKET-NAME> # bucket where customized code will reside
export SOLUTION_NAME=my-solution-name
export VERSION=my-version # version number for the customized code
```
_Note:_ You would have to create an S3 bucket with the prefix '<MY-BUCKET-NAME>-<AWS-REGION>'; <AWS-REGION> is where you are testing the customized solution. Also, the assets in bucket should be publicly accessible.

* Now build the distributable:
```
chmod +x ./build-s3-dist.sh 
./build-s3-dist.sh $DIST_OUTPUT_BUCKET $SOLUTION_NAME $VERSION 
```

* Deploy the distributable to an Amazon S3 bucket in your account. The head-bucket command verifies that your account owns the bucket. _Note:_ you must have the AWS Command Line Interface installed.
```
aws s3api head-bucket --bucket <MY-BUCKET-NAME>-<AWS-REGION> --expected-bucket-owner <AWS-ACCOUNT-ID>
aws s3 cp ./dist/ s3://<MY-BUCKET-NAME>-<AWS-REGION>/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control --profile aws-cred-profile-name 
```

* Get the link of the solution template uploaded to your Amazon S3 bucket.
* Deploy the solution to your account by launching a new AWS CloudFormation stack using the link of the solution template in Amazon S3.

## Running unit tests for customization
* Some packages require a build before unit tests will run
* Install the common package into the virtual envronment before running
```
cd ./deployment
pip install ./pkg/aws_virtual_waiting_room_common-1.0.0-py3-none-any.whl
chmod +x ./run-unit-tests.sh  
./run-unit-tests.sh 
```

*** 

## File Structure

```
├── deployment
│   ├── Dockerfile [ Used by docker_build script for building jwcrypto library ]
│   ├── aws-virtual-waiting-room-api-gateway-cw-logs-role.json   [ Base template for CloudWatch Logs role ] 
│   ├── aws-virtual-waiting-room-authorizers.json [ Base template for authorizers ]
│   ├── aws-virtual-waiting-room-getting-started.json [ Nested template for new users ]
│   ├── aws-virtual-waiting-room-openid.json    [ Base template for Open ID ]
│   ├── aws-virtual-waiting-room-sample-inlet-strategy.json   [ Base template for sample inlet strategy]
│   ├── aws-virtual-waiting-room-sample.json    [ Base template for sample site ]
│   ├── aws-virtual-waiting-room-swagger-private-api.json   [ Swagger file for private API ]
│   ├── aws-virtual-waiting-room-swagger-public-api.json    [ Swagger file for public API ]
│   ├── aws-virtual-waiting-room.json   [ Base template for core API ]
│   ├── build-s3-dist.sh    [ Script for building distributables and preparing the CloudFormation templates ]
│   ├── deploy.sh   [ Script for building distributables and preparing the CloudFormation templates ]
│   ├── docker_build.sh   [ Script for building jwcrypto library ]
│   ├── global-s3-assets  [ Directory for writing out CloudFormation during local build ]
│   ├── regional-s3-assets     [ Directory for writing out CloudFormation during local build ]
│   ├── requirements.txt    [ System requirements for local builds ]
│   └── run-unit-tests.sh   [ Script to run unit tests ]
├── docs
│   ├── developer-guide.md    [ Waiting room developer guide ]
│   ├── install-guide.md      [ Waiting room installation guide ]
│   ├── physical-view.drawio
│   ├── physical-view.jpg
│   ├── sequence-diagrams.drawio
│   └── software-architecture.md
└── source
    ├── control-panel    [ Source files for sample control panel ]
    ├── core-api    [ Source files for core API ]
    ├── core-api-authorizers-sample   [ Source files Authorizers ]
    ├── openid-waitingroom    [ Source files for Open ID ]
    ├── sample-inlet-strategies   [ Source files for inlet strategies ]
    ├── sample-waiting-room-site   [ Source files for sample waiting room ]
    ├── shared    [ Source files for shared library ]
    ├── token-authorizer    [ Source files for token authorizer ]
    └── tools   [ Source files for tools and helper scripts ]
```

***


Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://www.apache.org/licenses/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.
