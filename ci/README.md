# CI-1: one required check for every draft and stacked PR

Issue #48, on #46. No application/source price/account changes, paid runner,
subscription or external market/news service. Existing browser tests remain intact.

`.github/workflows/required-checks.yml` runs for every PR opened, synchronized,
reopened or marked ready, with **no branch/path filter and no draft exclusion**.
It also supports merge queues. Its JSON notation is valid YAML and lets the
standard-library regression test inspect the actual trigger/job policy.

The stable status to require is **Market Ripple required checks**. It runs even
when a dependency fails/cancels, and passes only if offline and both browser jobs
succeed. No continue-on-error, empty suite or absent required page can silently
pass. Older branch-scoped workflows are retained; this gate provides universal
coverage for new draft stacks that inherit it.

## Coverage

- Offline Python/JavaScript tests, repeatable price/event/library imports, frozen
  SIM/LEARN and all parent report contracts, source/privacy checks.
- Every existing Chromium script, plus the new profile smoke test.
- Actual WebKit for integrated application, ripple, three answers/history,
  intelligence, free-data, SIM-1 and LEARN-1, plus profile smoke.
- Four approved research pages at desktop, actual iPhone/iPad **touch emulation**
  device profiles, light/dark themes, source drilldowns/navigation, responsive
  layouts and unchanged practice storage. Existing suites cover missing/conflicting
  data, fake provider responses, safe rendering and account invariants.
- A future `ipo/` frontend without an explicitly registered two-engine test fails
  preflight. No IPO frontend exists in this stack; absence is not claimed as tested.

Fonts and every external request are blocked at context level. Existing explicit
page fixture routes still supply their local provider responses. No live feed,
API key or real account participates. Legacy scripts using `browser.new_page()`
and explicit contexts both get the same instrumentation; application files are
never altered to accommodate the runner.

## Run and reproduce a failure

```sh
python3 -m pip install playwright==1.64.1
python3 -m playwright install --with-deps chromium webkit
# Existing Chromium scripts use /usr/bin/chromium; use the installed browser or
# the same CI symlink setup in the workflow.
python3 -m ci.offline_checks
python3 -m ci.check_capture --browser chromium
python3 -m ci.run_browser --browser chromium
python3 -m ci.run_browser --browser webkit
python3 -m ci.run_browser --browser webkit --only learning
```

Each suite has an explicit timeout and a nonzero child/timeout fails the runner.
`results.json`, `summary.md` and `test.log` give the exact reproduction command.
Failure screenshots and Playwright trace ZIPs are captured before contexts close;
`python3 -m playwright show-trace <trace.zip>` opens them locally. An intentional
fixture assertion proves the failing status, readable trace and screenshot exist;
its `controlled-capture` artifact is a harness self-test, not a product failure.
Successful traces are discarded; compact profile screenshots and logs are retained.
Artifacts use three-day retention/compression, not raw market databases/journals.

## Verified earlier runs and enforcement limit

Actual final-head logs were audited, not inferred from old PR descriptions:

- #45 / `6204a23`: run **44196715431**, 126 Python / 112 JavaScript, all offline
  contracts, **12 Chromium / 6 WebKit scripts**, including three-answer/free/SIM
  desktop/iPhone/iPad light/dark flows; successful.
- #46 / `4c42c7d`: run **44200068071**, 142 Python / 112 JavaScript, all offline
  contracts, **13 Chromium / 7 WebKit scripts**, adding LEARN; successful.

Their stale PR checklists were corrected without changing branches or draft state.
Physical iPhone/iPad Safari was **not tested**; engine emulation does not establish
physical-device acceptance. The extra all-page smoke coverage begins in CI-1.

The connected GitHub App's branch-protection read returned **403, Resource not
accessible by integration**. No repository setting was changed. Once reviewed and
merged, the owner should require **Market Ripple required checks** in main's branch
protection/ruleset, without allowing bypass. Until then this draft cannot activate
a default-branch workflow or prove organization-wide enforcement for older PR heads
that do not contain it. This PR and the stacked DATA-2 draft do run the actual gate.
No merge is authorized here; do not confuse implementation with activated protection.
