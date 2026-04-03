# NOVA SYSTEM STATE MAP

This document defines the runtime states of the Nova system.

Nova operates as a state-driven system.

Each state defines what actions are allowed.

---

BOOTING

System is starting.

Allowed actions:
• initialize database
• load configuration
• restore agent states

Next state:
IDLE

---

IDLE

System waiting for tasks.

Allowed actions:
• receive commands
• schedule market scan
• wake agents

Possible transitions:
SCANNING_MARKET
PLANNING

---

SCANNING_MARKET

Market intelligence pipeline running.

Steps:
• generate niches
• collect signals
• detect patterns
• score opportunities
• generate proposals

Next state:
PLANNING

---

PLANNING

Nova evaluates possible actions.

Tasks:
• build execution plan
• run decision matrix
• check confidence score

Possible outcomes:
EXECUTING
REQUIRES_APPROVAL

---

EXECUTING

ExecutionEngine running tasks.

Tasks:
• assign agents
• run tools
• validate results

Possible transitions:
LEARNING
ERROR

---

LEARNING

System processes execution results.

Tasks:
• update reflection memory
• adjust confidence score
• update agent trust

Next state:
IDLE

---

HIBERNATING

Low activity state.

Tasks:
• suspend unused agents
• reduce compute usage

System wakes on:
• scheduled tasks
• new commands

---

ERROR

Failure handling state.

Tasks:
• rollback changes
• log incident
• reduce confidence score

Next state:
IDLE

---

FINAL RULE

State transitions must always be controlled by NovaBrainLoop.
