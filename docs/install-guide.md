# Virtual Waiting Room on AWS Installation Guide

##  Overview

The Virtual Waiting Room on AWS is a solution and toolkit that helps absorb and control incoming user requests to a web site that may not be prepared for an unusually large burst of traffic. 

It is used to redirect incoming users’ browsers to a holding-area before permitting them to continue into an event, commerce or scheduling site. 

The Virtual Waiting Room on AWS can be integrated with new or existing web sites. The templates create a cloud infrastructure designed for temporarily absorbing traffic away from a site, and it provides options to customize and integrate a virtual waiting room with an existing web site


The end-to-end architecture of the Virtual Waiting Room on AWS stacks, related REST APIs and event sources, and sample customer-protected sites are shown in the following diagram.

[Image: physical-view.jpg]

## AWS Supported Regions

The Virtual Waiting Room on AWS pre-releases can be installed into the following regions using the supplied CloudFormation templates. Please ask if you would like installation support in more regions.

1. ap-northeast-1
2. ap-south-1
3. ap-southeast-1
4. ca-central-1
5. eu-central-1
6. eu-north-1
7. eu-west-1
8. sa-east-1
9. us-east-1
10. us-east-2
11. us-west-1
12. us-west-2



## Prerequisites

AWS account
Console permissions equivalent to AdministratorAccess
Knowledge of deploying CloudFormation stacks
Staff familiar with the architecture and implementation details of the site to protect


### Enable CloudWatch logging from API Gateway

Navigate to the API Gateway console using the region you will use to install the stacks
If you have existing APIs defined in this region:
Select any API
Select Settings at the bottom left of the page
Check for a value in the **CloudWatch log role ARN** field
If there is no ARN, start by installing the virtual-waiting-room-on-aws-api-gateway-cw-logs-role.template
If there is an ARN here, skip this step and start with the aws-virtual-waiting-room.template
If there is no existing APIs defined in this region, start by installing the virtual-waiting-room-on-aws-api-gateway-cw-logs-role.template


## Installation

This solution is installed into one or more AWS accounts using CloudFormation templates. 

The Virtual Waiting Room on AWS includes four CloudFormation templates that can be installed from the AWS web console. Use exactly these template URLs for installing into any of the supported regions listed above. 

|Template URL	|Description	|
|---	|---	|
|https://virtual-waiting-room-on-aws-us-west-2.s3.us-west-2.amazonaws.com/aws-virtual-waiting-room/v1.0.0/virtual-waiting-room-on-aws-api-gateway-cw-logs-role.template	|Use this template to add a default role ARN to API Gateway at the account-level for CloudWatch logging permissions	|
|https://virtual-waiting-room-on-aws-us-west-2.s3-us-west-2.amazonaws.com/aws-virtual-waiting-room/v1.0.0/aws-virtual-waiting-room.template	|This is the core public and private REST APIs and cloud services for creating waiting room events	|
|https://virtual-waiting-room-on-aws-us-west-2.s3.us-west-2.amazonaws.com/aws-virtual-waiting-room/v1.0.0/virtual-waiting-room-on-aws-openid.template	|Open ID identity provider for waiting room integration with authorization interfaces	|
|https://virtual-waiting-room-on-aws-us-west-2.s3.us-west-2.amazonaws.com/aws-virtual-waiting-room/v1.0.0/virtual-waiting-room-on-aws-authorizers.template	|Lambda authorizer designed for waiting room-issued tokens and intended for protecting end-users' APIs	|
|https://virtual-waiting-room-on-aws-us-west-2.s3-us-west-2.amazonaws.com/aws-virtual-waiting-room/v1.0.0/virtual-waiting-room-on-aws-sample-inlet-strategy.template	|Sample inlet strategies intended for use between a commerce/reservation site and the waiting room. Inlet strategies help encapsulate logic to determine when to allow more users into the target site.	|
|https://virtual-waiting-room-on-aws-us-west-2.s3.us-west-2.amazonaws.com/aws-virtual-waiting-room/v1.0.0/virtual-waiting-room-on-aws-sample.template	|Minimal web and API Gateway configuration for  a waiting room and commerce site	|

