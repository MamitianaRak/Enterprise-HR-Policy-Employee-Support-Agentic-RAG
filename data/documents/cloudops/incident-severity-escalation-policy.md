# Incident Severity and Escalation Policy

## Purpose
This policy defines how production incidents are classified, who must be paged, and how quickly the team must respond. The on-call engineer assigns the initial severity and may raise or lower it as impact becomes clearer.

## Severity levels

| Severity | Definition | Examples | Response target |
|---|---|---|---|
| SEV1 | Full outage, confirmed data loss, security breach, or checkout/payments unavailable for all customers | Checkout API returns errors for all traffic; payment gateway unreachable; customer data exposed | Acknowledge within 5 minutes, incident commander assigned within 15 minutes |
| SEV2 | Major degradation: a key feature is broken or very slow for many customers | Checkout error rate above 5% for 5 minutes; payments latency p95 above 3 seconds | Acknowledge within 15 minutes |
| SEV3 | Partial or minor degradation with a workaround | One region slower than usual; a non-critical background job failing | Acknowledge within 1 hour, during business hours |
| SEV4 | Low impact or informational | Single-user issue, noisy alert, capacity planning question | Next business day |

## Who to page
- **SEV1**: on-call engineer, incident commander rotation, platform team lead, and the head of engineering. Open a dedicated incident channel and a customer-status-page draft immediately.
- **SEV2**: on-call engineer and the owning service team. Page the platform team if infrastructure (Kubernetes, load balancer, network) is involved.
- **SEV3 and SEV4**: create a ticket for the owning team; no page outside business hours.

## Communication
- Post an update in the incident channel at least every 30 minutes for SEV1 and every hour for SEV2.
- Customer-facing communication for SEV1 and SEV2 is approved by the incident commander before publication.
- Never share credentials, internal hostnames, or customer data in the incident channel.

## Closing an incident
An incident can be closed when metrics have been stable for at least 15 minutes after mitigation. A blameless postmortem is mandatory for every SEV1 and SEV2 and must be published within 5 business days.
