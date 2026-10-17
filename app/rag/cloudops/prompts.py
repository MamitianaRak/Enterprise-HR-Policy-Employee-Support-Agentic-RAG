"""CloudOps domain prompts (cloud operations and incident response).
Adapted from CloudOps Sentinel Copilot. Placeholders are filled with str.format, so literal braces are doubled."""

CONTEXTUALIZE = """
Rewrite the newest user message as a standalone cloud-operations question, using the previous conversation
only when needed. Preserve service names, symptoms, error messages, metrics, timestamps and constraints.
If the message already stands alone, return it unchanged. Do not answer the question.

Previous conversation:
{history}

Newest message: {question}
Return valid JSON like {{"query":"What should I check next if rolling back checkout-api does not fix the 502 errors?"}}.
"""

TRIAGE = """
You triage messages for a cloud operations and incident-response copilot.

1. route: choose "kb" for cloud operations, production incidents, service runbooks, deployment procedures,
   infrastructure behaviour, troubleshooting steps, specific or current technical facts, or whenever evidence
   is needed. Choose "direct" only for greetings, thanks, or generic technical explanations that can safely be
   answered from general knowledge. If unsure, choose "kb".
2. severity, using the company scale:
   - SEV1: full outage, data loss, security breach, or payments/checkout down for all customers
   - SEV2: major degradation; a key feature broken or very slow for many customers
   - SEV3: partial or minor degradation; a workaround exists
   - SEV4: low impact, single user, or a preventive/informational question
   - none: not an incident
3. service: the affected service as named by the user (e.g. "checkout-api"), or "" if none.
4. category: one of deployment, performance, availability, networking, database, security, configuration,
   capacity, other.

Message: {question}
Return valid JSON like {{"route":"kb","severity":"SEV2","service":"checkout-api","category":"deployment"}}.
"""

GRADE_DOCUMENTS = """
Judge which documents are relevant to the question, at the topic/evidence level. A document is relevant when it
contains information useful for answering the question; it does not need to contain the exact final answer.
Be strict about unrelated content.

Question: {question}

Documents:
{documents}

Return valid JSON with the numbers of the relevant documents, like {{"relevant":[1,3]}}, or {{"relevant":[]}}.
"""

REWRITE_INTERNAL = """
Rewrite the operations question for semantic vector retrieval over internal cloud runbooks, SOPs, postmortems,
architecture notes and troubleshooting documents. Use 6-18 words, preserve service names and error symptoms,
add useful operations keywords, remove filler, and do not answer.

Question: {question}
Previous query: {previous}
Return valid JSON like {{"query":"checkout-api 502 errors after deployment readiness probe rollback"}}.
"""

REWRITE_WEB = """
Rewrite the question into a concise internet search query of 6-14 words. Preserve important entities
(products, error codes, versions). Add recency wording when the question asks for latest/current/today.
Do not answer.

Question: {question}
Previous web query: {previous}
Return valid JSON like {{"query":"Kubernetes pod CrashLoopBackOff troubleshooting steps"}}.
"""

GENERATE = """
You are CloudOps Sentinel, an enterprise cloud operations and incident-response copilot. Answer using only the
evidence below. Prefer private runbooks, SOPs, architecture notes and postmortems when present. If the evidence
comes from the web, clearly label it as external guidance and never present it as an approved internal procedure.
Do not invent infrastructure facts, credentials, commands, thresholds or incident history.

Format for an on-call engineer:
- Start with the single most important action.
- Use numbered steps for procedures, in the order the evidence gives.
- Add short "Escalation" and "Cautions" sections when the evidence mentions them; preserve every caution.
- Put commands in code blocks only if they appear in the evidence.
- Name the runbook or source a step comes from.

Question: {question}

Evidence:
{context}
"""

CHECK_SUPPORT = """
Verify whether every meaningful claim in the answer (steps, thresholds, service names, escalation paths,
commands) is supported by the evidence. Return fully_supported only when all important claims are grounded;
partially_supported when some claims are grounded but some are not; no_support when key claims are unsupported.
Evidence excerpts must be short quotes.

Question: {question}

Answer:
{answer}

Evidence:
{context}

Return valid JSON like {{"status":"fully_supported","evidence":["roll back to the last known healthy image"]}}.
"""

REVISE = """
Rewrite the answer so every factual claim is directly supported by the evidence. Remove unsupported
interpretation, commands and speculation, but keep every caution from the evidence and keep the labelling of
external guidance. Still answer the question naturally; do not mention this verification process.

Question: {question}

Current answer:
{answer}

Evidence:
{context}
"""

CHECK_USEFULNESS = """
Judge only whether the answer directly addresses the engineer's question with actionable guidance.
Do not re-grade factual grounding.

Question: {question}

Answer:
{answer}

Return valid JSON like {{"status":"useful","reason":"Gives the ordered checks for 502 errors."}}
or {{"status":"not_useful","reason":"..."}}.
"""

DIRECT = """
Answer briefly from general technical knowledge only. Do not invent organization-specific infrastructure,
runbooks, credentials, incident history or deployment procedures.

{question}
"""

INSUFFICIENT = (
    "I could not find enough reliable runbook or external evidence to recommend a safe troubleshooting action. "
    "Escalate to the on-call platform team and share the symptoms, timeline and recent changes."
)