Each template provides a layer of functionality for building Virtual Waiting Rooms.

Install the main (also referred to as Core) template where you will need the waiting room REST APIs, ElasticCache and DynamoDB tables installed. This is also the account where the public and primary signing keys are generated into SecretsManager. These keys are used for creating and validating JSON web tokens issued from the waiting room solution.

1. aws-virtual-waiting-room.template

If this is the first time installing, or you are not sure what to install, include the authorizers, sample inlet strategies and sample waiting room code templates. This will allow you to see a minimal waiting room with a simple flow.

1. virtual-waiting-room-on-aws-authorizers.template
2. virtual-waiting-room-on-aws-sample-inlet-strategy.template
3. virtual-waiting-room-on-aws-sample.template

The authorizers template will request parameters that are outputs of the installation of the main template. This is also tru for the inlet strategies template. You can find these values by navigating to the previously installed CloudFormation stack and choosing the Output tab.

The sample waiting room template will request parameters from the outputs of the main, authorizers and inlet strategies templates. The Output tab of the


## Check and Review the Sample

The sample demonstrates a very simple, single-page waiting room and the use of a protected API after the user’s browser is provided an access token to proceed.

You will need a tool like Postman that can sign requests to API Gateway to do this exercise. You will also need AWS keys with permissions to call the IAM secured APIs in the core stack.



### Set an initial serving position

Find the Private API URL for the Core API by navigating to the CloudFormation stack installed for the main template. Click the Outputs tab of the stack, and copy and save the URL for PrivateApiInvokeURL for later.

Get the Event ID you used to install the main stack and save it for later. This value is retained on the Parameters tab of the main template stack.

The request needs to be signed, which Postman can do. Provide your AWS keys to Postman in the Authorization tab.

Send a POST request to this URL:
`*PrivateApiInvokeURL*/increment_serving_counter`

Modify and use this body for the request substituting the Event ID provided via stack parameters:
`{`
`"event_id": "EVENT_ID",`
`"increment_by": 1`
`}`

The first time you send this API call, you will receive a 200 status code and a response like:
`{`
`"serving_num": 1`
`}`


### Retrieve the link to the waiting room sample site and enter the waiting room

Navigate your browser to the ws-virtual-waiting-room-sample CloudFormation stack
Go to the Outputs tab
Copy the WaitingRoomURL link that includes the CloudFront domain and event_id parameter
Navigate your browser to that URL
The page will load and present a button to Get in Line.


### Get in line and test the waiting room

Click the Get in Line button and wait for a response with your queue position.
After you receive a place in the line, the code will retrieve the current serving position of the waiting room and display it.
If this is the first time using this page, you should be in position 1 and the serving position will be one from the API call issued above, and you will see the Time to Go! button enabled.
Clicking the Time to Go! button does the following:

1. Stops the serving position update
2. Retrieves a JWT from the public API using the event ID and request ID
3. Creates an API request to the protected demonstration customer API by adding the JWT to the Authorization header in the request
4. Displays the status and output of the API call on the web page
5. Refresh the page to repeat the process


Call the `increment_serving_counter` API again to move the serving position forward or back. This API will accept negative values to decrement the serving position of the waiting room if a situation requires that.



## Configure the Open ID Adapter

Install the Open ID adapter stack using the template named virtual-waiting-room-on-aws-openid.template
The Open ID stack will request parameters from the core API stack

This sample uses the following AWS resources:

* Load Balancer
* Domain name
* ACM certificate for domain name
* EC2 with a web server configured









## FAQ

* Q: When do I need to install the core API and services template?
    A: Always, first.
* Q: Can I protect my 

