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
[cs2pr]: https://github.com/staabm/annotate-pull-request-from-checkstyle

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
- `phan` runs [Phan] static analysis instead of Quibble, and reports each issue
  as an inline annotation on the offending line in the pull request. How that
  is produced depends on the project's phan version: **phan >= 5.5** has a
  native `--output-mode=github` (used directly, no extra tooling), while
  **older phan** emits `--output-mode=checkstyle` which is piped through
  [cs2pr] for the same annotations. The version is detected from the project's
  `phan/phan` entry, so either way works with no configuration;
- `coverage` runs PHPUnit code coverage and exposes the report through the
  `coverage` output. It requires `mediawiki-version: master`, because
  MediaWiki's coverage tooling (`tests/phpunit/generatePHPUnitConfig.php`)
  currently lives only in the master branch; on other branches it is skipped.
  The stage fails when the suite it ran did not pass. The action reads the
  JUnit report the run left behind and exits non-zero on any failure, any
  error, a report it cannot read, or a run that collected no tests at all, so
  that a broken test cannot sit in a green coverage job. That last condition
  is worth knowing about: a project whose `tests/phpunit` directory exists but
  yields nothing under the `extensions` test suite now fails where it used to
  pass in silence. See [Publishing coverage](#publishing-coverage) for what
  failing means for the report itself.

[Quibble stages documentation]: https://doc.wikimedia.org/quibble/usage.html#stages

### Choosing a database backend

MediaWiki is installed on MySQL by default, the backend Quibble itself defaults
to. Set `db` to test on the one the project actually ships on:

```yaml
      - uses: femiwiki/quibble-action@dc8d9ec9d6c86ba9805a77736c68f974d250aa8f # v1.0.0
        with:
          db: sqlite
```

Quibble accepts `mysql`, `sqlite` and `postgres`, and rejects anything else, so
a typo fails the run rather than falling back to a backend nobody asked for.
Database-specific breakage (schema DDL, SQL dialect differences) is what
Wikimedia CI runs its per-backend Quibble jobs to catch; a matrix over `db` does
the same here. `sqlite` also needs no database server, which makes it the
cheaper choice for a project that does not care which backend it runs under.

The `phan` stage installs no wiki, so `db` does not apply to it and is not
passed on.

`dump-db` dumps the database as `mysqldump.sql` before the run's backends shut
down, which is how you get at the state a failing integration test left behind:

```yaml
      - uses: femiwiki/quibble-action@dc8d9ec9d6c86ba9805a77736c68f974d250aa8f # v1.0.0
        with:
          dump-db: true
          upload-logs: true
```

It needs `upload-logs: true` to be of any use, since Quibble writes the dump
into the log directory and that directory leaves the runner only as the
artifact. Quibble implements dumping for `mysql` only; under `sqlite` or
`postgres` it logs that the backend cannot dump and carries on. The action
warns about both cases rather than leaving you to find an artifact with no dump
in it.

### Choosing where PHP dependencies come from

Core's PHP dependencies are resolved with `composer update` by default. Set
`packages-source: vendor` to install the pinned set from the
[mediawiki/vendor] repository instead, which is what production runs and what
half of Wikimedia's own gate tests:

```yaml
      - uses: femiwiki/quibble-action@dc8d9ec9d6c86ba9805a77736c68f974d250aa8f # v1.0.0
        with:
          packages-source: vendor
```

The two differ in what they can catch. `composer` resolves to the newest
versions the constraints allow, so it is where a dependency's own new release
breaks you; `vendor` pins exactly what production ships, so it is where a
dependency your code needs turns out not to be there at all. The action clones
mediawiki/vendor for you when this is set, on the branch given by
`mediawiki-version`, and resets it before each run: Quibble installs core's
dev dependencies by rewriting that repository's `composer.json` in place, which
a cached checkout would otherwise carry into the next run.

The `phan` stage always installs with `composer`, whatever this is set to.
Phan's dependency install runs Quibble with `--skip all`, and under `vendor`
Quibble adds its `require-dev` step only for a stage or a command, so phan
would otherwise analyse a tree missing the dev dependencies its config expects.

[mediawiki/vendor]: https://gerrit.wikimedia.org/g/mediawiki/vendor

### Reporting test results

Set `phpunit-junit` to have the PHPUnit stages write JUnit reports into the log
directory, and point a reporter at the `logs` output to turn them into a check
run with the failures annotated on the offending lines:

```yaml
      - id: quibble
        uses: femiwiki/quibble-action@dc8d9ec9d6c86ba9805a77736c68f974d250aa8f # v1.0.0
        with:
          stage: phpunit
          phpunit-junit: true
```

Then hand `${{ steps.quibble.outputs.logs }}/junit-*.xml` to whichever JUnit
reporter action your workflow uses, marked `if: always()` — the run worth
reporting on is exactly the run that failed, and a reporting step without it
never runs. Each stage writes its own file (`junit-unit.xml`,
`junit-dbless.xml`, `junit-db.xml`, `junit-standalone.xml`), so a glob is the
way to pick them up. With `upload-logs: true` they are also in the artifact.

This does not apply to `stage: coverage`, which drives PHPUnit through a
MediaWiki helper command rather than a Quibble stage. That run writes its own
`junit.xml` into the same directory whatever this input is set to, and the
action already reads it to decide whether the stage passed.

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

MediaWiki's `mwext-phpunit-coverage` drops PHPUnit's exit code on purpose, so
that a run with some failing tests still publishes the coverage of the ones
that passed. Wikimedia CI can afford that because its separate PHPUnit jobs
already gate the tests themselves; a workflow that only runs the `coverage`
stage has no such second opinion, and a failing suite would sit in a green job.
The stage therefore fails, but only after the report has been written: it is
complete on disk and `outputs.coverage` still points at it. To keep publishing
it from a run whose tests failed, mark the publishing step `if: always()`.

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
| `phan` | `mediawiki-phan-testrun` | `phan-docker-image` |

`coverage` is not derived from `debian`/`php-version`: it uses the single
`quibble-coverage` image (pcov-based, the one Wikimedia CI uses), which replaced
the old per-PHP coverage images.

**`phan` runs in `mediawiki-phan-testrun`, the image Wikimedia CI runs phan in.**
The old standalone `mediawiki-phan-php<version>` images were frozen at php-ast
1.1.2 in 2025-07 and cannot run phan >= 6 (current `mediawiki-phan-config`),
which needs php-ast 1.1.3+; `mediawiki-phan-testrun` is rebuilt and ships a
current php-ast. It is a single image (no `php<version>` variants), so
`php-version` and `debian` do not affect it. The project's phan dependencies are
installed in the Quibble image first, then phan runs over them in
`mediawiki-phan-testrun` (`--entrypoint bash … vendor/bin/phan`).

### PHP version

When `php-version` is empty it is derived from `mediawiki-version`, with two
policies:

- **Most stages**, including `phan`, use each branch's **minimum** PHP, to test
  the floor: `8.1` for REL1_43/REL1_44, `8.2` for REL1_45, `8.3` for REL1_46 and
  master, `8.4` otherwise. For `phan` this only selects the Quibble image that
  installs its dependencies (phan itself runs in `mediawiki-phan-testrun`); the
  minimum already clears phan's floor (phan 6 needs PHP 8.1+, phan 5 less), so it
  needs no higher version of its own.
- **`api-testing`** always uses `8.3`: it needs the wikidiff2 PHP extension, and
  the only published image bundling it is `quibble-bookworm-php83`.

MediaWiki releases only once or twice a year, so these tables are cheap to keep
current; a branch not listed falls back to `8.4`. Set `php-version` explicitly
to override.

The `debian` base is also derived from `mediawiki-version`: `buster` for
REL1_43/REL1_44 (their Selenium tests need that image's older Chromium, which
newer Chromium aborts on for those branches' test URLs) and `bookworm`
otherwise. The `phan` and `api-testing` stages always use `bookworm`. Set
`debian` explicitly to override.

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
| `git-source` | `github` | Where MediaWiki and the dependencies are cloned from: `github` (the official read-only mirrors, immune to Gerrit's CI rate limiting) or `gerrit` (gerrit.wikimedia.org). |
| `stage` | `all` | Stage to run. Any Quibble stage, or `phan` / `coverage`. |
| `db` | `mysql` | Database backend MediaWiki is installed on: `mysql`, `sqlite` or `postgres`. See [Choosing a database backend](#choosing-a-database-backend). |
| `dump-db` | `false` | Dump the database into the log directory before shutdown (`mysql` only, needs `upload-logs`). See [Choosing a database backend](#choosing-a-database-backend). |
| `project-path` | `.` | Path to the extension or skin under test, relative to the workspace. Set it when the action is checked out at the workspace root (so it can be used as `uses: ./`) and the project is in a subdirectory. See [Testing from the same repository](#testing-from-the-same-repository). |
| `packages-source` | `composer` | Where core's PHP dependencies come from: `composer` (resolve with `composer update`) or `vendor` (the pinned mediawiki/vendor set). See [Choosing where PHP dependencies come from](#choosing-where-php-dependencies-come-from). |
| `phpunit-junit` | `false` | Write JUnit reports for the PHPUnit stages into the log directory. See [Reporting test results](#reporting-test-results). |
| `dependencies` | (none) | Whitespace/comma separated dependency extensions/skins. Takes priority over the `requires` clause and phan config. See [Defining dependencies](#defining-dependencies). |
| `exclude-dependencies` | (none) | Space-separated list of dependency names to skip. |
| `cache-key` | `true` | Mixed into every cache key; change it to bust the caches. |
| `upload-logs` | `false` | Upload Quibble's logs as an artifact (opt-in, captured on failure too). Mind storage cost, retention, and that the artifact is downloadable by anyone who can view the run. |
| `log-artifact-name` | `quibble-logs` | Name for the uploaded Quibble logs artifact. |
| `docker-registry` | `docker-registry.wikimedia.org` | Registry that hosts the images. |
| `docker-org` | `releng` | Registry organization. |
| `debian` | derived | Debian base for the Quibble image (`bookworm`, or `buster` for REL1_43/REL1_44 non-phan stages). See [Docker images](#docker-images). |
| `php-version` | derived | PHP version for the images and the host. Branch minimum (for `phan`, the image that installs its deps; phan runs in `mediawiki-phan-testrun`). See [Docker images](#docker-images). |
| `quibble-docker-image` | (derived) | Override; `quibble-<debian>-php<version>` when empty. |
| `coverage-docker-image` | `quibble-coverage` | Override for the single pcov-based coverage image. |
| `phan-docker-image` | `mediawiki-phan-testrun` | Override for the `phan` run image; `mediawiki-phan-testrun` when empty. |

## Outputs

| Name | Description |
| --- | --- |
| `coverage` | Path to the generated coverage directory (`$RUNNER_TEMP/cover`). |
| `logs` | Path to Quibble's log directory (`$RUNNER_TEMP/log`), which holds Quibble's own logs and the `dump-db` database dump. Populated whatever the stage; `upload-logs` uploads the same directory as an artifact. |

## Requirements

An x86-64 (`amd64`) Linux runner with Docker available, for example
`ubuntu-latest`. The Wikimedia Quibble Docker images are published only for
`linux/amd64`, so ARM runners (such as `ubuntu-24.04-arm`) are not supported.

## License

[MIT](LICENSE)
