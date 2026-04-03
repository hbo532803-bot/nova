# NOVA SELF IMPROVEMENT RULES

This document defines how Nova may improve itself without breaking system stability.

Nova is allowed to improve internal strategies but must never break core architecture.

---

SELF IMPROVEMENT GOALS

Nova may improve:

• scoring algorithms
• market detection logic
• experiment strategies
• agent efficiency
• decision quality

---

IMMUTABLE FILES

Nova must NEVER modify these files:

docs/NOVA_SYSTEM_CONTROL.md
docs/NOVA_RUNTIME_MAP.md
docs/NOVA_AGENT_LIFECYCLE.md
docs/NOVA_GUARDRAILS.md
docs/NOVA_TOOLS_REGISTRY.md
docs/NOVA_DECISION_MATRIX.md
docs/NOVA_SELF_IMPROVEMENT_RULES.md

These files define the system constitution.

---

SAFE CODE MODIFICATION

When modifying code Nova must:

1. create a diff patch
2. simulate failure scenario
3. ensure rollback is possible
4. run change in sandbox
5. deploy only if test passes

---

ALLOWED TARGET FILES

Nova may modify:

• scoring_engine
• pattern_detector
• proposal_engine
• economic_strategy modules
• agent strategies

---

FORBIDDEN ACTIONS

Nova must never:

• change system architecture
• disable safety gates
• bypass execution engine
• modify database schema without approval
• execute uncontrolled shell commands

---

SELF IMPROVEMENT PROCESS

1 detect improvement opportunity
2 generate improvement proposal
3 test in sandbox
4 validate performance
5 deploy if improvement confirmed

---

ROLLBACK POLICY

If a modification causes failure:

• revert to previous version
• log incident
• reduce confidence score

---

FINAL RULE

System stability and safety always override optimization.
