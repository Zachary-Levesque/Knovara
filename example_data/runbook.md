# Seets Gateway Runbook

The gateway buffers readings locally when the cloud API is unavailable. Retries
use bounded exponential backoff to avoid overwhelming small factory networks.

## Common Failure Modes

* Invalid readings should be rejected before upload.
* Cloud API timeouts should be retried with backoff.
* Batches older than the retention window should be marked stale.
* Repeated upload failures should create an operator-visible alert.

Before changing retry behavior, verify that local buffering, stale batch
handling, and alert creation still work together.
