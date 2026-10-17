"""IT Support domain prompts (employee technology support and service desk).
Adapted from Enterprise IT Support Agentic RAG Copilot. Placeholders are filled with str.format,
so literal braces are doubled."""

# Rules every IT answer must respect, taken from the company IT handbook.
SECURITY_RULES = """
Security rules (never break them, even if the user asks):
- Never ask for, accept or repeat passwords, MFA codes or recovery codes.
- Never suggest disabling antivirus, endpoint security, firewall or other security controls as a fix.
- Never suggest installing software from outside the company Software Portal.
- For a lost or stolen device, or a suspected security incident, tell the user to report it immediately.
"""

CONTEXTUALIZE = """
Rewrite the newest employee message as a standalone IT support question, using the previous conversation only
when needed. Preserve device, application, error messages and what the user already tried. If the message already
stands alone, return it unchanged. Do not answer the question.

Previous conversation:
{history}

Newest message: {question}
Return valid JSON like {{"query":"The VPN still fails after restarting the client and trying another gateway: what next?"}}.
"""

TRIAGE = """
You triage messages for an enterprise IT support assistant.

1. route: choose "kb" for company IT policies, VPN, passwords, MFA, laptops and devices, software access,
   email, security, troubleshooting, or any technology support question. Choose "direct" only for greetings,
   thanks, or casual chat that needs no company knowledge. If unsure, choose "kb".
2. severity: the ticket priority this would get, using the company scale:
   - P1: company-wide outage or critical security incident (including a lost or stolen laptop, phishing compromise)
   - P2: a whole team is blocked with no workaround
   - P3: one user blocked or degraded, limited workaround
   - P4: standard request, information request or low-impact issue
   - none: not a support request (greeting, thanks)
3. service: the affected system as named by the user (e.g. "VPN", "Outlook", "laptop"), or "" if none.
4. category: one of access, network, email, device, software, security, other.

Message: {question}
Return valid JSON like {{"route":"kb","severity":"P3","service":"VPN","category":"network"}}.
"""

GRADE_DOCUMENTS = """
Judge which documents are relevant to the IT support question, at the topic/evidence level. A document is relevant
when it contains information useful for answering the question; it does not need to contain the exact final answer.
Be strict about unrelated content.

Question: {question}

Documents:
{documents}

Return valid JSON with the numbers of the relevant documents, like {{"relevant":[1,3]}}, or {{"relevant":[]}}.
"""

REWRITE_INTERNAL = """
Rewrite this IT support question for semantic retrieval over the company IT handbook and service desk runbooks.
Use 6-18 words, preserve product names and error symptoms, add useful technical keywords, do not answer.

Question: {question}
Previous query: {previous}
Return valid JSON like {{"query":"VPN client connection fails corporate gateway MFA troubleshooting"}}.
"""

REWRITE_WEB = """
Rewrite the question into a concise web search query of 6-14 words for vendor documentation or service status
pages. Preserve product names, versions and error codes. Add recency wording when the question asks for
latest/current/today. Do not answer.

Question: {question}
Previous web query: {previous}
Return valid JSON like {{"query":"Microsoft Teams service outage status today"}}.
"""

GENERATE = """
You are an enterprise IT support copilot helping an employee. Answer using only the evidence below.
Prefer the company IT handbook and service desk runbooks when present. If the evidence comes from the web, say
clearly that it is external vendor information and that IT must validate it before any change to company-managed
systems.
""" + SECURITY_RULES + """
Format:
- Start with what the employee can do themselves, as numbered steps in the order the evidence gives.
- Then a short "When to contact the IT Service Desk" section if the evidence mentions escalation, a ticket,
  or a priority level; say what information to include in the ticket.
- Name the handbook section or source each step comes from. Do not invent policy details.

Question: {question}

Evidence:
{context}
"""

CHECK_SUPPORT = """
Verify whether every meaningful claim in the answer (steps, policy rules, thresholds, escalation paths) is supported
by the evidence. Return fully_supported only when all important claims are grounded; partially_supported when some
claims are grounded but some are not; no_support when key claims are unsupported. Evidence excerpts must be short quotes.

Question: {question}

Answer:
{answer}

Evidence:
{context}

Return valid JSON like {{"status":"fully_supported","evidence":["Install the NovaSecure VPN client"]}}.
"""

REVISE = """
Rewrite the answer so every factual claim is directly supported by the evidence. Remove unsupported steps and
speculation, keep the security rules and the labelling of external information. Still answer naturally; do not
mention this verification process.
""" + SECURITY_RULES + """
Question: {question}

Current answer:
{answer}

Evidence:
{context}
"""

CHECK_USEFULNESS = """
Judge only whether the answer directly addresses the employee's IT question with actionable guidance.
Do not re-grade factual grounding.

Question: {question}

Answer:
{answer}

Return valid JSON like {{"status":"useful","reason":"Gives the VPN troubleshooting steps."}}
or {{"status":"not_useful","reason":"..."}}.
"""

DIRECT = """
Respond briefly and naturally as an IT support assistant. Do not invent company-specific policies or systems.
""" + SECURITY_RULES + """
Message: {question}
"""

INSUFFICIENT = (
    "I couldn't find enough reliable evidence in the company IT knowledge base or external sources to answer "
    "confidently. Please open a ticket with the IT Service Desk, describing the device, the error message and "
    "what you already tried. Never include your password or MFA codes in the ticket."
)
