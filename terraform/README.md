# terraform

Not built yet — Phase 5. State in GCS, not on the laptop.

What it creates:

- GCS bucket for the Parquet files
- Artifact Registry for the two images
- two Cloud Run services (api, web)
- one Cloud Run Job (ingest) + Cloud Scheduler trigger
- service accounts, least privilege

Order matters: deploy by hand with `gcloud` **first**, then codify. Writing Terraform for infra
that has never been stood up manually puts a layer between me and the error message, and a
service-account permission problem is a ten-minute fix at a prompt and a three-day fix through
plan/apply.

Then `terraform destroy && terraform apply` once, so "rebuildable from zero" is a verified fact
rather than a claim.
