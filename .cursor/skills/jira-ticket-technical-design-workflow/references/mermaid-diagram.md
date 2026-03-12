# Mermaid in TDD

**Place:** Architecture diagram section inside `technical-design.md`. Mermaid code blocks; no separate file.

**Types:** flowchart (default; use subgraph), sequenceDiagram, erDiagram, stateDiagram when ticket implies.

**Conventions:** subgraphs, clear labels (`id[Label]`), TB/LR, `-->` / `-.->`; one idea per diagram. For line breaks inside node labels use `<br/>` (not `\n`), so markdown and renderers show proper breaks.

**Example**

```mermaid
flowchart TB
  subgraph "Client"
    UI[Web / Mobile]
  end
  subgraph "Backend"
    API[API Gateway]
    SVC[Services]
  end
  subgraph "Data"
    DB[(Database)]
  end
  UI --> API
  API --> SVC
  SVC --> DB
```

Derive from ticket description and acceptance criteria.
