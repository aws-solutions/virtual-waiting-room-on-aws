# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2021-11-23

### Added

- First public release

## [1.1.0] - 2022-09-26

### Added 

- Create 2 more core-api Lambda functions for 
    - getting queue position expiry time (get_queue_position_expiry_time)
    - setting the max queue position expired (set_max_queue_position_expired)
- Deployment Templates
    - addl template parameters QueuePositionExpiryPeriod, EnableQueuePositionExpiry, IncrSvcOnQueuePositionExpiry
    - parameters included in the getting started template 
    - new Cloudfront cache policy QueuePositionExpiryCachePolicy
- Public Api endpoint to get remainig queue position expiry time 
    - GET /queue_pos_expiry?event_id={EventId}&request_id={RequestId}
- Additional 2 dyanamo db tables for storing waiting room information
    - queue position entry time QueuePositionEntryTimeTable
    - serving counter issue time ServingCounterIssuedAtTable
- Reduce redis cache usage by moving queue entry time information to dynamodb 
- Automatic serving counter increment based on expired queue positions (opt-in feature)
- Queue position expiry based on timeout (opt-in feature)
- Consolidate generate token methods with a base implementation  
    - generate_token_base

## [1.1.1] - 2023-04-18

### Updated 

- Explicitly set ACL permissions for logging bucket
