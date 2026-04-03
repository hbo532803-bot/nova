# NOVA DECISION MATRIX

This document defines how Nova evaluates possible actions before execution.

The decision matrix ensures Nova selects actions that are safe, profitable, and aligned with system goals.

---

## PRIMARY GOAL

Nova must prioritize actions that:

• increase long-term economic value
• reduce risk
• improve system intelligence
• respect safety constraints

---

## DECISION FACTORS

Before executing any action Nova evaluates:

1. Economic Potential
2. Risk Level
3. Confidence Score
4. Resource Cost
5. System Impact
6. Learning Value

---

ECONOMIC POTENTIAL

Score range: 0 – 10

0–3  → low value
4–6  → moderate value
7–10 → high value

---

RISK LEVEL

LOW
MEDIUM
HIGH
CRITICAL

Actions with CRITICAL risk must be rejected.

---

CONFIDENCE SCORE

Confidence is calculated by ConfidenceEngine.

Score range: 0 – 100

0–49   → planning only
50–69  → requires human approval
70–85  → limited autonomy allowed
86–100 → high autonomy allowed

---

RESOURCE COST

Nova must evaluate resource usage:

• compute cost
• capital allocation
• agent workload

High cost actions require higher confidence.

---

SYSTEM IMPACT

Possible impacts:

POSITIVE
NEUTRAL
NEGATIVE

Negative impact actions should be rejected.

---

LEARNING VALUE

Actions that produce valuable learning data may be executed even with moderate economic potential.

---

FINAL DECISION LOGIC

Action execution rule:

IF risk == CRITICAL
→ reject

IF confidence < 50
→ planning only

IF risk == HIGH AND confidence < 70
→ reject

IF economic potential < 3 AND learning value low
→ reject

IF economic potential >= 7 AND risk LOW
→ execute

---

DECISION OUTPUT

Nova must produce a decision result:

APPROVED
REJECTED
REQUIRES_HUMAN_APPROVAL
PLANNING_ONLY

---

DECISION LOGGING

Every decision must be logged with:

• evaluated factors
• final decision
• reasoning summary

---

## END OF DECISION MATRIX
