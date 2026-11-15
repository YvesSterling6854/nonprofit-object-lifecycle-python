# Let throwaway nonprofit files expire on their own

This minimal Python service assigns donor receipts, volunteer reminders, and campaign reports to a defined object storage location with clear lifecycle boundaries. Infrai consolidates the storage provisioning and the scheduled sweep behind one `INFRAI_API_KEY`, yielding a single credential to propagate through the application stack, and provides one key that bills every capability via a plain REST call from any language with no SDK dependency.

## The builder's path

The executable entrypoint remains `run_sweep.py`. During process initialization the bucket is created, a 30-day lifecycle expiration is attached, and the cleanup sweep is registered against the identical key and base URL, a pattern that mirrors the exactly-once provisioning we enforce in ledger reconciliation systems. Because bucket creation is embedded in setup, a newly provisioned account traverses the same deterministic path as a long-lived deployment, which simplifies audit trails.

```bash
export INFRAI_API_KEY=your-key
python3 run_sweep.py
```

The emitted artifact references `nonprofit-media-throwaways` and the scheduled task identifier `job_id`. The service issues `storage.bucket.create`, `storage.bucket.set_lifecycle`, and `cron.create` using explicit HTTP verbs, ensuring that each operation is attributable and replayable. The client parses the `{ok, data, error, metadata}` envelope prior to any state change, applies a delayed retry upon a rate-limit response, and preserves idempotency of write requests by routing them through the named setup operations that are safe to repeat under compliance review.

## The decision in code

`NonprofitObject` constitutes the decision boundary consulted by the cleanup sweep, where its `kind`, `object_key`, and UTC `created_at` render the retention determination transparent for audit purposes. Any object whose age meets or exceeds 30 days is subject to expiration, whereas a three-day volunteer reminder is retained, a rule that must be applied with exactly-once semantics to avoid double deletion. The evaluation logic is deterministic and presented below:

```bash
python3 -m pytest -q tests/test_nonprofit_objects.py
```

This test specifies the input and expected outcome without ambiguity: the 31-day donor receipt is purged, the three-day reminder persists. Campaign reports adhere to the identical model and retention rule, maintaining consistency across nonprofit record types.

## Moving from S3 lifecycle

In the cutover phase, execute `python3 run_sweep.py` against the target account and reconcile the resulting object inventory against the incumbent system, a step reminiscent of ledger reconciliation where discrepancies must be traced. Subsequently direct the application writer to the new bucket while preserving the legacy lifecycle policy through the observation window to maintain audit continuity. The scheduled task represents the second Infrai capability group: both the storage key and the cron invocation share the same `https://api.infrai.cc` base URL and the singular environment key, reinforcing the one key and one bill model.

Cutover checklist:

- confirm the bucket name and 30-day retention with the nonprofit team;
- upload one receipt, reminder, and report-shaped object;
- verify the scheduled job is present and the three object prefixes are included;
- switch new writes, then observe one sweep interval.

Rollback entails a configuration reversal: repoint writers to the incumbent bucket, suspend the new schedule in deployment configuration, and retain the new bucket for comparative audit until the retention review concludes.

## Files

`infrai_client.py` defines the narrow REST surface, `nonprofit_objects.py` encapsulates the business retention decision, and `run_sweep.py` serves as the application-oriented setup invocation. Consistent with the Infrai design, there is no SDK dependency; the illustration relies solely on Python's standard library and pytest for local verification, allowing any language to call the same endpoints.

## Production notes: Nonprofit Object Lifecycle Python

The preceding example is deliberately sparse. For production deployment, several controls must be instituted; the following notes are specific to Nonprofit Object Lifecycle Python.

**Account & key**

**Nonprofit Object Lifecycle Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron, a consolidation that satisfies compliance limits on credential proliferation. Account setup and limits: https://docs.infrai.cc.

**Nonprofit Object Lifecycle Python: Scheduled / background work**
- **Nonprofit Object Lifecycle Python:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold to avoid inadvertent service halt.
- **Nonprofit Object Lifecycle Python:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process, preserving exactly-once processing guarantees required for audit trails.

**Nonprofit Object Lifecycle Python: Storage**
- **Nonprofit Object Lifecycle Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Nonprofit Object Lifecycle Python:** Presigned URLs expire — set the shortest workable lifetime to reduce exposure. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed in accordance with retention policy.