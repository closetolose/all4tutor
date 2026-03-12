---
name: jira-ticket-technical-design-workflow
description: Fetch open JIRA tickets, user picks one; generate TDD with inline Mermaid in docs/jira/<KEY>/; update JIRA (comment with design summary, In Progress, assign). Use when starting from a JIRA ticket or generating a technical design. Atlassian MCP.
---

# JIRA Ticket to Technical Design Workflow

Fetch open tickets → user picks one → create TDD with inline Mermaid in `docs/jira/<TICKET-KEY>/technical-design.md` → update JIRA (comment with design summary, status In Progress, assign).

## When to Use

- User wants to work from a JIRA ticket or generate a technical design document from one

## Atlassian MCP (user-Atlassian)

| Tool                              | Purpose                                                          |
| --------------------------------- | ---------------------------------------------------------------- |
| `getAccessibleAtlassianResources` | cloudId                                                          |
| `searchJiraIssuesUsingJql`        | open tickets (`cloudId`, `jql`; optional `maxResults`, `fields`) |
| `getJiraIssue`                    | full issue (`cloudId`, `issueIdOrKey`)                           |
| `addCommentToJiraIssue`           | comment (`cloudId`, `issueIdOrKey`, `commentBody` Markdown)      |
| `getTransitionsForJiraIssue`      | available transitions                                            |
| `transitionJiraIssue`             | change status (`transition: { id }`)                             |
| `editJiraIssue`                   | set fields e.g. assignee (`fields`)                              |
| `atlassianUserInfo`               | current user accountId                                           |

JQL examples: [references/jql-and-paths.md](references/jql-and-paths.md)

## Workflow

### 1. Fetch open tickets

1. **getAccessibleAtlassianResources** → get `cloudId`.
2. **searchJiraIssuesUsingJql** (`cloudId`, `jql` for open tickets, `maxResults`: 50, `fields`: summary, description, status, issuetype, priority, created, key).
3. Show table (Key, Summary, Type, Status, Priority). Ask user to pick by key or number.

### 2. Fetch ticket and create directory

4. **getJiraIssue** (`cloudId`, `issueIdOrKey`). Full details.
5. Create `docs/jira/<TICKET-KEY>/` (exact JIRA key as folder name).

### 3. Generate TDD

6. Produce TDD from ticket. Structure: [references/technical-design-template.md](references/technical-design-template.md). Include **Architecture diagram** section with Mermaid (flowchart and/or sequence/ER/state as needed). Conventions: [references/mermaid-diagram.md](references/mermaid-diagram.md).
7. Save as `docs/jira/<TICKET-KEY>/technical-design.md`.

### 4. Update JIRA

8. **addCommentToJiraIssue**: path to `technical-design.md` + summarized design (overview, architecture, components, tech, acceptance criteria). Template: [references/jira-update.md](references/jira-update.md).
9. **getTransitionsForJiraIssue** → find "In Progress" (or equivalent) → **transitionJiraIssue** with that `transition.id`.
10. **atlassianUserInfo** → accountId. **editJiraIssue** with `fields: { assignee: { accountId } }` (current user unless user specified otherwise).
11. On transition/assign failure: report and continue.

### 5. Summarize

12. Tell user: ticket key, `docs/jira/<TICKET-KEY>/`, `technical-design.md`, JIRA updates (or failures), next steps (e.g. jira-epic-generation).

## Output layout

```
docs/jira/<TICKET-KEY>/
└── technical-design.md
```

## Checklist

- [ ] cloudId → search → user picks ticket → getJiraIssue → create dir.
- [ ] TDD + Mermaid in `technical-design.md`.
- [ ] JIRA: comment (path + design summary), transition In Progress, assign.
- [ ] User told paths and JIRA result.

**References:** [technical-design-template](references/technical-design-template.md) · [jql-and-paths](references/jql-and-paths.md) · [mermaid-diagram](references/mermaid-diagram.md) · [jira-update](references/jira-update.md)
