---
description: "Brief description of what this rule provides. Used by Agent to decide if rule should be applied."
alwaysApply: false
globs:
  - "**/*.ts"
  - "**/*.tsx"
---

# Rule Content

Your rule content goes here. This is where you define the instructions, guidelines, patterns, or workflows.

## Structure

- Use clear, actionable instructions
- Provide concrete examples
- Reference files using @filename syntax
- Keep it focused and under 500 lines

## Examples

When working with [specific context]:
- Follow this pattern
- Use this convention
- Avoid this anti-pattern

@example-file.ts

---

## Template Notes

### Rule Types

| Rule Type                    | Description                                                                      | Frontmatter Settings |
| :--------------------------- | :------------------------------------------------------------------------------- | :------------------- |
| `Always Apply`               | Apply to every chat session                                                     | `alwaysApply: true`  |
| `Apply Intelligently`        | When Agent decides it's relevant based on description                           | `alwaysApply: false` with `description` |
| `Apply to Specific Files`    | When file matches a specified pattern                                           | `globs: ["**/*.ts"]` |
| `Apply Manually`             | When @-mentioned in chat (e.g., `@my-rule`)                                     | `alwaysApply: false` |

### Frontmatter Configuration

```yaml
---
description: "Brief description of what this rule provides"
alwaysApply: false  # true = Always Apply, false = Apply Intelligently or Manual
globs:              # Optional: file patterns for "Apply to Specific Files"
  - "**/*.ts"
  - "**/*.tsx"
---
```

### File Locations

- **Project Rules**: `.cursor/rules/` (version-controlled, scoped to codebase)
- **User Rules**: `Cursor Settings → Rules` (global to your Cursor environment)
- **Team Rules**: Managed from Cursor dashboard (Team/Enterprise plans)
- **AGENTS.md**: Project root or subdirectories (simple markdown alternative)

### File Structure

```bash
.cursor/rules/
  react-patterns.mdc       # Rule with frontmatter (description, globs)
  api-guidelines.md         # Simple markdown rule
  frontend/                 # Organize rules in folders
    components.md
```

### Common Rule Patterns

#### Standards and Guidelines
```markdown
---
description: "Standards for frontend components and API validation"
alwaysApply: false
---

When working in components directory:
- Always use Tailwind for styling
- Use Framer Motion for animations
- Follow component naming conventions

In API directory:
- Use zod for all validation
- Define return types with zod schemas
- Export types generated from schemas
```

#### Templates
```markdown
---
description: "Templates for Express services and React components"
alwaysApply: false
---

Use this template when creating Express service:
- Follow RESTful principles
- Include error handling middleware
- Set up proper logging

@express-service-template.ts

React components should follow this layout:
- Props interface at top
- Component as named export
- Styles at bottom

@component-template.tsx
```

#### Workflow Automation
```markdown
---
description: "Automating development workflows and documentation generation"
alwaysApply: false
---

When asked to analyze the app:
1. Run dev server with `npm run dev`
2. Fetch logs from console
3. Suggest performance improvements

Help draft documentation by:
- Extracting code comments
- Analyzing README.md
- Generating markdown documentation
```

#### File-Specific Rules
```markdown
---
description: "Standards for service files"
globs:
  - "**/services/**/*.ts"
  - "**/api/**/*.ts"
alwaysApply: false
---

- Use our internal RPC pattern when defining services
- Always use snake_case for service names
- Include error handling for all external calls

@service-template.ts
```

### Best Practices

✅ **Do:**
- Keep rules under 500 lines
- Split large rules into multiple, composable rules
- Provide concrete examples or referenced files
- Write rules like clear internal docs
- Reference files instead of copying their contents
- Check rules into git for team sharing
- Start simple and add rules when Agent makes repeated mistakes

❌ **Don't:**
- Copy entire style guides (use a linter instead)
- Document every possible command (Agent knows common tools)
- Add instructions for edge cases that rarely apply
- Duplicate what's already in your codebase
- Create overly long or vague rules

### Referencing Files

Use `@filename` syntax to include files in your rule's context:

```markdown
When creating new components, follow this structure:

@component-template.tsx

For API endpoints, use this pattern:

@api-endpoint-template.ts
```

### AGENTS.md Alternative

For simpler use cases, use `AGENTS.md` in project root or subdirectories:

```markdown
# Project Instructions

## Code Style

- Use TypeScript for all new files
- Prefer functional components in React
- Use snake_case for database columns

## Architecture

- Follow the repository pattern
- Keep business logic in service layers
```

**Note**: `AGENTS.md` is plain markdown without frontmatter. It supports nested files in subdirectories.

### Team Rules

Team Rules (Team/Enterprise plans):
- Managed from Cursor dashboard
- Can be enforced (required) or optional
- Apply across all projects for team members
- Plain text format (no frontmatter or globs)
- Precedence: **Team Rules → Project Rules → User Rules**

### User Rules

User Rules (global preferences):
- Defined in `Cursor Settings → Rules`
- Apply across all projects
- Used by Agent (Chat) only
- Simple text format

Example:
```markdown
Please reply in a concise style. Avoid unnecessary repetition or filler language.
```

### Importing Rules

#### Remote Rules (GitHub)
1. Open `Cursor Settings → Rules, Commands`
2. Click `+ Add Rule` → `Remote Rule (Github)`
3. Paste GitHub repository URL
4. Rule stays synced with source repository

#### Agent Skills
- Load rules from Agent Skills (open standard)
- Always applied as agent-decided rules
- Enable/disable in `Cursor Settings → Rules → Import Settings`

### Rule Precedence

When multiple rules apply:
1. **Team Rules** (highest precedence)
2. **Project Rules**
3. **User Rules** (lowest precedence)

All applicable rules are merged; earlier sources take precedence when guidance conflicts.

### Tips

- **Start simple**: Add rules only when you notice Agent making the same mistake repeatedly
- **Version control**: Check `.cursor/rules/` into git so your whole team benefits
- **Update iteratively**: When you see Agent make a mistake, update the rule
- **Use @mentions**: Reference rules in chat with `@rule-name` to apply manually
- **Reference, don't copy**: Point to canonical examples instead of copying code

### FAQ

**Q: Why isn't my rule being applied?**
- Check the rule type. For `Apply Intelligently`, ensure a description is defined. For `Apply to Specific Files`, ensure the file pattern matches referenced files.

**Q: Can rules reference other rules or files?**
- Yes. Use `@filename.ts` to include files in your rule's context. You can also @mention rules in chat to apply them manually.

**Q: Can I create a rule from chat?**
- Yes, you can ask the agent to create a new rule for you.

**Q: Do rules impact Cursor Tab or other AI features?**
- No. Rules do not impact Cursor Tab or other AI features.

**Q: Do User Rules apply to Inline Edit (Cmd/Ctrl+K)?**
- No. User Rules are not applied to Inline Edit. They are only used by Agent (Chat).
