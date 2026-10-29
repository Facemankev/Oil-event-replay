# DAT-3 · EIA reconciliation review · 29 October 2026

**Recommendation: keep the current prices. Do not apply the three API-only
replacements, delete the 17 API-omitted observations, or fill the 137 API-only
dates. Primary EIA channels disagree. This is a review PR, not approval to change
canonical data.**

The owner supplied `eia-verification-new.json` after a successful authenticated
EIA API fetch. The report is preserved byte-for-byte with SHA-256
`4b0b690b2a12096789386519dc82d86700b7c9dfa41d68e36a3ba31190ce618b`.
It contains no key. This environment did not repeat that authenticated request:
we reviewed its results and independently checked **all 157 disputed date/series
pairs** against EIA's public historical tables without credentials.

## Actual report counts

| Series | Seed numeric records | Equal reported values | Different reported values | API-only rows | Seed-only rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| Brent | 5,231 | 5,219 | 3 | 40 | 9 |
| WTI | 5,137 | 5,129 | 0 | 97 | 8 |
| Total | 10,368 | 10,348 | 3 | 137 | 17 |

Report retrieval timestamps: Brent `2026-10-29T18:00:51.244720+00:00`,
WTI `2026-10-29T18:01:10.806961+00:00`. Requested coverage was
2006-01-03–2026-10-20. The API counts describe returned date rows, not necessarily
numeric observations: the summary report omits the values of its API-only rows.

## Every proposed value correction

| Brent date | Preserved seed | Reported API | EIA HTML table | API minus seed | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| 2016-12-28 | 54.95 | 53.93 | 54.95 | −1.02 | Hold; retain seed |
| 2016-12-29 | 54.97 | 54.95 | 54.97 | −0.02 | Hold; retain seed |
| 2018-04-16 | 72.05 | 73.18 | 72.05 | +1.13 | Hold; retain seed |

All values are USD/barrel. The official
[Brent daily history](https://www.eia.gov/dnav/pet/hist/RBRTED.htm), week of
26 December 2016 and week of 16 April 2018, corroborates the seeds. The API report
values also appear on earlier dates in that table (23 December 2016, 28 December
2016 and 13 April 2018 respectively). That suggests a possible date-alignment
issue, but **does not establish its cause**. A revision time, source bug or mirror
error cannot be inferred from these differences alone. No historical revision
has been established, and the original values must not be silently replaced.

## Missing observations versus unavailable prices

Every date is individually recorded in [REVIEW.json](REVIEW.json), with the
preserved seed value if any, API row state, HTML cell value, source URL, week/column
locator, checked date, classification and recommended action.

- **All 137 API-only rows correspond to blank cells in EIA's HTML tables.** There
  are zero confirmed numeric seed gaps among these rows. A blank is unavailable
  data, not zero and not a value to interpolate. The summary report alone cannot
  prove whether those API rows contain explicit nulls or numeric values conflicting
  with HTML; `API_value_state` remains `unknown_from_summary` until the retained
  response snapshot is inspected.
- **All 17 seed-only rows have published HTML prices equal to the seeds.** These
  are API omissions relative to another official EIA publication, not justification
  to delete observations. Their exact dates/values are listed below.
- Seven API-only date/series entries fall on 25 December or 1 January. These have
  calendar labels only; **no EIA holiday-closure reason is asserted**. The other
  blank weekdays also remain unavailable with an unknown cause. No exchange or
  publication calendar has been invented.
- Weekends do not become missing numeric observations simply because no daily
  row exists. This report does not establish a complete trading calendar or all
  historical reasons for publication gaps.

| Date | Brent seed / EIA HTML | WTI seed / EIA HTML |
| --- | ---: | ---: |
| 2014-09-30 | 94.67 | 91.17 |
| 2014-10-01 | 94.57 | 90.74 |
| 2014-10-02 | 91.29 | 91.02 |
| 2016-11-01 | 45.77 | Not an API-omission claim for WTI |
| 2022-10-25 | 91.76 | 86.93 |
| 2022-12-13 | 80.14 | 75.44 |
| 2023-03-07 | 83.03 | 77.45 |
| 2024-02-06 | 80.46 | 73.83 |
| 2024-04-16 | 91.29 | 86.15 |

## Reproduce the review without a key

```sh
python3 -m historical.reconcile --output work/eia-reviewed.json
python3 -m unittest discover -s tests -p 'test_reconciliation.py' -v
```

The command validates seed hashes, counts, date sets, old/new values, successful
fetch status and the official table transcriptions, then reproduces the committed
review. It has **no database-write or apply operation** and refuses an existing
output path. Re-running with another new output name yields identical bytes.
Never replace the original CSVs, change their pinned manifest hashes or rebuild
published exports just to make an API-only comparison pass.

For the actual sanitized response snapshots, the owner already has
`work/eia-reconciliation.sqlite` from the successful Windows verification. This
additional read-only command needs **no API key**:

```powershell
py -3 -m historical.reconcile --primary-db .\work\eia-reconciliation.sqlite --output .\work\eia-reviewed-with-snapshots.json
```

Run from a checkout/extracted copy of this PR that can access that file. Use its
full local path if it is in another project copy. Keep the database local; there
is no need to publish it. The reader requires the exact primary response hashes
recorded in the supplied report, checks the retained payload against SQLite rows,
and verifies the dates/value differences again. Explicit nulls become
`explicit_API_missing_and_HTML_blank`; numeric API values conflicting with blank
HTML stay primary-source conflicts. It never treats null as zero, asks for a key,
connects to the network or changes the database. A different/corrupt snapshot
fails closed. The snapshot reader is tested with clearly synthetic transport
fixtures, not claimed as an actual rerun of the owner's full API payload here.

## Evidence, reproducibility and remaining approval

- `eia-verification-new.json`: exact supplied report, including original source
  hashes and retrieval timestamps. Its 10,348 matching-value claims come from the
  owner's completed API run; raw responses are not attached here.
- `web-evidence.json`: 102 curated weekly rows transcribed through the browsing
  tool from the official [Brent](https://www.eia.gov/dnav/pet/hist/RBRTED.htm) and
  [WTI](https://www.eia.gov/dnav/pet/hist/RWTCD.htm) HTML histories. These are
  bibliographic numeric/blank-cell transcriptions with locators and check dates,
  not complete archived HTML pages or a substitute for the API snapshots.
- `REVIEW.json`: deterministic per-date analysis, hashes of both evidence files
  and a zero-change proposal. Table HTML checked on 29 October 2026 is a separate
  publication/vintage from the supplied API response; their disagreement remains
  open. Exact original market publication times and past vintages remain unknown.

**Next:** inspect the retained primary snapshot locally, then resolve the three
value conflicts and the API omissions against EIA's published history or an EIA
clarification. Review any proposed corrections/additions separately. If a price
change is eventually approved, import it as a new immutable version with its
source evidence; preserve the original seed/revision and explicitly rebuild and
retest downstream exports. No current dashboard, research result, matching
catalogue, database schema or default importer is changed by this PR. PR #16 and
PR #2 remain separate. No merge or data overwrite is authorized by this review.
