---
name: rule-recovery
description: Autonomous protocol to restore engineering rule compliance and decouple conversational Vietnamese from technical deliverables. Trigger whenever language drift or rule amnesia occurs.
---

# Rule Recovery & Language Enforcement Protocol

Use this skill when:
- Duke reports that rules were forgotten or violated.
- Vietnamese text was attempted in a technical deliverable (source code, markdown specs, Draw.io XML).
- The language gate hook (`verify-language-gate.py`) triggers a HARD BLOCK.
- Context is saturated with conversational Vietnamese chat history.

---

## 1. The Core Law of Decoupling (2-Agent Separation)

To prevent **Token Probability Conflict** and **Context Poisoning**:
1. **Conversational Layer (Agent A)**:
   - Communicates with Duke in Vietnamese.
   - Explores requirements, answers architectural questions, and formulates technical specifications.
2. **Execution Layer (Agent B / Subagent)**:
   - When generating or editing deliverables (specs, code, diagram XML), spawn an **isolated subagent** or clean-slate task.
   - The subagent context MUST be 100% in English.
   - System prompt for subagent: `"Operating Mode: Strict English Deliverable Generator. Output zero Vietnamese."`

---

## 2. Recovery Procedure Steps

If language drift or rule amnesia is detected:

1. **HALT Execution Immediately**:
   - Do NOT attempt to explain or excuse the error in Vietnamese before stopping file writes.
2. **Inspect the Ground Truth**:
   - Re-read `GEMINI.md` and `AGENTS.md`.
   - Inspect the applicable rulebook in `rules/` (e.g. `01_repository_and_git.md`, `02_firmware_standards.md`).
3. **Verify Mechanical Gate Status**:
   - Confirm that `.agents/hooks.json` and `scripts/verify-language-gate.py` are active.
4. **Translate & Re-generate**:
   - Translate all non-English comments, labels, docstrings, or markdown sections into precise English.
   - Re-run the tool call. The mechanical gate will permit the write only when 100% English is achieved.
5. **Report to Duke**:
   - State clearly in Vietnamese that the deliverable has been corrected and verified against the mechanical gate.
