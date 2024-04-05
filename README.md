# Kitsune

![Status Sustain](https://img.shields.io/badge/Status-Sustain-green)

Kitsune is the platform that powers [SuMo (support.mozilla.org)](https://support.mozilla.org)

## Usage

It is a [Django](http://www.djangoproject.com/) application. There is [documentation](https://mozilla.github.io/kitsune/) online.

## Releasing a new version

-   Create a [signed tag](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work) for the new version.

    We are using [semantic versioning](https://semver.org/).

    Given a version number MAJOR.MINOR.PATCH, increment the:

        MAJOR version when you make incompatible API changes
        MINOR version when you add functionality in a backward compatible manner
        PATCH version when you make backward compatible bug fixes

    Example:

    `git tag -s 1.0.1 -m "Bump version: 1.0.0 to 1.0.1`

-   Draft a new release in GitHub for the new tag. Document the highlights of the release or use the option to automatically document the release through the commit history.

-   Trigger the release for the specified tag in the deploy repository.

> [!TIP]
> You can access the staging site at <https://support.allizom.org/>.

## Code of Conduct

By participating in this project, you're agreeing to uphold the [Mozilla Community Participation Guidelines](https://www.mozilla.org/en-US/about/governance/policies/participation/). If you need to report a problem, please see our [Code of Conduct](./CODE_OF_CONDUCT.md) guide.

## Contribute

See our [contribution guide](https://mozilla.github.io/kitsune/contributors), or dive into [setting up your development environment](https://mozilla.github.io/kitsune/hacking_howto/).

## Issues

We use [Bugzilla](https://bugzilla.mozilla.org/enter_bug.cgi?product=support.mozilla.org) for submitting and prioritizing issues.

## Thanks to all of our contributors ❤️

<a href = "https://github.com/mozilla/kitsune/contributors">
  <img src = "https://contrib.rocks/image?repo=mozilla/kitsune"/>
</a>
