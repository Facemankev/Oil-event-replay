---
name: plan-change
description: Propose a change to Market Ripple's direction. Use when someone says "I want to change the plan", wants to add, drop or reorder a workstream or milestone, edit the vision or principles, or record a decision. The change goes to the other partner as a pull request to agree to.
---

# Change the plan

The vision, principles, workstreams and decisions belong to both partners.
A change is a proposal until the other partner approves it.

1. **Understand it.** Ask what they want to change and why, if they haven't
   said. Read `team/PLAN.md` and `team/DECISIONS.md`. If it reverses a
   recorded decision, point that out and confirm they mean to.
2. **Branch:** `person/plan-<topic>` from an up-to-date `main`.
3. **Edit:**
   - `team/PLAN.md`: make the change, and add a dated line to *Change
     history* saying what changed and why.
   - `team/DECISIONS.md`: add a new numbered row with status
     `Proposed: <other partner> to confirm`. Never edit an old decision. A
     new one replaces it and says which.
   - `team/TODO.md`: add any jobs that follow from it.
4. **Log it** with a short entry in `team/log/` (the `wrap-up` format).
5. **Send it:** commit, push, and open a pull request titled
   `Plan change: <what>`. Request the other partner as reviewer. The
   description says what changes, why, and what it means for current work,
   in plain words.
6. **Once approved,** the author changes the decision's status to `Agreed`
   in the same branch, then merges.

Show the person the exact wording before opening the pull request.
