# Seets Ownership Map

The Platform team owns the local gateway, cloud ingestion API, and normalized
event schema. Firmware engineers own edge sampling cadence and device
connectivity. Product operations owns alert thresholds and customer escalation
rules.

## Experts

* Gateway batching and retry policy: Senior platform engineer.
* Event schema and API contracts: Platform tech lead.
* Sensor firmware sampling: Firmware lead.
* Alert thresholds and operator workflows: Product operations partner.

When a change crosses firmware, gateway, and cloud API boundaries, the platform
tech lead should review the design before implementation.
