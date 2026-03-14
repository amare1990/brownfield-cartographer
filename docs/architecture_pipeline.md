                ┌────────────────────────────┐
                │      Repository Input      │
                │  (Python / SQL / YAML)    │
                └─────────────┬─────────────┘
                              │
                     Codebase Ingestion
                              │
          ┌───────────────────┴───────────────────┐
          │                                       │
   ┌───────────────┐                       ┌───────────────┐
   │   Surveyor    │                       │  Hydrologist  │
   │ (Code Graph)  │                       │ (Lineage DAG) │
   └───────┬───────┘                       └───────┬───────┘
           │                                       │
           └──────────────┬────────────────────────┘
                          │
                 ┌─────────────────┐
                 │   Knowledge     │
                 │     Graph       │
                 │ (NetworkX)      │
                 └─────────┬───────┘
                           │
                   ┌───────────────┐
                   │  Semanticist  │
                   │ Semantic Repo │
                   │ Understanding │
                   └───────┬───────┘
                           │
                   ┌───────────────┐
                   │   Archivist   │
                   │ Living Context│
                   │  Artifacts    │
                   └───────┬───────┘
                           │
                   ┌───────────────┐
                   │   Navigator   │
                   │ Query Agent   │
                   │ Interactive   │
                   └───────────────┘
