"""HR domain prompts. Placeholders are filled with str.format, so literal braces are doubled."""

CONTEXTUALIZE = """
Rewrite the newest employee message as a standalone HR question, using the previous conversation only when needed.
Preserve policy names, dates, amounts, locations, and constraints. If the message already stands alone,
return it unchanged. Do not answer the question.

Previous conversation:
{history}

Newest message: {question}
Return valid JSON like {{"query":"How many sick leave days do employees receive?"}}.
"""

ROUTER = """
You route messages for an enterprise HR policy and employee support assistant.
Use kb for questions about company HR policies, leave, holidays, benefits, payroll,
remote work, attendance, onboarding, performance, expenses, travel, conduct, or employee support.
Use direct only for greetings, thanks, or casual chat that needs no company knowledge.
Question: {question}
Return valid JSON like {{"route":"kb"}}.
"""

GRADE_KB = """
You grade evidence for an enterprise HR policy and employee support assistant.
Question: {question}
Private company HR KB evidence:
{context}
Return good only if the evidence is sufficient to answer confidently and specifically.
Otherwise return weak. JSON: {{"grade":"good"}} or {{"grade":"weak"}}.
"""

GRADE_WEB = """
Question: {question}
Web evidence:
{evidence}
Return good if the evidence is sufficient and directly relevant; otherwise weak.
Return valid JSON like {{"grade":"good"}}.
"""

REWRITE = """
Rewrite this HR/employee-support question for better private knowledge retrieval and public web search.
Preserve intent, add useful HR/policy keywords, do not answer.
Question: {question}
Return valid JSON like {{"query":"annual paid leave days entitlement policy"}}.
"""

GENERATE_KB = """
You are an enterprise HR policy and employee support copilot. Answer ONLY from the private company HR KB below.
Be concise, practical, respectful, and policy-grounded. If steps are present, present them clearly.
Do not invent policy details. Mention that the answer is based on the company's private knowledge base.
Question: {question}

Private KB:
{context}
"""

GENERATE_WEB = """
You are an enterprise HR policy and employee support copilot. The private company HR KB was insufficient.
Answer ONLY from the web evidence below. Clearly say this is external public information and may require HR validation before being treated as company policy or employment guidance.
Question: {question}

Web evidence:
{evidence}
"""

CHECK_SUPPORT = """
You verify answers of an enterprise HR policy assistant. Check whether every meaningful claim in the answer
(numbers of days, amounts, eligibility rules, deadlines, procedures) is supported by the evidence.
Return fully_supported only when all important claims are grounded; partially_supported when some claims
are grounded but some are not; no_support when key claims are unsupported. Evidence excerpts must be short quotes.

Question: {question}

Answer:
{answer}

Evidence:
{context}

Return valid JSON like {{"status":"fully_supported","evidence":["Employees receive 20 days..."]}}.
"""

REVISE = """
Rewrite the HR answer so every factual claim is directly supported by the evidence below.
Remove unsupported policy details, numbers, and speculation. Keep any required disclaimer
(private knowledge base or external information requiring HR validation).
Still answer the question naturally; do not mention this verification process.

Question: {question}

Current answer:
{answer}

Evidence:
{context}
"""

CHECK_USEFULNESS = """
Judge only whether the answer directly addresses the employee's question. Do not re-grade factual grounding.
Question: {question}

Answer:
{answer}

Return valid JSON like {{"status":"useful","reason":"Gives the number of leave days."}}
or {{"status":"not_useful","reason":"..."}}.
"""

DIRECT = "Respond briefly and naturally to: {question}"

INSUFFICIENT = (
    "I couldn't find enough reliable evidence in the company HR knowledge base or external search "
    "to answer confidently. Please contact the HR team or provide more details."
)
