# P1R-04 supplemental source re-review request — 2026-09-24

Status: `READY_FOR_INDEPENDENT_REVIEW`

The builder registered and selected official VBPL Word attachments for the six
records previously blocked by missing official sources. The four batches now
contain 20 source-backed proposals and zero blocked records. No review decision
was created or modified.

Review the six supplemental records and confirm the refreshed packet digests:

- `doc:10/2012/QH13` — `batch-01.json` `$.documents[0]`
- `doc:12/2012/QH13` — `batch-01.json` `$.documents[2]`
- `doc:25/2008/QH12` — `batch-02.json` `$.documents[0]`
- `doc:38/2013/QH13` — `batch-02.json` `$.documents[4]`
- `doc:58/2014/QH13` — `batch-03.json` `$.documents[2]`
- `doc:84/2015/QH13` — `batch-04.json` `$.documents[2]`

Pinned SHA-256 values:

- `batch-01.json`: `0036070b76f25062d682df5388e0abb214146f0f69af96f93bce24cba09e8887`
- `batch-02.json`: `b49d8b22ddbe788b655d66ed7ed6477be1ae60a72efe32c2af54f06dae9c786f`
- `batch-03.json`: `d50db9513423654bb5887a3a08274fbddeda86c469d5e16937bc75532d1e015f`
- `batch-04.json`: `e164d8ee362a0cff59e994f215a456be621c552d75db636324c99e3a7e1d0f7e`
- `evidence-index.json`: `824c914676431f2a1e42cb7907a58f7a969b88f4c9de98aab3373ba9bac98604`

Required checks:

1. Recompute source-byte, full-content and locator hashes for the six records.
2. Confirm each selected path is registered, bound to the correct document and
   points to the official VBPL record URL.
3. Confirm title, issued date and general effective date from the exact DOCX
   locators; retain the Article 124 exception on `58/2014/QH13`.
4. Do not create a verified v2 decision without a real reviewer identity,
   typed dependencies and a fresh dependency-bound input fingerprint.

CP-B, Gate 1, Phase 1 and Phase 2 remain unsigned regardless of this review.
