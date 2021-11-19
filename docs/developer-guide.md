# AWS Virtual Waiting Room Developer Guide


## What is the AWS Virtual Waiting Room?

the AWS Virtual Waiting Room is a solution that, when deployed, can be used to temporarily divert and absorb web traffic from a site that not be prepared for large bursts of requests related to an event.

The AWS Virtual Waiting Room is can be integrated with new or existing web sites in several different ways. The CloudFormation templates create a cloud infrastructure that can be used as-is, or customized for unique needs.

Refer to the implementation guide for details on installing an AWS Virtual Waiting Room stack in your AWS account.

## Managing a Deployed Virtual Waiting Room

### CloudFormation stacks

Adding, removing and updating the top-level subsystems of a AWS Virtual Waiting Room is performed using CloudFormation.

|Template	|Description	|
|---	|---	|
|aws-virtual-waiting-room-api-gateway-cw-logs-role.template	|Use this template to add a default role ARN to API Gateway at the account-level for CloudWatch logging permissions	|
|aws-virtual-waiting-room.template	|This is the core security, public and private REST APIs, storage configuration and logic for creating waiting room events	|
|aws-virtual-waiting-room-openid.template	|Open ID identity provider for waiting room integration with authorization interfaces	|
|aws-virtual-waiting-room-authorizers.template	|Lambda authorizer designed for waiting room-issued tokens and intended for protecting end-users' APIs	|
|aws-virtual-waiting-room-sample-inlet-strategy.template	|Sample inlet strategies intended for use between a commerce/reservation site and the waiting room. Inlet strategies help encapsulate logic to determine when to allow more users into the target site.	|
|aws-virtual-waiting-room-sample.template	|Minimal web and API Gateway configuration for  a waiting room and commerce site	|

Each template provides a layer of functionality for building Virtual Waiting Rooms and integrating it with a web site.


### Updating stack parameters

Most of the AWS Virtual Waiting Room stacks include parameters for various settings used during configuration and while the solution is running. Any of the parameters can be changed and the stack updated in place using the existing templates.

### CloudWatch metrics and alarms

The core stack for the AWS Virtual Waiting Room installs several CloudWatch Alarms. Navigate to the CloudWatch Console and select an alarm option on the left side of the page. The installed alarms include:

1. 4xx status codes for public and private APIs
1. 5xx status codes for public and private APIs
1. Lambda throttling for each installed function
1. Lambda errors for each installed function

The alarms are installed in the same region as the core API stack. Each alarm is prefixed with the stack name, the resource name and "Alarm" at the end. If you know the core stack name, you can quickly filter other alarms out of the list view.

The alarms are configured for a 1-minute evaluation period and any count greater than zero (0) will trigger the alarm for that period of time. You can configure these alarms to send notifications when their state changes.



## Basic Concepts and Flow of a Virtual Waiting Room


High level flow chart


Options - inlet strategies
Options - Open ID adapter



## Customizing and Extending

### Virtual Waiting Room Landing Pages



### Inlet Strategies

Inlet strategies encapsulate the logic and data needed to move clients from the waiting room to the website. An inlet strategy can be implemented as a Lambda function, container, EC2 or any other compute resource. It does not need to be a cloud resource as long as it can call the waiting room public and private APIs. The inlet strategy may receive events about the waiting room, the website, or other outside indicators that help it decide when more clients can have tokens issued and enter the site. There are several approaches to inlet strategies. Which one you adopt depends on the resources available to you and constraints in the design of the website being protected. 

The primary action taken by the inlet strategy is to call the increment_serving_num private API with a relative value that indicates how many more clients can enter the site. This section describes two sample inlet strategies. These can be used as-is, customized, or you can employ a completely different approach.

**MaxSize**

Using the MaxSize strategy, the Inlet Lambda function is configured with the maximum number of clients that can use the website concurrently. This is a fixed value. A client issues an Amazon SNS notification that invokes the MaxSizeInlet Lambda function to increase the serving counter based on the message payload. The source of the SNS message can come from anywhere, including code on the website or a monitoring tool that observes the site’s utilization level.
The MaxSizeInlet Lambda function expects to receive a message that can include:
•	exited : number of transactions that have completed
•	list of request IDs to be marked completed
•	list of request IDs to be marked abandoned
This data is used to determine how much to increment the serving counter. There may be cases where there is no additional capacity to increment the counter, based on the current number of clients.

**Periodic**

