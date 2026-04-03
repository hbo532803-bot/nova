# NOVA SYSTEM CONTROL

This document defines the immutable architecture rules of Nova.

All AI coding tools must follow these rules.

Nova is an autonomous economic intelligence system designed to discover opportunities and run controlled experiments.

---

SYSTEM PURPOSE

Nova must:

• scan markets
• detect opportunities
• create experiments
• manage capital allocation
• learn from outcomes
• improve strategies

---

CORE LAYERS

User / Scheduler
↓
NovaBrainLoop
↓
NovaCore
↓
SupervisorAgent
↓
AgentRegistry
↓
ExecutionEngine
↓
Subsystems

---

SUBSYSTEMS

Market Engine
Economic Engine
Reflection Memory
Confidence Engine
Agent Factory

---

ARCHITECTURE RULES

1. All commands must pass through NovaCore
2. Execution must pass through SupervisorAgent
3. Agents cannot bypass ExecutionEngine
4. Safety gates must always run
5. Database access must use get_db()

---

SAFETY SYSTEMS

Kill Switch
Budget Guard
Permission Gate
Circuit Breaker

---

FINAL RULE

System stability is more important than new features.
