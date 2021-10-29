// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/*jshint esversion: 6 */

module.exports = {
  publicPath: (process.env.NODE_ENV === 'production' ? '/control-panel/' : '/'),
  outputDir: 'dist/www/control-panel'
};