When using the Periodic strategy, a CloudWatch rule invokes a Lambda function every minute to increase the serving counter by a fixed quantity. The Periodic inlet is parameterized with the event start time, end time, and increment amount. Optionally, this strategy will also check a CloudWatch alarm and, if the alarm is in OK state, perform the increment, otherwise skip it. The site integrators can connect a utilization metric to an alarm, and use that alarm to pause the periodic inlet. This strategy will only change the serving position while the current time is between the start and end times, and optionally, the specified alarm is in the OK state.



## Security

ElastiCache for Redis is assigned a network interface inside the private VPC. The Lambda functions that interact with 

ElastiCache for Redis are also assigned network interfaces within a VPC. All other resources have network connectivity in the shared AWS network space. Lambda functions with VPC interfaces that interact with other AWS services use VPC endpoints to connect to these services.

The public and private keys used for creating and validating JSON web tokens are generated at installation time and stored in Secrets Manager. The password used to connect to ElastiCache for Redis is also generated at installation time and stored in Secrets Manager. The private key and ElastiCache for Redis password are not accessible via any solution API.

The public API must be accessed through CloudFront. The solution generates an API key for API Gateway, which is used as the value of a custom header, x-api-key, in CloudFront. CloudFront includes this header when making origin requests. For additional details, refer to [Adding custom headers to origin requests](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/add-origin-custom-headers.html) in the Amazon CloudFront Developer Guide.

The private APIs are configured to require AWS IAM authorization for invocation. The solution creates the ProtectedAPIGroup IAM user group with the appropriate permissions to invoke the private APIs. An IAM user added to this group are authorized to invoke the private APIs.

IAM policies used in roles and permissions that are attached to various resources created by the solution grant only the permissions required to perform the necessary tasks.
For resources such as S3 buckets, SQS queues, and SNS topics generated by the solution, encryption at rest and during transit is enabled wherever possible. 

## Monitoring
The core API stack includes several CloudWatch Alarms that can be monitored to detect problems while the solution is operating. The stack creates an alarm for Lambda function errors and throttle conditions, and will change the state of the alarm from OK to ALARM if an error or throttle condition occurs in a one-minute period.
The stack also creates alarms for each API Gateway deployment for 4XX and 5XX status codes. The alarm will change state from OK to ALARM if a 4XX or 5XX status code is returned from the API within a one-minute period.
These alarms will return to an OK state after one minute of no errors or throttles.

### API Gateway Alarms

4xx response status from APIs
-	This can be caused from an incorrect Event ID or Request ID or both – you will see this occur in the CloudWatch Logs for the related Lambda function
-	Private APIs are IAM authenticated and the client will need AWS keys that have rights to invoke the private APIs – you will see this occur in the CloudWatch Logs for API Gateway

5xx response status from APIs
-	Response from throttled Lambda or API Gateway, check LambdaNameThrottlesAlarm
-	Misconfiguration on back-end, check LambdaNameErrorsAlarm and CloudWatch Logs for details

5XXErrorPublic/PrivateApiAlarm
-	This alarm state is ALARM when the API returns a 5XX status to the caller within a 60 second period
-	This alarm returns to OK when no 5xx status is returned for 60 seconds
-	This alarm can be triggered by a Lambda function or Lambda runtime returning an error to API Gateway

4XXErrorPublic/PrivateApiAlarm
-	This alarm state is ALARM when the API return a 4XX status to the caller within a 60 second period
-	This alarm returns to OK when to 4XX status is returned for 60 seconds
-	This alarm can be trigged by an incorrect API URL

### Lambda Throttle Alarms

*LambdaName*ThrottlesAlarm
-	This alarm state is ALARM when the named Lambda encounters a concurrent execution limit within a 60 second period
-	This alarm returns to OK if no throttles are encountered for 60 seconds
-	You may need to increase the concurrency limit for your account’s region
-	You may be encountering the burst limit for Lambda, which requires some retry logic on your client

### Lambda Error Alarms

*LambdaName*ErrorsAlarm
-	This alarm state is ALARM when the named Lambda encounters a runtime execution error within a 60 second period
-	This alarm returns to OK if no errors are encountered for 60 seconds
-	This can be caused by a misconfiguration on the back-end
-	This can be caused by a bug in the Lambda’s code












## Developing a Virtual Waiting Room

The purpose of a virtual waiting room is to absorb and reduce the traffic load on a web site that may not be prepared for large bursts of requests related to an event.

The AWS Virtual Waiting Room is can be integrated with new or existing web sites. The CloudFormation templates create a cloud infrastructure designed for temporarily absorbing traffic away from a site. 









## Waiting Room Development Roles/Tasks



