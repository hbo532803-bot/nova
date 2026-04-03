# NOVA RUNTIME MAP

This document describes how commands flow inside Nova.

---

COMMAND ENTRY

Commands enter Nova through:

• API
• Dashboard
• Autonomous scheduler

---

COMMAND FLOW

User / Scheduler
↓
API Router
↓
NovaCore
↓
SupervisorAgent
↓
AgentRegistry
↓
Agents
↓
ExecutionEngine
↓
Subsystems

---

RUNTIME CYCLE

1 Scheduler triggers NovaBrainLoop
2 Brain loop observes system state
3 Strategic decision created
4 NovaCore builds plan
5 Supervisor validates plan
6 Agents execute tasks
7 ExecutionEngine runs action
8 Subsystem processes action
9 ReflectionMemory stores results
10 ConfidenceEngine updates trust

---

NO BYPASS RULE

No component may bypass:

NovaCore
SupervisorAgent
ExecutionEngine
