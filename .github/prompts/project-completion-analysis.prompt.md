---
description: Analyze the project completion status and feasibility from available evidence, then produce a structured summary for reporting or paper drafting.
---

# Project Completion and Feasibility Analysis

Use this prompt when you need Claude Code to analyze the current state of the project and determine:

1. What has been completed.
2. What remains incomplete.
3. Whether the project is feasible to finish within the current scope.
4. Which evidence files support the conclusion.

## Analysis Instructions

1. Read the project context from `CLAUDE.md` first.
2. Inspect the results directory for CSV summaries, logs, figures, and report files.
3. Compare the available results against the project’s intended milestones:
   - M1: runnability and environment validation
   - M2: baseline reproduction and strategy comparison
   - M3: branching-strategy ablation
   - M4: epsilon-grid trend validation
4. Judge completion using evidence, not intention.
5. Separate facts, interpretation, risks, and next steps.

## Required Output Structure

Provide the answer in this order:

1. Completion status summary.
2. Evidence-backed completed items.
3. Remaining gaps or risks.
4. Feasibility assessment.
5. Recommended next actions.

## Quality Rules

1. Mention file paths explicitly when referring to evidence.
2. Do not invent numbers or claim unverified completion.
3. If results are sufficient for a report but not for a publication, state that clearly.
4. If high-epsilon experiments are time-limited or use a different budget regime, note that boundary.
