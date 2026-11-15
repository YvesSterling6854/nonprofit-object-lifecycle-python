from nonprofit_objects import lifecycle_rule
from infrai_client import client


BUCKET = "nonprofit-media-throwaways"
SWEEP_URL = "https://example.org/nonprofit/sweep"


def configure() -> None:
    infrai = client()
    infrai.storage.bucket.create(name=BUCKET)
    infrai.storage.bucket.set_lifecycle(BUCKET, rules=[lifecycle_rule(30)])
    job = infrai.cron.create(cron_expr="0 3 * * *", task=SWEEP_URL)
    print({"bucket": BUCKET, "job_id": job.get("job_id") if isinstance(job, dict) else job})


if __name__ == "__main__":
    configure()
