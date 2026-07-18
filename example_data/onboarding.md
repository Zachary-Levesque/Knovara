# Seets Engineering Onboarding

New backend engineers should begin with the gateway service because it is the
clearest path through the product. The gateway receives readings from edge
sensors, validates payload shape, batches events, and retries cloud uploads.

## First Week

1. Run the gateway locally with a fixture stream.
2. Trace one temperature reading from sensor input to cloud API request.
3. Read the retry policy before changing upload behavior.
4. Pair with the platform owner before modifying event schemas.

## Local Development

The gateway should fail closed when readings are malformed. Developers should
prefer small changes with unit tests around validation, batching, and retry
timing.
