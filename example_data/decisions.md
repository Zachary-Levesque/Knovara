# Seets Architecture Decisions

## ADR-001: Start With a Local Gateway

The first prototype uses a local gateway instead of direct-to-cloud sensors.
Small manufacturing floors often have unreliable connectivity, and direct
sensor uploads would make retries and buffering harder to coordinate.

The gateway centralizes validation, batching, and upload retries. This reduces
firmware complexity and gives operators one place to inspect local telemetry
health.

## ADR-002: Normalize Events in the Cloud API

The cloud API stores normalized telemetry events rather than raw device payloads.
This makes dashboard queries simpler and keeps product analytics independent of
firmware-specific payload details.
