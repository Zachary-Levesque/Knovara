# Architecture

## Objective

Build the simplest possible system that validates the core Knovara hypothesis:

> Engineers become productive faster when organizational knowledge is organized, connected, and personalized.

This architecture prioritizes speed of development and validation over scalability.

---

# High-Level Architecture

```text
                 ┌──────────────┐
                 │   Frontend   │
                 │   Next.js    │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │   Backend    │
                 │   FastAPI    │
                 └──────┬───────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼

  GitHub API     Document Store     LLM Provider
                                   (OpenAI/Anthropic)

                        │
                        ▼

                 Knowledge Layer
```

---

# Frontend

## Technology

* Next.js
* TypeScript
* TailwindCSS

## Responsibilities

* User authentication
* Project dashboard
* Search interface
* AI chat interface
* Learning recommendations

---

# Backend

## Technology

* Python
* FastAPI

## Responsibilities

* Data ingestion
* Document processing
* Knowledge extraction
* AI orchestration
* API endpoints

---

# Data Sources

## Phase 1

* GitHub repositories
* README files
* Documentation folders
* Commit history
* Contributors

---

## Future Sources

* Jira
* Confluence
* Notion
* Slack
* Teams
* Internal Wikis

---

# Knowledge Model

Knovara's core asset is a knowledge graph.

Relationships include:

Engineer ↔ Team

Engineer ↔ Project

Project ↔ Repository

Repository ↔ Documentation

Decision ↔ Project

Expert ↔ Topic

The graph becomes the foundation for recommendations and mentorship.

---

# AI Layer

## Responsibilities

Generate:

* Project summaries
* Learning paths
* Expert recommendations
* Technical explanations
* Context-aware answers

---

# MVP Workflow

### Step 1

Connect repository.

### Step 2

Ingest:

* Code structure
* Documentation
* Commit history

### Step 3

Extract:

* Topics
* Components
* Contributors

### Step 4

Generate:

* Project overview
* Learning path
* Suggested experts
* Questions and answers

### Step 5

Present results to the user.

---

# Design Principles

## Simplicity First

Avoid overengineering.

---

## Validation Before Scale

Build the smallest version that can prove the hypothesis.

---

## Human-Centered

The goal is not information retrieval.

The goal is helping engineers understand.

---

# Future Architecture

Future versions may include:

* Organizational knowledge graphs
* Multi-source ingestion
* Enterprise deployment
* Personalized mentorship agents
* Continuous learning recommendations

These are intentionally out of scope for the first version.
