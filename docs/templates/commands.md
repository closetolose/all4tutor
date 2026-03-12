# Command Name

## Overview
Brief description of what this command does and when to use it.

## Steps
1. **Step 1**
   - Action item
   - Another action item

2. **Step 2**
   - Action item
   - Another action item

3. **Step 3**
   - Action item
   - Another action item

## Checklist
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

---

## Template Notes

### File Locations

Commands can be stored in three locations:

1. **Project commands**: `.cursor/commands/` (version-controlled, project-specific)
2. **Global commands**: `~/.cursor/commands/` (user home directory, all projects)
3. **Team commands**: Managed from [Cursor Dashboard](https://cursor.com/dashboard?tab=team-content&section=commands) (Team/Enterprise plans)

### File Structure

```bash
.cursor/
└── commands/
    ├── address-github-pr-comments.md
    ├── code-review-checklist.md
    ├── create-pr.md
    ├── light-review-existing-diffs.md
    ├── onboard-new-developer.md
    ├── run-all-tests-and-fix.md
    ├── security-audit.md
    └── setup-new-feature.md
```

### Command Format

Commands are plain Markdown files (`.md` extension) with:
- Descriptive filename (becomes the command name)
- Clear structure with sections
- Actionable steps
- Optional checklists

### Using Parameters

You can provide additional context after the command name:

```text
/commit and /pr these changes to address DX-523
```

Anything typed after the command name is included in the model prompt alongside the command content.

### Common Command Patterns

#### Code Review Checklist
```markdown
# Code Review Checklist

## Overview
Comprehensive checklist for conducting thorough code reviews to ensure quality, security, and maintainability.

## Review Categories

### Functionality
- [ ] Code does what it's supposed to do
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] No obvious bugs or logic errors

### Code Quality
- [ ] Code is readable and well-structured
- [ ] Functions are small and focused
- [ ] Variable names are descriptive
- [ ] No code duplication
- [ ] Follows project conventions

### Security
- [ ] No obvious security vulnerabilities
- [ ] Input validation is present
- [ ] Sensitive data is handled properly
- [ ] No hardcoded secrets
```

#### Security Audit
```markdown
# Security Audit

## Overview
Comprehensive security review to identify and fix vulnerabilities in the codebase.

## Steps
1. **Dependency audit**
   - Check for known vulnerabilities
   - Update outdated packages
   - Review third-party dependencies

2. **Code security review**
   - Check for common vulnerabilities
   - Review authentication/authorization
   - Audit data handling practices

3. **Infrastructure security**
   - Review environment variables
   - Check access controls
   - Audit network security

## Security Checklist
- [ ] Dependencies updated and secure
- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] Authentication secure
- [ ] Authorization properly configured
```

#### Setup New Feature
```markdown
# Setup New Feature

## Overview
Systematically set up a new feature from initial planning through to implementation structure.

## Steps
1. **Define requirements**
   - Clarify feature scope and goals
   - Identify user stories and acceptance criteria
   - Plan technical approach

2. **Create feature branch**
   - Branch from main/develop
   - Set up local development environment
   - Configure any new dependencies

3. **Plan architecture**
   - Design data models and APIs
   - Plan UI components and flow
   - Consider testing strategy

## Feature Setup Checklist
- [ ] Requirements documented
- [ ] User stories written
- [ ] Technical approach planned
- [ ] Feature branch created
- [ ] Development environment ready
```

#### Create Pull Request
```markdown
# Create PR

## Overview
Create a well-structured pull request with proper description, labels, and reviewers.

## Steps
1. **Prepare branch**
   - Ensure all changes are committed
   - Push branch to remote
   - Verify branch is up to date with main

2. **Write PR description**
   - Summarize changes clearly
   - Include context and motivation
   - List any breaking changes
   - Add screenshots if UI changes

3. **Set up PR**
   - Create PR with descriptive title
   - Add appropriate labels
   - Assign reviewers
   - Link related issues

## PR Template
- [ ] Feature A
- [ ] Bug fix B
- [ ] Unit tests pass
- [ ] Manual testing completed
```

#### Run Tests and Fix Failures
```markdown
# Run All Tests and Fix Failures

## Overview
Execute the full test suite and systematically fix any failures, ensuring code quality and functionality.

## Steps
1. **Run test suite**
   - Execute all tests in the project
   - Capture output and identify failures
   - Check both unit and integration tests

2. **Analyze failures**
   - Categorize by type: flaky, broken, new failures
   - Prioritize fixes based on impact
   - Check if failures are related to recent changes

3. **Fix issues systematically**
   - Start with the most critical failures
   - Fix one issue at a time
   - Re-run tests after each fix
```

#### Onboard New Developer
```markdown
# Onboard New Developer

## Overview
Comprehensive onboarding process to get a new developer up and running quickly.

## Steps
1. **Environment setup**
   - Install required tools
   - Set up development environment
   - Configure editor and extensions
   - Set up git and SSH keys

2. **Project familiarization**
   - Review project structure
   - Understand architecture
   - Read key documentation
   - Set up local database

## Onboarding Checklist
- [ ] Development environment ready
- [ ] All tests passing
- [ ] Can run application locally
- [ ] Database set up and working
- [ ] First PR submitted
```

### Team Commands

Team commands (Team/Enterprise plans):
- Created by team admins in Cursor Dashboard
- Automatically available to all team members
- No manual sync required
- Centralized management
- Standardized workflows

**Creating team commands:**
1. Navigate to [Team Content dashboard](https://cursor.com/dashboard?tab=team-content&section=commands)
2. Click to create a new command
3. Provide:
   - **Name**: The command name (appears after `/` prefix)
   - **Description** (optional): Helpful context
   - **Content**: The Markdown content defining the command's behavior
4. Save the command

**Benefits:**
- Centralized management (update once, available to all)
- Standardization across team
- Easy sharing (no file distribution needed)
- Access control (only admins can modify)

### Best Practices

✅ **Do:**
- Use descriptive filenames that clearly indicate the command's purpose
- Structure commands with clear sections (Overview, Steps, Checklist)
- Make steps actionable and specific
- Include checklists for complex workflows
- Keep commands focused on a single workflow or task
- Use markdown formatting for readability
- Test commands to ensure they work as expected

❌ **Don't:**
- Create overly complex commands that try to do too much
- Use vague or ambiguous language
- Duplicate functionality that already exists
- Create commands that are too specific to one project (use project commands instead)
- Forget to update commands when workflows change

### Command Precedence

When commands with the same name exist in multiple locations:
1. **Project commands** (highest precedence)
2. **Team commands**
3. **Global commands** (lowest precedence)

### Tips

- **Start simple**: Create commands for workflows you repeat frequently
- **Version control**: Check `.cursor/commands/` into git for team sharing
- **Iterate**: Refine commands based on actual usage
- **Document**: Add clear overviews so team members understand when to use each command
- **Organize**: Use descriptive filenames and consider organizing into subdirectories if needed

### Usage

Commands are triggered by typing `/` in the chat input box. Cursor will:
- Automatically detect available commands from all locations
- Display them in a dropdown menu
- Allow you to select and execute them
- Include any additional text you type after the command name as parameters

Example:
```text
/review-code
/security-audit
/create-pr these changes for the new feature
```

### Notes

- Commands are currently in beta - feature and syntax may change
- Commands are plain Markdown files - no special syntax required
- File name (without `.md`) becomes the command name
- Commands work best for standardized, repeatable workflows
