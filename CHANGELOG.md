# Changelog

## [2.0.0](https://github.com/femiwiki/quibble-action/compare/v1.0.0...v2.0.0) (2026-07-01)


### ⚠ BREAKING CHANGES

* .github/workflows/dependencies is no longer read and exclude-known-failures is removed; declare dependencies via the new sources.
* the default php-version is now 8.4 on Debian bookworm, so the Quibble and phan stages run on PHP 8.4. Set php-version (and debian) explicitly to keep the old behavior.
* the default mediawiki-version is now REL1_45. Workflows that relied on the previous REL1_43 default must set mediawiki-version: REL1_43 explicitly to keep testing against it.

### Features

* add php-version input ([#25](https://github.com/femiwiki/quibble-action/issues/25)) ([d746cad](https://github.com/femiwiki/quibble-action/commit/d746cad345d00533b76a0f6813c1f382633e2507))
* add project-path input for the project under test ([#35](https://github.com/femiwiki/quibble-action/issues/35)) ([961ecc6](https://github.com/femiwiki/quibble-action/commit/961ecc624a6bb53f91747a80054c87fe25d85131))
* annotate phan findings on the changed lines ([#41](https://github.com/femiwiki/quibble-action/issues/41)) ([24809c1](https://github.com/femiwiki/quibble-action/commit/24809c11bc7f8790681a0697440541f993964e0c))
* annotate phpcs findings on the changed lines ([#43](https://github.com/femiwiki/quibble-action/issues/43)) ([6bf963a](https://github.com/femiwiki/quibble-action/commit/6bf963a3b99b64861bec07c429edb7bf996d6013))
* default api-testing to the wikidiff2 image ([#30](https://github.com/femiwiki/quibble-action/issues/30)) ([8eed531](https://github.com/femiwiki/quibble-action/commit/8eed531afccc9d426ea88cdea415d1a63411a45b)), closes [#3](https://github.com/femiwiki/quibble-action/issues/3)
* default mediawiki-version to REL1_45 ([#24](https://github.com/femiwiki/quibble-action/issues/24)) ([f5ab739](https://github.com/femiwiki/quibble-action/commit/f5ab739c819562bf47282ed7d06f5c1842715224))
* default to PHP 8.4 on Debian bookworm ([#28](https://github.com/femiwiki/quibble-action/issues/28)) ([b03fe80](https://github.com/femiwiki/quibble-action/commit/b03fe80e356d5bfb029c81147db8ad07c8510246))
* derive PHP version from the MediaWiki branch ([#39](https://github.com/femiwiki/quibble-action/issues/39)) ([29a0905](https://github.com/femiwiki/quibble-action/commit/29a09052cf11da332b39e781bbe708a0c8499674))
* derive the Debian base from the MediaWiki branch ([#40](https://github.com/femiwiki/quibble-action/issues/40)) ([f485e3d](https://github.com/femiwiki/quibble-action/commit/f485e3d07409f1524adfb26d12d22830b6b39b06))
* redefine dependency resolution from local sources ([#36](https://github.com/femiwiki/quibble-action/issues/36)) ([dee0c88](https://github.com/femiwiki/quibble-action/commit/dee0c886057c8c5b7fd0e57400efcf77647404db))
* run phan in the Quibble image instead of the unmaintained phan image ([#44](https://github.com/femiwiki/quibble-action/issues/44)) ([a214585](https://github.com/femiwiki/quibble-action/commit/a214585731ad69858468970bce09f046078b37f4))
* select Docker images from php-version and debian ([#26](https://github.com/femiwiki/quibble-action/issues/26)) ([db7cafb](https://github.com/femiwiki/quibble-action/commit/db7cafbb57790038fa0e13f5fdfa48ba599c6070))
* Skip selenium stage when the project has no selenium tests ([#46](https://github.com/femiwiki/quibble-action/issues/46)) ([dafc839](https://github.com/femiwiki/quibble-action/commit/dafc83975bd1fb4b443dc8439019c519f5f09426))
* upload Quibble logs as an artifact ([#29](https://github.com/femiwiki/quibble-action/issues/29)) ([cfc52af](https://github.com/femiwiki/quibble-action/commit/cfc52af113b34896708e528f93a67877c00152bf))


### Bug Fixes

* address zizmor security findings in action.yml ([#18](https://github.com/femiwiki/quibble-action/issues/18)) ([2b69fca](https://github.com/femiwiki/quibble-action/commit/2b69fca413701868e58f6bc18bbf815abb934ed2))
* correct phan docker image cache path ([#20](https://github.com/femiwiki/quibble-action/issues/20)) ([8a1dd02](https://github.com/femiwiki/quibble-action/commit/8a1dd020396f4fa840d39013f4648ef67ea71bce))
* default the phan stage to the mediawiki-phan-testrun image ([#49](https://github.com/femiwiki/quibble-action/issues/49)) ([ffc9227](https://github.com/femiwiki/quibble-action/commit/ffc9227efa59e085ef82243d81b122ec9c673e53)), closes [#48](https://github.com/femiwiki/quibble-action/issues/48)
* drop the phan-specific PHP version bump ([#50](https://github.com/femiwiki/quibble-action/issues/50)) ([0a60f70](https://github.com/femiwiki/quibble-action/commit/0a60f700df5391a123ceb4c7913ad98c0ac145ec))
* iterate over EXCLUDES in known-failures exclusion ([#21](https://github.com/femiwiki/quibble-action/issues/21)) ([b826e19](https://github.com/femiwiki/quibble-action/commit/b826e19cb3f91c404c442344a98859365f52f982))
* make Quibble logs readable before uploading them ([#34](https://github.com/femiwiki/quibble-action/issues/34)) ([a702a46](https://github.com/femiwiki/quibble-action/commit/a702a4664bfa524b913ab1f20e184bffc4610f35))
* Make Wikibase submodule URL fix branch-agnostic ([#45](https://github.com/femiwiki/quibble-action/issues/45)) ([6cdce58](https://github.com/femiwiki/quibble-action/commit/6cdce5833f7d82f9e003b0077c8bc5a7572343cf))
* modernize the coverage stage to the quibble-coverage image ([#37](https://github.com/femiwiki/quibble-action/issues/37)) ([614e10a](https://github.com/femiwiki/quibble-action/commit/614e10a4363fa08ecde20544a540888c6d08b1ef))
* use RUNNER_TEMP instead of hardcoded /home/runner ([#31](https://github.com/femiwiki/quibble-action/issues/31)) ([5b6ace3](https://github.com/femiwiki/quibble-action/commit/5b6ace3ed931097dd881ce2132994c2912b7f411)), closes [#6](https://github.com/femiwiki/quibble-action/issues/6)


### Reverts

* skip selenium stage when the project has no selenium tests ([#47](https://github.com/femiwiki/quibble-action/issues/47)) ([5cec8cc](https://github.com/femiwiki/quibble-action/commit/5cec8ccb1468bc91fd3a0e2b97e1ecf2d1506fa3))

## Changelog
