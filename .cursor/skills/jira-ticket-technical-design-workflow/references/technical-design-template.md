# TDD structure

Structure for `technical-design.md`. **Architecture diagram** section: Mermaid diagram(s) inline.

```markdown
# Technical Design: [Ticket Key] – [Short title from summary]

## Ticket reference

- **Key**: [KEY]
- **Type**: [Issue type]
- **Status**: [Status]
- **Priority**: [Priority]

## Design overview

[Context and design objectives derived from the ticket.]

## Architecture

[High-level structure: components, layers, or services and how they interact. Short narrative.]

## Architecture diagram

[Mermaid code blocks. Flowchart default; add sequenceDiagram/erDiagram/stateDiagram when ticket implies. See mermaid-diagram.md.]

## Component design

[Key modules, responsibilities, and interfaces between them.]

## Data design

[Schema, entities, storage approach, or data flow as applicable.]

## Interface / API design

[APIs, contracts, or integration approach (request/response, events).]

## Technology choices

[Stack, frameworks, and rationale where inferable from the ticket.]

## Implementation approach

[Phasing, key design decisions, or sequencing if relevant.]

## Cross-cutting concerns

[Security, performance, or observability design decisions.]

## Acceptance criteria

- [Criterion 1]
- [Criterion 2]
- ...

## References

- [Related tickets, Confluence, or links from the JIRA issue]
```

Fill from JIRA; omit empty sections. At least one Mermaid diagram in Architecture diagram.
