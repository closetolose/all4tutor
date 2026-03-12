# JQL and paths

**JQL examples**

- Open: `status in (Open, "To Do", "In Progress") ORDER BY updated DESC`
- Project: `project = "MYPROJ" AND status in ("To Do", "In Progress") ORDER BY priority DESC, updated DESC`
- Assigned to me: `assignee = currentUser() AND status != Done ORDER BY updated DESC`
- Unassigned: `assignee is EMPTY AND status in ("To Do", "In Progress") ORDER BY created DESC`

**Output:** `docs/jira/<TICKET-KEY>/technical-design.md`
