# Postmortem: Checkout Failures Caused by Redis Connection Exhaustion

**Severity:** SEV2 · **Duration:** 47 minutes · **Services:** checkout-api, Redis session cache

## Summary
After a release of checkout-api that increased the number of worker processes, checkout requests intermittently failed with 502 and timeout errors. Each worker opened its own Redis connection pool, and the Redis session cache reached its maximum client limit. New checkout sessions could not be created while existing ones continued to work.

## Timeline
- 14:02 Release of checkout-api with worker count raised from 4 to 12 per pod.
- 14:09 Checkout error rate rose above 5%; on-call engineer paged (SEV2).
- 14:15 Readiness probes were passing, so pods were not restarted, following the Checkout API runbook.
- 14:24 Application logs showed `ERR max number of clients reached` from Redis.
- 14:31 Rollback to the last known healthy image started, following the Production Deployment Rollback SOP.
- 14:49 Error rate back to normal; incident kept open for 15 minutes of stable metrics, then closed.

## Root cause
The total number of Redis connections is workers × pool size × pods. Tripling the worker count pushed this above the Redis `maxclients` setting. The change was not reviewed against Redis capacity.

## What went well
- The team checked readiness probes and logs before deleting pods, which preserved the evidence.
- The rollback followed the approved procedure and did not require database changes.

## Action items
1. Add an alert when Redis connected clients exceed 80% of `maxclients`.
2. Share one connection pool per pod instead of one per worker.
3. Add a pre-release check: any change to worker or replica counts must include a connection-budget estimate for Redis and PostgreSQL.

## Lessons for on-call engineers
When checkout fails right after a release and readiness probes pass, check dependency connection limits (Redis clients, PostgreSQL connection pool) in the logs before scaling up. Scaling up a release that exhausts connections makes the incident worse.
