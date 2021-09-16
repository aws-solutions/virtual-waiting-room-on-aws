# AWS Virtual Waiting Room
Site wrapper to absorb and control user traffic flowing into smaller web sites.

## Running unit tests for customization
* Clone the repository, then make the desired code changes
* Next, run unit tests to make sure added customization passes the tests
```
cd ./deployment
chmod +x ./run-unit-tests.sh  \n
./run-unit-tests.sh \n
```

## Building distributable for customization
* Configure the bucket name of your target Amazon S3 distribution bucket
```
export DIST_OUTPUT_BUCKET=my-bucket-name # bucket where customized code will reside
export SOLUTION_NAME=my-solution-name
export VERSION=my-version # version number for the customized code
```
_Note:_ You would have to create an S3 bucket with the prefix 'my-bucket-name-<aws_region>'; aws_region is where you are testing the customized solution. Also, the assets in bucket should be publicly accessible.

* Now build the distributable:
```
chmod +x ./build-s3-dist.sh \n
./build-s3-dist.sh $DIST_OUTPUT_BUCKET $SOLUTION_NAME $VERSION \n
```

* Deploy the distributable to an Amazon S3 bucket in your account. _Note:_ you must have the AWS Command Line Interface installed.
```
aws s3 cp ./dist/ s3://my-bucket-name-<aws_region>/$SOLUTION_NAME/$VERSION/ --recursive --acl bucket-owner-full-control --profile aws-cred-profile-name \n
```

* Get the link of the solution template uploaded to your Amazon S3 bucket.
* Deploy the solution to your account by launching a new AWS CloudFormation stack using the link of the solution template in Amazon S3.

*** 

## File Structure

```
├── deployment
│   ├── Dockerfile [ Used by docker_build script for building jwcrypto library ]
│   ├── aws-virtual-waiting-room-api-gateway-cw-logs-role.json   [ Base template for CloudWatch Logs role ] 
│   ├── aws-virtual-waiting-room-authorizers.json [ Base template for authorizers ]
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
    ├── core-api    [ Source files for core API ]
    ├── core-api-authorizers-sample   [ Source files Authorizers ]
    ├── openid-waitingroom    [ Source files for Open ID ]
    ├── sample-inlet-strategies   [ Source files for inlet strategies ]
    ├── shared    [ Source files for shared library ]
    ├── token-authorizer    [ Source files for token authorizer ]
    ├── tools   [ Source files for tools and helper scripts ]
    └── webserver-container   [ Source files for sample site's web server ]
```

***


Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://www.apache.org/licenses/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.
