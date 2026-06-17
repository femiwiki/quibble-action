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
      - uses: femiwiki/quibble-action@v1
```

### Choosing a stage

By default the `all` stage runs. Set `stage` to run a single Quibble stage, or
one of the two extra modes this action adds:

```yaml
      - uses: femiwiki/quibble-action@v1
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
        mediawiki-version: [REL1_43, master]
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3
      - uses: femiwiki/quibble-action@v1
        with:
          mediawiki-version: ${{ matrix.mediawiki-version }}
```

### Publishing coverage

```yaml
      - id: quibble
        uses: femiwiki/quibble-action@v1
        with:
          stage: coverage
          mediawiki-version: master
      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: coverage
          path: ${{ steps.quibble.outputs.coverage }}
```

## Inputs

| Name | Default | Description |
| --- | --- | --- |
| `mediawiki-version` | `REL1_43` | MediaWiki branch to test against, for example `master` or `REL1_43`. |
| `stage` | `all` | Stage to run. Any Quibble stage, or `phan` / `coverage`. |
| `exclude-known-failures` | `true` | Skip dependencies that are known to fail. |
| `exclude-dependencies` | (none) | Space-separated list of dependency names to skip. |
| `cache-key` | `true` | Mixed into every cache key; change it to bust the caches. |
| `docker-registry` | `docker-registry.wikimedia.org` | Registry that hosts the Quibble images. |
| `docker-org` | `releng` | Registry organization. |
| `quibble-docker-image` | `quibble-buster-php81` | Image used for most stages. |
| `coverage-docker-image` | `quibble-buster-php74-coverage` | Image used for the `coverage` stage. |
| `phan-docker-image` | `mediawiki-phan-php81` | Image used for the `phan` stage. |

## Outputs

| Name | Description |
| --- | --- |
| `coverage` | Path to the generated coverage directory (`/home/runner/cover`). |

## Requirements

A Linux runner with Docker available, for example `ubuntu-latest`. The action
pulls and runs the Wikimedia Quibble Docker images.

## License

[MIT](LICENSE)
