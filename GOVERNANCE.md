# Governance

avenir-mcp is a small project with a single maintainer. This file says how decisions
are made, who does what, and what happens to the project if the maintainer can no
longer act.

## How decisions are made

- Every change is proposed in public: an issue for an idea or a bug, a pull request
  for code or documentation. Security reports are the exception: they go through a
  private [security advisory](SECURITY.md#reporting-a-vulnerability).
- Anyone may comment, review or propose. The discussion happens on the issue or the
  pull request, so the reasons stay with the change.
- The maintainer decides: what is merged, what goes on the [roadmap](ROADMAP.md), and
  when a version is released. A refusal comes with its reason.
- The rules a change must follow are written down, not decided case by case:
  [AGENTS.md](AGENTS.md) for the code, [CONTRIBUTING.md](CONTRIBUTING.md) for the
  process, the required checks of CI for everything that can be checked by a machine.
- A rule changes the same way as code: by a pull request that edits the file stating it.

With more than one maintainer, the maintainers decide together. A pull request
written by a maintainer is then merged after another maintainer's review; when they
disagree, the change waits until they agree.

## Roles

| Role | Who | Responsibilities |
|---|---|---|
| Maintainer | Mathieu Beal ([@mathbeal](https://github.com/mathbeal)) | decides what is merged and released; reviews pull requests (owner of every file in `CODEOWNERS`) as [CONTRIBUTING.md](CONTRIBUTING.md#code-review) describes; approves CI runs of first-time contributors; answers issues; handles vulnerability reports as [SECURITY.md](SECURITY.md) describes; cuts releases (changelog, tag, PyPI through Trusted Publishing, MCP registry); keeps the dependencies current with Renovate; enforces the [code of conduct](CODE_OF_CONDUCT.md) |
| Reviewer | anyone who comments on a pull request | reads the change against [AGENTS.md](AGENTS.md) and the checklist of [code review](CONTRIBUTING.md#code-review); says what is wrong and why; checks that the tests come with the change. A review informs the maintainer's decision; it does not merge |
| Contributor | anyone who opens an issue or a pull request | follows [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md); writes the tests first; signs off every commit ([DCO](https://developercertificate.org)); never shares real financial data or a token; follows the [code of conduct](CODE_OF_CONDUCT.md) |

## Becoming a maintainer

A contributor becomes a maintainer when the maintainers invite them, after several
merged pull requests and reviews that show they hold to [AGENTS.md](AGENTS.md). A
maintainer uses two-factor authentication on GitHub and PyPI. A maintainer who
stops can say so at any time; their access is then removed.

## Access continuity

Running the project needs these accesses:

| Access | What it allows |
|---|---|
| admin of the GitHub repository `mathbeal/avenir-mcp` | merge pull requests, close issues, read and publish security advisories, change the required checks and the repository's settings, publish a GitHub release, which runs the `publish` workflow; the documentation site is deployed from `main` by the `docs` workflow |
| owner of the PyPI project `avenir-mcp` | manage the Trusted Publisher that lets the `publish` workflow upload a release, yank a broken release |
| publishing to the MCP registry | update the `io.github.mathbeal/avenir-mcp` entry with each release |

So that the project can continue if the maintainer becomes unavailable, the credentials
and recovery codes for each of these accesses — the GitHub account, the PyPI account and
the GitHub login used for the MCP registry (`io.github.mathbeal`) — are held in the
maintainer's password manager with its **emergency-access** feature enabled for one
designated, trusted person, and are also kept in a sealed physical lockbox. That person
holds written authorization, legally sufficient where required (including for any domain
names), to use the accounts, merge changes, handle a vulnerability report and publish a
release, or to transfer ownership. The emergency-access waiting period and the lockbox are
set so that this person can create and close issues, accept proposed changes and publish a
release within a week of confirmation that the maintainer can no longer continue.

Whatever happens, the code stays usable: it is under the MIT licence, each release's
source is on PyPI, and everything needed to build, test, document and release it is in
the repository.

A second maintainer is still sought (see the [roadmap](ROADMAP.md)). Once found, they will
get the least privilege that lets them review, merge and cut a release — write, or maintain,
access on the repository — not standing admin; the admin role and the PyPI owner role reach
them through the continuity arrangement above, and only if the maintainer can no longer act.
This file will name them; from then on either maintainer can accept changes and publish a
release, which also raises the project's bus factor.
