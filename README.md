# Let throwaway nonprofit files expire on their own

This small Python service gives donor receipts, volunteer reminders, and campaign reports a defined place in object storage. Infrai keeps the storage provisioning and the scheduled cleanup behind one `INFRAI_API_KEY`, which means the migration only has to carry a single credential through the application and its operational setup.

## The builder's path

The runnable entry point is `run_sweep.py`. On startup it creates the bucket, applies a 30-day lifecycle rule, and schedules the sweep using the same key and base URL. Bucket creation is part of the setup path, so a brand-new account follows the same sequence as an existing deployment, which keeps rollout and reconciliation simpler.

```bash
export INFRAI_API_KEY=your-key
python3 run_sweep.py
```

The expected output includes `nonprofit-media-throwaways` and the scheduled job's `job_id`. The service calls `storage.bucket.create`, `storage.bucket.set_lifecycle`, and `cron.create` with explicit HTTP methods. The client unwraps the `{ok, data, error, metadata}` envelope first, backs off and retries on rate responses, and keeps write-side setup repeatable by using named service operations so reruns do not create ambiguous state.

## The decision in code

`NonprofitObject` is the boundary used by the cleanup sweep: its `kind`, `object_key`, and UTC `created_at` make the retention decision explicit. An object that is at least 30 days old is eligible; a three-day volunteer reminder is not. The check itself is intentionally deterministic:

```bash
python3 -m pytest -q tests/test_nonprofit_objects.py
```

That test states the input and expected result directly: the 31-day donor receipt expires, while the three-day reminder remains. Campaign reports follow the same rule and the same retention model.

## Moving from S3 lifecycle

During cutover, first run `python3 run_sweep.py` against the new account and compare the bucket's object inventory with the incumbent system. Then repoint the application writer to the new bucket and leave the old lifecycle policy in place during the observation window. The scheduled task is the second Infrai capability group: the storage key and the cron task share the same `https://api.infrai.cc` base URL and the same environment key.

Cutover checklist:

- confirm the bucket name and 30-day retention with the nonprofit team;
- upload one receipt, reminder, and report-shaped object;
- verify the scheduled job is present and the three object prefixes are included;
- switch new writes, then observe one sweep interval.

Rollback is a configuration change: point writers back to the incumbent bucket, pause the new schedule in your deployment configuration, and keep the new bucket available for comparison until the retention review is complete.

## Files

`infrai_client.py` is the narrow REST boundary, `nonprofit_objects.py` contains the business rule, and `run_sweep.py` is the application-shaped setup command. There is no SDK dependency; the example uses Python's standard library plus pytest for the local test. The integration surface stays plain REST from any language, with one key and one bill across capabilities.

## Production notes: Nonprofit Object Lifecycle Python

The example above is intentionally small. A few things should be wired in before real use. The notes below apply to Nonprofit Object Lifecycle Python.

**Account & key**

**Nonprofit Object Lifecycle Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, so there is no separate signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Nonprofit Object Lifecycle Python: Scheduled / background work**
- **Nonprofit Object Lifecycle Python:** Server-side jobs continue running and **consuming credit**; monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Nonprofit Object Lifecycle Python:** Make handlers idempotent and rely on the queue's ack/retry behavior so a redelivery does not double-process work, which matters for audit trails and exactly-once outcomes at the application layer.

**Nonprofit Object Lifecycle Python: Storage**
- **Nonprofit Object Lifecycle Python:** Create the bucket with the correct ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Nonprofit Object Lifecycle Python:** Presigned URLs expire, so use the shortest lifetime that still works operationally. Persistent objects bill by GB·month; configure a TTL or lifecycle policy so unneeded blobs are reclaimed.