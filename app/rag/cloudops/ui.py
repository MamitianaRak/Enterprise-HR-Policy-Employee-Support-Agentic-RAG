"""How the CloudOps domain presents itself in the web UI."""

UI = {
    "label": "CloudOps",
    "title": "CloudOps Incident Response",
    "tagline": "Private runbooks, SOPs and postmortems first. Web search only when internal evidence is insufficient. "
               "Follow-up questions keep the incident context.",
    "placeholder": "Describe the incident or ask an operations question…",
    "documents_label": "Runbooks & SOPs",
    "web_warning": "External guidance: not an approved internal procedure. Validate before applying it in production.",
    "accent": "#2563eb",
    "examples": [
        "Our checkout API is returning 502 errors after deployment. What should the on-call engineer check first?",
        "CPU on the payments service is above 90%. What is our recommended response procedure?",
        "What should I verify when a Kubernetes pod keeps restarting with CrashLoopBackOff?",
        "Which incidents count as SEV1 and who must be paged?",
    ],
}
