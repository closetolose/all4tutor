# JIRA update after TDD

Comment (path + summarized design) → transition to In Progress → assign.

## Comment

**addCommentToJiraIssue** with path + summarized design (overview, architecture, components, tech, acceptance criteria). Example:

```markdown
**Technical design created**

Document: `docs/jira/<TICKET-KEY>/technical-design.md`

**Design summary**

- _Overview:_ [1–2 sentences from Design overview.]
- _Architecture:_ [Key components, layers, or services and how they interact.]
- _Key components:_ [Main modules or responsibilities.]
- _Tech / approach:_ [Stack, key design decisions, or implementation approach.]
- _Acceptance criteria (high level):_ [2–4 main criteria from the TDD.]

Ready for implementation.
```

Populate from `technical-design.md`; keep concise.

## Transition

**getTransitionsForJiraIssue** → find "In Progress" (or equivalent) → **transitionJiraIssue** with `transition: { id }`.

## Assignee

**atlassianUserInfo** → accountId. **editJiraIssue** with `fields: { assignee: { accountId } }`. For another user use that accountId.

## Errors

On failure: report and continue.