|Role	|Task	|
|---	|---	|
|AWS Solution Developers	|Provide waiting room infrastructure and extension mechanisms for customization	|
|Customer IT Staff	|Deploy waiting room stacks for each site requiring protection	|
|	|Determine how to measure load on the commerce site	|
|Customer Development	|Use or customize an inlet strategy handler	|
|Customer Web Development	|Customize the waiting room page(s) to match commerce site style, theme, etc.	|
|	|	|



## Sample Stack


The Sample stack requires the Core (main) API and API Gateway authorizers stacks be installed first.

The main web page is stored in an S3 bucket and used as an origin to CloudFront. The connection between CloudFront and the bucket is secured using a CloudFront Origin Access Identity.

The entire sample is contained by the single page. It will take the user through the following steps:

1. Get in Line at the waiting room for entry into the site
2. Obtain the client’s position in line
3. Obtain the serving position of the waiting room
4. Obtain a token set once the serving position is equal or greater to the client’s position
5. Use the token to call an API available to clients that have progressed through the waiting room 



## Extension Points

The AWS Virtual Waiting Room is designed for extension through two mechanisms: EventBridge for uni-directional event notification and REST APIs for bi-directional communication.


## Events

Events from EventBridge are emitted as activities occur within the waiting room solution. The main template will install an EventBridge bus with the name STACK-WaitingRoomEventBus. You can find the exact name of the bus by navigating to the CloudFormation stack for the main template, select the Resources tab, and follow the link from the WaitingRoomEventBus logical ID to the EventBridge console.

Events emitted from the solution are:

1. **token_generated**
    1. Detail:
        `{
        "event_id": EVENT_ID,
        "request_id":REQUEST_ID
        }`
2. **session_updated**
    1. Detail:
        `{
        "event_id": EVENT_ID,
        "request_id": REQUEST_ID,
        "status": STATUS_TEXT
        }`


Periodic Event Generation for Metrics

This is an option setting in the main template.



## REST APIs

There are two levels of REST APIs provided with the AWS Virtual Waiting Room. The Core APIs are the lowest layer of interaction with the solution. Other Lambda functions, EC2, and containers can act as extensions and call the Core APIs to build waiting rooms and control inlet traffic and react to events generated from the solution.

The Open ID Adapter provides a set of OIDC-compatible APIs that can be used with existing web hosting software that support OIDC identity providers, like AWS Elastic Load Balancers, WordPress, or as a federated identity provider for a service like Amazon Cognito.

The Sample stack includes an API Gateway as an example of a commerce API protected by a waiting room. The Sample stack APIs are protected by the Authorizer stack that is installed earlier. 


## JSON Web Tokens

The JSON Web Tokens generated from the Core REST API are intended as credentials to figuratively pass through the waiting room to access content and use services of the commerce site being protected. The JWTs can be used for web site protection, as in preventing access to web pages until the waiting room token is obtained, and also for API access authorization.

The solution includes an API Gateway Lambda Authorizer. This allows a developer to prevent access to one or more API endpoints until a token has been issued from the API.



## Public REST APIs

The Core APIs are divided into publicly accessible resources and IAM-authorized resources. 

The “Content-Type” header is always set to “application/json” with these resources and request body parameters are URL-encoded JSON objects.

1. `/assign_queue_num`
    1. Description: Request to enter the waiting room queue. This is usually the first request issued by client when thy are ready to get in line. This is an asynchronous request that returns a request ID immediately that can be used later to retrieve the result of this request using `/queue_num`.
    2. Authorization: NONE
    3. Method: POST
    4. Content-Type: `application/json`
    5. Query parameters: NONE
    6. Request body: 
        `{
        "event_id": EVENT_ID
        }`
    7. Response body:
        `{
        "api_request_id": REQUEST_ID
        }`
    8. Status code: 200
2. `/generate_token`
    1. Description: Generates a JWT set issued from the Core API. The current serving position must be equal or greater to this request ID’s queue position to obtain a token. This API is idempotent, meaning, the exact tokens generated for the event and request ID are returned on all future requests.
    2. Authorization: None
    3. Method: POST
    4. Content-Type: `application/json`
    5. Query parameters: NONE
    6. Request body:
        `{ 
        "event_id": EVENT_ID,
        "request_id": REQUEST_ID
        }`
    7. Response body:
        `{
        "access_token": JWT,
        "refresh_token": JWT,
        "id_token": JWT,
        "token_type": "Bearer",
        "expires_in": SECONDS
        }`
    8. Status codes:  
        200: Success  
        202: Request ID queue position not being served  
        400: Invalid event ID or request ID not in the expected format  
        404: Invalid request ID (not found)
