# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.13] - 2025-06-02

### Security

- bump setuptools to `78.1.1` to mitigate [CVE-2025-47273](https://avd.aquasec.com/nvd/cve-2025-47273)
- bump http-proxy-middleware to `2.0.9` to mitigate [CVE-2025-32997](https://avd.aquasec.com/nvd/cve-2025-32997)
- bump cryptography to `44.0.1` to mitigate [CVE-2024-12797](https://avd.aquasec.com/nvd/2024/cve-2024-12797)

### Fixed

- Moved docker container cleanup (`docker container rm`) to the end of `docker_build.sh` to fix intermittent build failures when the container would be removed before it could be used.

## [1.1.12] - 2025-03-14

### Security

- Bump axios to `1.8.2` to mitigate [CVE-2025-27152](https://github.com/axios/axios/security/advisories/GHSA-jr5f-v2jv-69x6)
- Bump serialize-javascript to `6.0.2` to mitigate [CVE-2024-11831](https://avd.aquasec.com/nvd/2024/cve-2024-11831/)
- Bump @babel/runtime and @babel/helpers to `7.26.10` to mitigate [CVE-2025-27789](https://avd.aquasec.com/nvd/cve-2025-27789)

## [1.1.11] - 2025-02-06

### Security

- `path-to-regexp` to mitigate [CVE-2024-52798]
- `nanoid` to mitigate [CVE-2024-55565]

## [1.1.10] - 2024-11-22

### Security

- `cross-spawn` to mitigate [CVE-2024-21538]

### Changed

- Migrate Python dependency manager from pip to Poetry.

## [1.1.9] - 2024-11-01

### Security

- `http-proxy-middleware` to mitigate [CVE-2024-21536]

## [1.1.8] - 2024-09-16

### Security

- `micromatch` to mitigate [CVE-2024-4067]
- `webpack` to mitigate [CVE-2024-43788]
- `express` to mitigate [CVE-2024-43796]
- `send` to mitigate [CVE-2024-43799]
- `serve-static` to mitigate [CVE-2024-43800]
- `body-parser` to mitigate [CVE-2024-45590]

## [1.1.7] - 2024-08-16

### Security

- `axios` to mitigate [CVE-2024-39338]

## [1.1.6] - 2024-08-06

### Changed

- Lambda runtime to Python 3.12

## [1.1.5] - 2024-06-25

### Security

- `ws` to mitigate [CVE-2024-37890]
- `braces` from 3.0.2 to 3.0.3 to mitigate [CVE-2024-4068]
- `urllib3` to `2.2.2` to mitigate [CVE-2024-37891]

## [1.1.4] - 2024-04-09

### Fixed

- Updated webpack-dev-middleware from 5.3.3 to 5.3.4 to resolve security vulnerability [CVE-2024-29180]
- Updated express from 4.18.1 to 4.19.2 to resolve security vulnerability [CVE-2024-29041]
- Updated follow-redirects from 1.15.4 to 1.15.6 to resolve security vulnerability [CVE-2024-28849]

## [1.1.3] - 2024-03-07

### Added

- Available Servings info to Control Panel UI [#232](https://github.com/aws-solutions/virtual-waiting-room-on-aws/pull/232).

### Fixed

- Expired queue positions persist in the Virtual Waiting Room size [#208](https://github.com/aws-solutions/virtual-waiting-room-on-aws/issues/208).
- /queue_num endpoint returns outdated results even after a reset [#214](https://github.com/aws-solutions/virtual-waiting-room-on-aws/issues/214).
- Intermittent failures in OpenID adapter's /userInfo endpoint [#231](https://github.com/aws-solutions/virtual-waiting-room-on-aws/issues/231).
- /expired_tokens endpoint bug when LastEvaluatedKey is present in query response [#235](https://github.com/aws-solutions/virtual-waiting-room-on-aws/pull/235).

## [1.1.2] - 2023-11-01

### Changed

- Resolve dependabot alerts and fix critical vulnerabilities.
- Dependency updates.

## [1.1.1] - 2023-04-18

### Changed

- Explicitly set ACL permissions for logging bucket
- Update runtime versions for pipeline files
- Update GitHub workflows used for push/PR
- Dependency updates

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

## [1.0.0] - 2021-11-23

### Added

- First public release
