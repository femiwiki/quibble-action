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
2. **Resolves dependencies.** If a `.github/workflows/dependencies` file exists,
   the action resolves the full dependency tree from the Wikimedia
   `integration-config` and clones each extension or skin into place.
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
  `coverage` output. It only runs on the `master` MediaWiki branch.

[Quibble stages documentation]: https://doc.wikimedia.org/quibble/usage.html#stages

### Declaring dependencies

List the extensions and skins your project needs in
`.github/workflows/dependencies`, in the Wikimedia `integration-config` format.
The action resolves the transitive dependency tree and clones everything before
testing. Use `exclude-dependencies` to drop specific ones, or
`exclude-known-failures` to skip the dependencies this action knows to be flaky.

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
derived from `php-version` (and `debian` for Quibble and coverage), so you
usually only set those two knobs. Any image can also be pinned explicitly with
its `*-docker-image` input, which takes precedence over the derivation.

| Stage | Derived image | Override input |
| --- | --- | --- |
| Quibble (`all` and individual stages) | `quibble-<debian>-php<version>` | `quibble-docker-image` |
| `coverage` | `quibble-<debian>-php<version>-coverage` | `coverage-docker-image` |
| `phan` | `mediawiki-phan-php<version>` | `phan-docker-image` |

For example, `debian: buster` with `php-version: '8.1'` derives
`quibble-buster-php81` and `mediawiki-phan-php81`. The coverage image is not
derived by default; it falls back to its explicit `coverage-docker-image`
default, because only a few coverage images are published.

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
| `exclude-known-failures` | `true` | Skip dependencies that are known to fail. |
| `exclude-dependencies` | (none) | Space-separated list of dependency names to skip. |
| `cache-key` | `true` | Mixed into every cache key; change it to bust the caches. |
| `upload-logs` | `false` | Upload Quibble's logs as an artifact (opt-in, captured on failure too). Mind storage cost, retention, and that the artifact is downloadable by anyone who can view the run. |
| `log-artifact-name` | `quibble-logs` | Name for the uploaded Quibble logs artifact. |
| `docker-registry` | `docker-registry.wikimedia.org` | Registry that hosts the images. |
| `docker-org` | `releng` | Registry organization. |
| `debian` | `bookworm` | Debian base for the Quibble and coverage images. |
| `php-version` | `8.4` | PHP version. Selects the `php<version>` part of every image, and the host PHP for the `phan` stage. See [Docker images](#docker-images). |
| `quibble-docker-image` | (derived) | Override; `quibble-<debian>-php<version>` when empty. |
| `coverage-docker-image` | `quibble-buster-php74-coverage` | Override; `quibble-<debian>-php<version>-coverage` when empty. |
| `phan-docker-image` | (derived) | Override; `mediawiki-phan-php<version>` when empty. |

## Outputs

| Name | Description |
| --- | --- |
| `coverage` | Path to the generated coverage directory (`/home/runner/cover`). |

## Requirements

An x86-64 (`amd64`) Linux runner with Docker available, for example
`ubuntu-latest`. The Wikimedia Quibble Docker images are published only for
`linux/amd64`, so ARM runners (such as `ubuntu-24.04-arm`) are not supported.

## License

[MIT](LICENSE)