3. `/public_key`
    1. Description: Returns the public JWT that can be used to verify signed tokens issued by this stack.
    2. Authorization: NONE
    3. Method: GET
    4. Content-Type: `application/json`
    5. Query parameters: `event_id`
    6. Request body: NONE
        Response body:
        `{
        "kty": "RSA",
        "alg": "RS256",
        "kid": KID,
        "n": KEY,
        "e": "AQAB"
        }`
    7. Status codes:  
        200: Success  
        404: Missing event ID
4. `/queue_num`
    1. Description: Returns the queue position for the provided event and request ID. This API may need to be called more than once depending on load of the waiting room. This API will return a 404 status code until it has processed the request from API Gateway.
    2. Authorization: NONE
    3. Method: GET
    4. Content-Type: `application/json`
    5. Query parameters: `event_id, request_id`
    6. Request body: NONE
    7. Response body:
        {
        "entry_time": TIMESTAMP,
        "queue_number": INTEGER,
        "event_id": EVENT_ID,
        "status": STATUS (1 = successfully entered, -1 = invalid request sent)
        }
    8. Status codes:  
        200: Success  
        202: Request ID not processed yet  
        404: Invalid event or request ID 
5. `/serving_num`
    1. Description: Returns the current serving position in the queue. Requests with an equal or lower position in the waiting room can request tokens from the API.
    2. Authorization: NONE
    3. Method: GET
    4. Content-Type: `application/json`
    5. Query parameters: `event_id`
    6. Request body: NONE
    7. Response body:
        `{
        "serving_counter": INTEGER
        }`
    8. Status codes:  
        200: Success  
        404: Invalid event ID
6. `/waiting_num`
    1. Description: Returns the number users currently queued in the waiting room and have not been issued a token yet.
    2. Authorization: NONE
    3. Method: GET
    4. Content-Type: `application/json`
    5. Query parameters: `event_id`
    6. Request body: NONE
    7. Response body:
        `{
        "waiting_num": INTEGER
        }`
    8. Status codes:  
        200: Success  
        404: Invalid event ID

## Private REST APIs

1. `/expired_tokens`
    1. Description: Returns a list of REQUEST_IDs with tokens with `exp` claims that are earlier than the current time.
    2. Authorization: IAM
    3. Method: GET
    4. Content-Type: `application/json`
    5. Query parameters: `event_id`
    6. Request body: NONE
    7. Response body:
        `[ REQUEST_ID, REQUEST_ID, ... ]`
    8. Status codes:  
        200: Success  
        400: Invalid event ID
2. `/generate_token`
    1. Description: Generates a JWT set with options to override the token claims. The current serving position must be equal or greater to this request ID’s queue position to obtain a token. This API is idempotent, meaning, the exact tokens generated for the event and request ID are returned on all future requests.
    2. Authorization: IAM
    3. Method: POST
    4. Content-Type: `application/json`
    5. Query parameters: NONE
    6. Request body:
        `{ 
        "event_id": EVENT_ID,
        "request_id": REQUEST_ID,
        "issuer": ISSUER,
        "validity_period": SECONDS
        }`
    7. Response body:
        `{
        "access_token": JWT,
        "refresh_token": JWT,
        "id_token": JWT,
        "token_type": "Bearer",
        "expires_in": SECONDS
        }`
    8. Status codes:  
        200: Success  
        202: Request ID not being served  
        400: Invalid event ID or request ID not in the expected format  
        404: Invalid request ID (not found)
3. `/increment_serving_counter`
    1. Description: Move the serving counter forward or backward a number of positions.
    2. Authorization: IAM
    3. Method: POST
    4. Content-Type: `application/json`
    5. Query parameters: NONE
    6. Request body:
        `{ 
        "event_id": EVENT_ID,
        "increment_by": -INTEGER or INTEGER
        }`
    7. Response body:
        `{
        "serving_num": INTEGER
        }`
    8. Status codes:  
        200: Success  
        400: Invalid event ID
4. `/num_active_tokens`
    1. Description: Returns the number of active tokens issued for this event. An active token has an `exp` attribute that is later than the current time.
    2. Authorization: IAM
    3. Method: GET
    4. Content-Type: `application/json`
    5. Query parameters: `event_id`
    6. Request body: NONE
        Response body:
        `{
        "active_tokens": INTEGER
        }`
    7. Status codes:  
        200: Success  
        404: Invalid event ID
