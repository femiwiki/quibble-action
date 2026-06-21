# quibble-action

⏯️ Quibble is for setting up a MediaWiki instance and running various tests against it.

[![Linter](https://github.com/femiwiki/quibble-action/actions/workflows/linter.yaml/badge.svg)](https://github.com/femiwiki/quibble-action/actions/workflows/linter.yaml)
[![zizmor](https://github.com/femiwiki/quibble-action/actions/workflows/zizmor.yaml/badge.svg)](https://github.com/femiwiki/quibble-action/actions/workflows/zizmor.yaml)

A GitHub composite action that runs [Quibble] against a MediaWiki extension or
skin. It mirrors what Wikimedia CI does on Gerrit, but on GitHub Actions: it
clones MediaWiki core and your declared dependencies, sets everything up inside
the official Wikimedia [Quibble Docker images], and runs the test stage you ask
for. It can also run [Phan] static analysis and PHPUnit code coverage.

[Quibble]: https://doc.wikimedia.org/quibble/
[Quibble Docker images]: https://docker-registry.wikimedia.org/
[Phan]: https://github.com/phan/phan

## How it works

1. **Detects the project.** The action reads `extension.json` or `skin.json`
   from the checked-out repository to decide whether it is testing an extension
   or a skin, and under which name. When neither file is present it falls back
   to the Vector skin.
2. **Resolves dependencies.** Dependency extensions and skins are read from the
   `dependencies` input, the `requires` clause of `extension.json`/`skin.json`,
   or the phan config, and cloned into place. See
   [Defining dependencies](#defining-dependencies).
3. **Restores caches.** The Docker images, the MediaWiki checkout, and the
   Composer cache are all cached between runs.
4. **Runs the stage.** Quibble runs the requested stage inside the Docker image,
   or the action runs Phan or coverage for those two modes.

## Usage

Add a workflow to your extension or skin repository:

```yaml
name: Test
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3
      - uses: femiwiki/quibble-action@dc8d9ec9d6c86ba9805a77736c68f974d250aa8f # v1.0.0
```

### Choosing a stage

By default the `all` stage runs. Set `stage` to run a single Quibble stage, or
one of the two extra modes this action adds:

```yaml
      - uses: femiwiki/quibble-action@dc8d9ec9d6c86ba9805a77736c68f974d250aa8f # v1.0.0
        with:
          stage: phpunit
```

- any stage from the [Quibble stages documentation] (for example `phpunit`,
  `selenium`, `qunit`);
- `phan` runs [Phan] static analysis instead of Quibble;
- `coverage` runs PHPUnit code coverage and exposes the report through the
  `coverage` output. It requires `mediawiki-version: master`, because
  MediaWiki's coverage tooling (`tests/phpunit/generatePHPUnitConfig.php`)
  currently lives only in the master branch; on other branches it is skipped.

[Quibble stages documentation]: https://doc.wikimedia.org/quibble/usage.html#stages

### Defining dependencies

Dependency extensions and skins are resolved from the **first** of these sources
that yields anything:

1. **The `dependencies` input** — a whitespace/comma separated list:

   ```yaml
   with:
     dependencies: Foo Bar skins/Vector
   ```

   Entries may be bare names (`Foo` → `mediawiki/extensions/Foo`), short prefixed
   paths (`skins/Vector`), or full Gerrit paths.

2. **The `requires` clause of `extension.json` / `skin.json`** — the
   `requires.extensions` and `requires.skins` keys.

3. **The phan config (`.phan/config.php`)** — `../../extensions/<Name>` and
   `../../skins/<Name>` entries in the directory/file list.

Use `exclude-dependencies` to drop specific resolved entries by name.

### Testing several MediaWiki versions

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        mediawiki-version: [REL1_45, master]
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3
      - uses: femiwiki/quibble-action@dc8d9ec9d6c86ba9805a77736c68f974d250aa8f # v1.0.0
        with:
          mediawiki-version: ${{ matrix.mediawiki-version }}
```

### Testing from the same repository

By default the action treats the workspace root as the project under test, so a
consumer just checks out their repository and runs the action. When the action
itself lives at the workspace root, for example to test it as `uses: ./`, check
the project under test out into a subdirectory and point `project-path` at it:

```yaml
      # The action under test at the workspace root, so it can be `uses: ./`.
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3
      # The extension or skin under test in a subdirectory.
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3
        with:
          repository: my-org/MyExtension
          path: project
      - uses: ./
        with:
          project-path: project
```

### Publishing coverage

```yaml
      - id: quibble
        uses: femiwiki/quibble-action@dc8d9ec9d6c86ba9805a77736c68f974d250aa8f # v1.0.0
        with:
          stage: coverage
          mediawiki-version: master
      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: coverage
          path: ${{ steps.quibble.outputs.coverage }}
```

## Docker images

Every stage runs in an official Wikimedia image, pulled as
`<docker-registry>/<docker-org>/<image>:<tag>`. By default the `<image>` is
derived from `php-version` (and `debian` for Quibble), so you usually only set
those two knobs. Any image can also be pinned explicitly with its
`*-docker-image` input, which takes precedence over the derivation.

| Stage | Image | Override input |
| --- | --- | --- |
| Quibble (`all` and individual stages) | `quibble-<debian>-php<version>` | `quibble-docker-image` |
| `coverage` | `quibble-coverage` | `coverage-docker-image` |
| `phan` | `mediawiki-phan-php<version>` | `phan-docker-image` |

For example, `debian: buster` with `php-version: '8.1'` derives
`quibble-buster-php81` and `mediawiki-phan-php81`. Coverage is not derived from
`debian`/`php-version`: it uses the single `quibble-coverage` image (pcov-based,
the one Wikimedia CI uses), which replaced the old per-PHP coverage images.

When `php-version` is empty it is derived from `mediawiki-version`, matching
each MediaWiki branch's minimum PHP: `8.1` for REL1_43/REL1_44, `8.2` for
REL1_45, `8.3` for REL1_46 and master, and `8.4` for anything else. MediaWiki
releases only once or twice a year, so this table is cheap to keep current; a
branch not listed falls back to `8.4`, so set `php-version` explicitly when
testing older branches. The `api-testing` stage always uses `8.3`: it requires
the wikidiff2 PHP extension, and the only published Quibble image that bundles
it is `quibble-bookworm-php83`. Setting `php-version` (or `quibble-docker-image`)
explicitly overrides all of this.

The `debian` base is derived from `mediawiki-version` the same way: `buster`
for REL1_43/REL1_44 (their Selenium tests need that image's older Chromium,
which newer Chromium aborts on for those branches' test URLs) and `bookworm`
otherwise; `api-testing` always uses `bookworm`. Set `debian` explicitly to
override.

Available bases and versions are whatever the
[Wikimedia Docker registry](https://docker-registry.wikimedia.org/) publishes,
so not every `debian` / `php-version` combination exists. For example, to pin an
older PHP, such as when testing an older MediaWiki branch:

```yaml
      - uses: femiwiki/quibble-action@dc8d9ec9d6c86ba9805a77736c68f974d250aa8f # v1.0.0
        with:
          debian: buster
          php-version: '8.3'
```

## Inputs

| Name | Default | Description |
| --- | --- | --- |
| `mediawiki-version` | `REL1_45` | MediaWiki branch to test against, for example `master` or `REL1_43`. |
| `stage` | `all` | Stage to run. Any Quibble stage, or `phan` / `coverage`. |
| `project-path` | `.` | Path to the extension or skin under test, relative to the workspace. Set it when the action is checked out at the workspace root (so it can be used as `uses: ./`) and the project is in a subdirectory. See [Testing from the same repository](#testing-from-the-same-repository). |
| `dependencies` | (none) | Whitespace/comma separated dependency extensions/skins. Takes priority over the `requires` clause and phan config. See [Defining dependencies](#defining-dependencies). |
| `exclude-dependencies` | (none) | Space-separated list of dependency names to skip. |
| `cache-key` | `true` | Mixed into every cache key; change it to bust the caches. |
| `upload-logs` | `false` | Upload Quibble's logs as an artifact (opt-in, captured on failure too). Mind storage cost, retention, and that the artifact is downloadable by anyone who can view the run. |
| `log-artifact-name` | `quibble-logs` | Name for the uploaded Quibble logs artifact. |
| `docker-registry` | `docker-registry.wikimedia.org` | Registry that hosts the images. |
| `docker-org` | `releng` | Registry organization. |
| `debian` | derived from `mediawiki-version` | Debian base for the Quibble image (`buster` for REL1_43/REL1_44, else `bookworm`). See [Docker images](#docker-images). |
| `php-version` | derived from `mediawiki-version` (`8.3` for `api-testing`) | PHP version. Selects the `php<version>` part of every image, and the host PHP for the `phan` stage. See [Docker images](#docker-images). |
| `quibble-docker-image` | (derived) | Override; `quibble-<debian>-php<version>` when empty. |
| `coverage-docker-image` | `quibble-coverage` | Override for the single pcov-based coverage image. |
| `phan-docker-image` | (derived) | Override; `mediawiki-phan-php<version>` when empty. |

## Outputs

| Name | Description |
| --- | --- |
| `coverage` | Path to the generated coverage directory (`$RUNNER_TEMP/cover`). |

## Requirements

An x86-64 (`amd64`) Linux runner with Docker available, for example
`ubuntu-latest`. The Wikimedia Quibble Docker images are published only for
`linux/amd64`, so ARM runners (such as `ubuntu-24.04-arm`) are not supported.

## License

[MIT](LICENSE)
