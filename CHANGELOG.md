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
- Update runtime versions for pipeline files
- Update GitHub workflows used for push/PR
- Dependency updates

## [1.1.2] - 2023-11-01

### Updated

- Resolve dependabot alerts and fix critical vulnerabilities.
- Dependency updates.

## [1.1.3] - 2024-03-07

### Added 

- Available Servings info to Control Panel UI [#232](https://github.com/aws-solutions/virtual-waiting-room-on-aws/pull/232).

### Fixed

- Expired queue positions persist in the Virtual Waiting Room size [#208](https://github.com/aws-solutions/virtual-waiting-room-on-aws/issues/208).
- /queue_num endpoint returns outdated results even after a reset [#214](https://github.com/aws-solutions/virtual-waiting-room-on-aws/issues/214).
- Intermittent failures in OpenID adapter's /userInfo endpoint [#231](https://github.com/aws-solutions/virtual-waiting-room-on-aws/issues/231).
- /expired_tokens endpoint bug when LastEvaluatedKey is present in query response [#235](https://github.com/aws-solutions/virtual-waiting-room-on-aws/pull/235).

## [1.1.4] - 2024-04-09

### Fixed
- Updated webpack-dev-middleware from 5.3.3 to 5.3.4 to resolve security vulnerability [CVE-2024-29180]
- Updated express from 4.18.1 to 4.19.2 to resolve security vulnerability [CVE-2024-29041]
- Updated follow-redirects from 1.15.4 to 1.15.6 to resolve security vulnerability [CVE-2024-28849]