5. `/reset_initial_state`
    1. Description: This API resets the internal counters to zero and deletes then recreates the DynamoDB table used by the core API.
    2. Authorization: IAM
    3. Method: POST
    4. Content-Type: `application/json`
    5. Query parameters: `event_id`
    6. Request body: 
        `{
        "event_id": EVENT_ID
        }`
        Response body:
        `{
        "message": "Counters reset. DynamoDB table recreated."
        }`
    7. Status codes:  
        200: Success  
        400: Invalid event ID
6. /update_session
    1. Description: This API will change the status of an issued token.
    2. Authorization: IAM
    3. Method: POST
    4. Content-Type: `application/json`
    5. Query parameters: NONE
    6. Request body:
        `{
        "event_id": EVENT_ID,
        "request_id": REQUEST_ID,
        "status": INTEGER (1 = completed, -1 = abandoned)
        }`
    7. Response body: NONE
    8. Status codes:  
        200: Success  
        400: Invalid event ID or request ID  
        404: Request ID doesn't exist or status already set




## Open ID Adapter

This is the translation table of Virtual Waiting Room to Open ID values and naming.

|Waiting Room Name	|Open ID Name	|
|---	|---	|
|Event ID	|Audience (aud), Client ID	|
|Request ID	|Code, Subject (sub)	|

### Waiting Room Token Claims

`{
"aud": EVENT_ID,
"sub": REQUEST_ID,
"queue_position": INTEGER,
"token_use": "access|id|refresh",
"iat": TIMESTAMP,
"nbf": TIMESTAMP,
"exp": TIMESTAMP,
"iss": ISSUER_URL
}`



### APIs

1. /`.well-known/jwks.json`
    1. Description: Returns a list of public keys that will be used to sign tokens. The `kid` attribute will match tokens generated with a specific key. This endpoint is returned in the response from `/.well-known/openid-configuration.`
    2. Authorization: NONE
    3. Method: GET
    4. Content-Type: `application/json`
    5. Query parameters: NONE
    6. Request body: NONE
    7. Response body:
        `{
        "keys":[ PUBLIC-JWK ]
        }`
    8. Status code:
        200: Success
2. `/.well-known/openid-configuration`
    1. Description: https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderConfig
    2. Authorization: NONE
    3. Method: GET
    4. Content-Type: `application/json`
    5. Query parameters: NONE
    6. Request body: NONE
    7. Response body:
        `{
        "authorization_endpoint": URL,
        "id_token_signing_alg_values_supported":["RS256"],
        "issuer":URL,
        "jwks_uri":URL,
        "response_types_supported":["code"],
        "scopes_supported":["openid"],
        "subject_types_supported":["public"],
        "token_endpoint":URL,
        "token_endpoint_auth_methods_supported":
             ["client_secret_basic","client_secret_post"],
        "userinfo_endpoint":URL
        }`
    8. Status code:
        200: Success
3. `/authorize`
    1. Description: https://openid.net/specs/openid-connect-core-1_0.html#AuthorizationEndpoint
    2. Authorization: NONE
    3. Method: GET
    4. Content-Type: ANY
    5. Query parameters: `client_id, redirect_uri, response_type`
    6. Request body: NONE
    7. Response body: NONE
    8. Status codes:  
        302: Redirect to waiting room entry page  
        400: Bad request
4. `/token`
    1. Description: https://openid.net/specs/openid-connect-core-1_0.html#TokenEndpoint
    2. Authorization: NONE
    3. Method: POST
    4. Content-Type: `application/x-www-form-urlencoded`
    5. Query parameters: NONE
    6. Request body:
        `{
        "client_id": EVENT_ID,
        "client_secret": SHARED_SECRET,
        "code": REQUEST_ID,
        "grant_type": "authorization_code"
        }`
    7. Response body:
        `{
        "access_token": JWT,
        "refresh_token": JWT,
        "id_token": JWT,
        "token_type": "Bearer",
        "expires_in": SECONDS
        }`
    8. Status codes:  
        200: Success  
        400: Bad request
5. `/userInfo`
    1. Description: https://openid.net/specs/openid-connect-core-1_0.html#UserInfo
    2. Authorization:
        Header: `Authorization: Bearer ACCESS-TOKEN`
    3. Method: GET
    4. Content-Type: `application/json`
    5. Query parameters: NONE
    6. Request body:
        `{
        "client_id": EVENT_ID,
        "client_secret": SHARED_SECRET,
        "code": REQUEST_ID,
        "grant_type": "authorization_code"
        }`
    7. Response body:
        `{
        "access_token": JWT,
        "refresh_token": JWT,
        "id_token": JWT,
        "token_type": "Bearer",
        "expires_in": SECONDS
        }`
    8. Status codes:  
        200: Success  
        400: Bad request

