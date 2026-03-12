---
name: jira-epic-generation
description: Generate comprehensive JIRA epics, stories, and subtasks from a requirements document (PRD/BRD/SRS). Use when the user provides a requirements document and asks to create or draft JIRA issues.
---

# JIRA Epic & Story Generation

Generate comprehensive JIRA epics, stories, and subtasks from a requirements document using Atlassian MCP.

## When to Use

- User provides a requirements document (PRD/BRD/SRS/requirements spec) and wants JIRA created
- User asks to convert written requirements into epics, stories, and subtasks
- User wants structured agile planning items from a requirements document

## Overview

This skill analyzes a requirements document and generates structured JIRA items (epics, stories, subtasks) with comprehensive agile details, then creates them in JIRA via Atlassian MCP.

## MCP Server Integration

### Atlassian MCP Server

Use Atlassian MCP server for all JIRA operations:

- **Get Project Details**: Use `getVisibleJiraProjects` to find available projects
- **Get Issue Types**: Use `getJiraProjectIssueTypesMetadata` to get available issue types (Epic, Story, Subtask)
- **Create Issues**: Use `createJiraIssue` to create epics, stories, and subtasks
- **Link Issues**: Use `editJiraIssue` to link epics to stories and stories to subtasks (subtasks are automatically linked via parent issue)
- **Get Cloud ID**: Use `getAccessibleAtlassianResources` to get your Atlassian cloud ID

## Workflow

### 1. Analyze Requirements Document

Analyze the requirements document to extract:

- **Scope & Context**: product/objective, in-scope vs out-of-scope, assumptions
- **Actors & Personas**: user types/roles and primary goals
- **Functional Requirements**: features, workflows, business rules, validations
- **Non-Functional Requirements**: performance, security, compliance, availability, observability
- **Interfaces & Integrations**: APIs, systems, data flows, dependencies
- **Data Requirements**: entities, fields, retention, privacy constraints
- **Acceptance Criteria**: explicit AC in the document; infer only when clearly implied
- **Constraints**: tech stack, deployment, environments, regulatory constraints
- **Priorities & Milestones**: MVP definition, priorities, deadlines (if present)

**Output**: Create an analysis summary with extracted requirements, proposed epics, and story candidates.

### 2. Generate JIRA Items

Based on the analysis, generate:

**Epics**:

- Title: Clear, business-focused epic name
- Description: Comprehensive epic description with business context
- Acceptance Criteria: High-level epic acceptance criteria
- Business Value: Business value and impact
- Dependencies: Dependencies on other epics or external factors

**Stories**:

- Title: User story format (As a... I want... So that...)
- Description: Detailed story description
- Acceptance Criteria: Specific, testable acceptance criteria
- Story Points: Story point estimation (Fibonacci scale: 1, 2, 3, 5, 8, 13)
- Priority: Story priority (High, Medium, Low)
- Epic Link: Link to parent epic
- Dependencies: Dependencies on other stories or tasks

**Subtasks**:

- Title: Clear subtask description
- Description: Detailed subtask description
- Acceptance Criteria: Subtask completion criteria
- Parent Issue: Link to parent story (set via parent field when creating subtask)
- Estimated Duration: Time estimate in hours
- Priority: Subtask priority

**Output**: Generate structured JIRA items in markdown format ready for JIRA creation.

### 3. Review with User

Present generated JIRA items to the user:

- Show epics with their stories and subtasks
- Display descriptions, acceptance criteria, and estimates
- Allow user to refine, add, or remove items
- Update items based on user feedback

### 4. Create in JIRA

Once user approves, create items in JIRA:

1. **Get Atlassian Cloud ID**: Use `getAccessibleAtlassianResources` to get cloud ID
2. **Get Project Details**: Use `getVisibleJiraProjects` to find target project
3. **Get Issue Types**: Use `getJiraProjectIssueTypesMetadata` to get Epic, Story, Subtask types
4. **Create Epics First**: Create all epics using `createJiraIssue` with issue type "Epic"
5. **Create Stories**: Create stories linked to epics using `createJiraIssue` with issue type "Story"
6. **Create Subtasks**: Create subtasks linked to stories using `createJiraIssue` with issue type "Subtask" and parent field set to the story key
7. **Link Issues**: Use `editJiraIssue` to establish epic-story relationships (subtasks are automatically linked via parent field)

**Note**: When creating issues, include:

- Summary (title)
- Description (markdown format)
- Issue type (Epic, Story, or Subtask)
- Parent field (for subtasks - set to parent story key)
- Additional fields as needed (priority, story points, etc.)

## Key Principles

- **Comprehensive Analysis**: Extract all requirements, features, and user stories from the requirements document
- **Agile Best Practices**: Follow agile methodologies (Scrum/Kanban) and JIRA standards
- **Complete Details**: Include all standard JIRA fields (descriptions, estimates, dependencies)
- **User Review**: Always present items for user review before creating in JIRA
- **MCP Integration**: Use Atlassian MCP to create JIRA items with proper linking
- **Subtask Parent Link**: Subtasks must have a parent story specified via the parent field when creating

## Example Output Structure

```markdown
# Epic: User Authentication System

**Description**: Implement comprehensive user authentication and authorization system
**Business Value**: Enable secure access to the platform
**Acceptance Criteria**:

- Users can register and login
- Password reset functionality works
- Multi-factor authentication available

## Story: User Registration

**As a** new user **I want** to register an account **So that** I can access the platform
**Story Points**: 5
**Priority**: High
**Acceptance Criteria**:

- User can create account with email and password
- Email verification required
- Password strength validation enforced

### Subtask: Implement Registration API

**Description**: Create REST API endpoint for user registration
**Estimated Duration**: 8 hours
**Priority**: High
**Parent**: [Story Key]
```

## Directory Structure (Optional)

If saving artifacts locally:

```
.jira-epic-docs/
├── requirements/             # Requirements document(s)
├── analysis/                 # Requirements analysis
└── jira-items/               # Generated JIRA items
```

## Notes

- Always get user confirmation before creating items in JIRA
- Verify project access and issue type availability before creation
- Handle errors gracefully and provide clear feedback
- Link epics to stories and set parent field for subtasks to stories for proper hierarchy
- Subtasks require a parent story to be created - ensure stories exist before creating subtasks
