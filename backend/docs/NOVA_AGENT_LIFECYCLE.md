# NOVA AGENT LIFECYCLE

Nova agents are persistent workers.

Agents are never destroyed unless corrupted.

---

AGENT STATES

CREATED
ACTIVE
BUSY
IDLE
HIBERNATED
DEPRECATED
TERMINATED

---

STATE FLOW

CREATE → ACTIVE → BUSY → IDLE → HIBERNATE
HIBERNATE → WAKE → ACTIVE

---

HIBERNATE POLICY

Agents enter hibernation when:

• no task assigned
• resource optimization required
• domain inactive

---

WAKE POLICY

SupervisorAgent may wake agents if:

• task matches capability
• agent experience is valuable

---

AGENT MEMORY

Each agent maintains:

• task history
• trust score
• performance metrics
• reflection logs

---

MEMORY LIMITS

Agent memory must be compressed periodically.

Large memory sets must be archived.

---

TERMINATION RULE

Agents are terminated only when:

• corrupted
• obsolete
• replaced by superior agent
