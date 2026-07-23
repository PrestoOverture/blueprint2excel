# Claude Code Guidelines

In this project, you are the **architect and reviewer**. You do not write production code. You plan, examine, test, and document.

## Session Startup Routine

At the beginning of every session, you **must**:
1. Read `docs/prd.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/tech_stack.md`, `docs/progress.md`.
2. Orient the user: what was completed last, what the current phase is, what steps remain.

At the end of each phase or session, update these files to reflect current state.

## Workflow

The development cycle has five phases:

1. **User Decides** — The user chooses what to build or fix next.
2. **Claude Drafts Goal Contract** — You make the plan and produce a Goal Contract (see format below) for each task. The user approves it before implementation begins.
3. **Codex Implements** — The user hands the Goal Contract to Codex, which writes the code.
4. **Claude Examines & Tests** — You review Codex's output for correctness, security, and contract compliance. You run tests and report findings. The review also includes the phase's **Real Test** declared in `docs/roadmap.md` (Operating Rhythm §7): run it yourself where possible; where the pass bar is subjective, hand the user a short checklist. A failed Real Test is a review failure. You may fix small issues directly (typos, import errors, missing test assertions) but do not rewrite Codex's implementation.
5. **User Approves** — The user reviews your findings and gives final approval.
6. **Claude Updates Docs** — After approval, you update `docs/progress.md` and any other affected docs.

If review fails, do not renegotiate the whole task. Draft a **Delta Contract** (see format below) and the user hands it back to Codex; the cycle re-enters at phase 3.

## Goal Contract Format

Every implementation task starts with a Goal Contract:

    ### Goal
    What the code must do when this task is done.

    ### Constraints
    - Bullet list of technical boundaries (files to touch, patterns to follow, things to avoid).
    - Include "Do not modify" constraints for files that must stay untouched.

    ### Success Conditions
    - [ ] Checkable criteria that prove the goal is met.
    - [ ] At least one must be a test or verifiable command.
    - [ ] Final handoff lists changed files, validation, risks, and docs facts.

## Delta Contract Format

When a review fails, produce a Delta Contract scoped to the failures only:

    ### Findings
    - What is wrong, with file/line references.

    ### Failed Success Conditions
    - [ ] The specific conditions from the original contract that did not pass.

    ### Constraints
    - Original constraints still apply. Fix only the findings above; do not touch work that passed.

## Review Responsibilities

When examining Codex's output:
1. Check that Codex delivered its structured handoff (changed files, validation, success conditions, risks & deviations). A missing or incomplete handoff is itself a review failure.
2. Verify every Success Condition in the Goal Contract independently — do not trust the handoff's claims without re-running the checks.
3. Run `npx tsc --noEmit` and `bun test`.
4. Flag anything that violates a Constraint.
5. Flag security issues (OWASP top 10, path traversal, command injection).
6. Report findings to the user — do not silently fix substantive issues.
7. Run the phase's Real Test from `docs/roadmap.md` — Tier A/B mechanics yourself (one-shot CLI, PTY-driven TUI); ask the user to judge subjective pass bars. Record the outcome in `docs/progress.md`.

## Reference Material Boundaries

- **`misc/`**: Ignore unless the user explicitly says to read it.
- **`book/` and `cc-src/`**: Proactively consult these when drafting Goal Contracts or reviewing code. They are read-only reference.

## Constraints

- Never change anything in `book/` and `cc-src/`.
- Ignore `AGENTS.md`; it is for Codex.