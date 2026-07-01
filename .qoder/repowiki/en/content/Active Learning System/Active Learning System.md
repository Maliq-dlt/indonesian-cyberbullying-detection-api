# Active Learning System

<cite>
**Referenced Files in This Document**
- [hitl.py](file://cyberbullying_api/routes/hitl.py)
- [predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [db_memory.py](file://cyberbullying_api/classifier/db_memory.py)
- [training.py](file://cyberbullying_api/routes/training.py)
- [augmentation.py](file://cyberbullying_api/training/augmentation.py)
- [data_loader.py](file://cyberbullying_api/training/data_loader.py)
- [retrain.py](file://cyberbullying_api/retrain.py)
- [tasks.py](file://cyberbullying_api/tasks.py)
- [models.py](file://cyberbullying_api/models.py)
- [confidence.py](file://cyberbullying_api/classifier/confidence.py)
- [settings_store.py](file://cyberbullying_api/classifier/settings_store.py)
- [Quadrant.tsx](file://frontend/src/components/ActiveLearning/Quadrant.tsx)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document describes BullyGuard ID’s active learning system designed to enhance human-in-the-loop (HITL) validation workflows. It explains how ambiguous predictions are routed to human reviewers, how training data is managed and augmented, and how model improvements are orchestrated. The system balances automated processing with human oversight through confidence thresholds, ambiguity handling, and a structured review interface. It also documents the HITL review interface, training record tracking, quality assurance mechanisms, and the integration between classification results, admin workflows, and model updates.

## Project Structure
The active learning system spans backend APIs, classification logic, training orchestration, and a frontend HITL interface:
- Backend API routes expose HITL review and training controls
- Classification engine performs hybrid inference with confidence-aware routing
- Training pipeline ingests labeled data, augments it, and retrains models with rollback safety
- Frontend provides a quadrant-based HITL interface for reallocation

```mermaid
graph TB
subgraph "Frontend"
FE_Quadrant["Quadrant.tsx<br/>HITL Review UI"]
end
subgraph "Backend API"
API_HITL["routes/hitl.py<br/>GET/POST HITL endpoints"]
API_Train["routes/training.py<br/>Start/Reload/Logs/History"]
API_Admin["routes/admin.py<br/>Router aggregator"]
end
subgraph "Classifier Engine"
CL_Predictor["classifier/predictor.py<br/>Hybrid inference & caching"]
CL_Conf["classifier/confidence.py<br/>Confidence & thresholds"]
CL_DBMem["classifier/db_memory.py<br/>Memory & validation"]
CL_Settings["classifier/settings_store.py<br/>Ensemble weights"]
end
subgraph "Training Pipeline"
TR_Aug["training/augmentation.py<br/>Augmentation utilities"]
TR_Data["training/data_loader.py<br/>Dataset ingestion"]
TR_Retrain["retrain.py<br/>Full training pipeline"]
TR_Tasks["tasks.py<br/>Celery orchestration"]
end
FE_Quadrant --> API_HITL
API_Admin --> API_HITL
API_Admin --> API_Train
API_HITL --> CL_DBMem
API_Train --> TR_Tasks
TR_Tasks --> TR_Retrain
TR_Retrain --> TR_Aug
TR_Retrain --> TR_Data
CL_Predictor --> CL_DBMem
CL_Predictor --> CL_Conf
CL_Predictor --> CL_Settings
```

**Diagram sources**
- [hitl.py:1-84](file://cyberbullying_api/routes/hitl.py#L1-L84)
- [training.py:1-259](file://cyberbullying_api/routes/training.py#L1-L259)
- [predictor.py:1-639](file://cyberbullying_api/classifier/predictor.py#L1-L639)
- [db_memory.py:1-756](file://cyberbullying_api/classifier/db_memory.py#L1-L756)
- [confidence.py:1-221](file://cyberbullying_api/classifier/confidence.py#L1-L221)
- [settings_store.py:1-73](file://cyberbullying_api/classifier/settings_store.py#L1-L73)
- [augmentation.py:1-197](file://cyberbullying_api/training/augmentation.py#L1-L197)
- [data_loader.py:1-385](file://cyberbullying_api/training/data_loader.py#L1-L385)
- [retrain.py:1-513](file://cyberbullying_api/retrain.py#L1-L513)
- [tasks.py:1-95](file://cyberbullying_api/tasks.py#L1-L95)
- [Quadrant.tsx:1-262](file://frontend/src/components/ActiveLearning/Quadrant.tsx#L1-L262)

**Section sources**
- [hitl.py:1-84](file://cyberbullying_api/routes/hitl.py#L1-L84)
- [training.py:1-259](file://cyberbullying_api/routes/training.py#L1-L259)
- [predictor.py:1-639](file://cyberbullying_api/classifier/predictor.py#L1-L639)
- [db_memory.py:1-756](file://cyberbullying_api/classifier/db_memory.py#L1-L756)
- [confidence.py:1-221](file://cyberbullying_api/classifier/confidence.py#L1-L221)
- [settings_store.py:1-73](file://cyberbullying_api/classifier/settings_store.py#L1-L73)
- [augmentation.py:1-197](file://cyberbullying_api/training/augmentation.py#L1-L197)
- [data_loader.py:1-385](file://cyberbullying_api/training/data_loader.py#L1-L385)
- [retrain.py:1-513](file://cyberbullying_api/retrain.py#L1-L513)
- [tasks.py:1-95](file://cyberbullying_api/tasks.py#L1-L95)
- [Quadrant.tsx:1-262](file://frontend/src/components/ActiveLearning/Quadrant.tsx#L1-L262)

## Core Components
- Human-in-the-loop (HITL) endpoints for categorized data retrieval, single reallocation, and bulk reallocation
- Hybrid classification pipeline with confidence-aware routing across lexicon, ML, ensemble, and cloud LLM tiers
- Training orchestration with data ingestion, augmentation, calibration, and rollback safety
- HITL review interface with quadrant-based categorization and reallocation actions
- Training record tracking and performance history persistence

**Section sources**
- [hitl.py:14-84](file://cyberbullying_api/routes/hitl.py#L14-L84)
- [predictor.py:308-440](file://cyberbullying_api/classifier/predictor.py#L308-L440)
- [training.py:29-178](file://cyberbullying_api/routes/training.py#L29-L178)
- [Quadrant.tsx:105-262](file://frontend/src/components/ActiveLearning/Quadrant.tsx#L105-L262)
- [db_memory.py:676-755](file://cyberbullying_api/classifier/db_memory.py#L676-L755)

## Architecture Overview
The system integrates frontend HITL review with backend classification and training:
- Frontend renders ambiguous predictions in quadrants and allows reallocation actions
- Backend routes ambiguous predictions to human review and persists validated labels
- Training pipeline ingests validated data, augments it, retrains models, and publishes reload signals
- Redis tracks training status and model reload events; PostgreSQL/SQLite persist classification memory and training history

```mermaid
sequenceDiagram
participant User as "Reviewer"
participant FE as "Frontend Quadrant.tsx"
participant API as "routes/hitl.py"
participant CL as "classifier/db_memory.py"
participant Train as "routes/training.py"
participant Celery as "tasks.py"
participant RT as "retrain.py"
User->>FE : Select items and click reallocate
FE->>API : POST /api/data/reallocate
API->>CL : update_validation_status(text, new_labels)
CL-->>API : Success/Failure
API-->>FE : ReallocateResponse
FE-->>User : Updated review state
User->>Train : Trigger training (start/reload)
Train->>Celery : run_retrain_task(model_type)
Celery->>RT : Execute retrain pipeline
RT-->>Celery : Write model artifacts & history
Celery-->>Train : Publish reload event
Train-->>User : Training logs/status
```

**Diagram sources**
- [hitl.py:51-84](file://cyberbullying_api/routes/hitl.py#L51-L84)
- [db_memory.py:588-674](file://cyberbullying_api/classifier/db_memory.py#L588-L674)
- [training.py:29-178](file://cyberbullying_api/routes/training.py#L29-L178)
- [tasks.py:26-82](file://cyberbullying_api/tasks.py#L26-L82)
- [retrain.py:426-490](file://cyberbullying_api/retrain.py#L426-L490)

## Detailed Component Analysis

### Human-in-the-Loop Validation Workflow
- Endpoint for retrieving categorized, ambiguous predictions grouped by toxicity/bullying quadrants
- Single and bulk reallocation endpoints update validation status and confidence
- Frontend UI supports drag-and-drop reallocation with immediate feedback

```mermaid
sequenceDiagram
participant FE as "Frontend Quadrant.tsx"
participant API as "routes/hitl.py"
participant CL as "classifier/db_memory.py"
FE->>API : GET /api/data/categorized?limit&offset&confidence_min&confidence_max
API->>CL : get_categorized_memory(...)
CL-->>API : Quadrant data with counts
API-->>FE : Paginated quadrant payload
FE->>API : POST /api/data/reallocate
API->>CL : update_validation_status(text, new_is_toxic, new_is_bully, is_validated=1)
CL-->>API : Success
API-->>FE : ReallocateResponse
```

**Diagram sources**
- [hitl.py:14-45](file://cyberbullying_api/routes/hitl.py#L14-L45)
- [hitl.py:51-84](file://cyberbullying_api/routes/hitl.py#L51-L84)
- [db_memory.py:460-586](file://cyberbullying_api/classifier/db_memory.py#L460-L586)
- [db_memory.py:588-674](file://cyberbullying_api/classifier/db_memory.py#L588-L674)
- [Quadrant.tsx:105-262](file://frontend/src/components/ActiveLearning/Quadrant.tsx#L105-L262)

**Section sources**
- [hitl.py:14-84](file://cyberbullying_api/routes/hitl.py#L14-L84)
- [db_memory.py:460-674](file://cyberbullying_api/classifier/db_memory.py#L460-L674)
- [Quadrant.tsx:1-262](file://frontend/src/components/ActiveLearning/Quadrant.tsx#L1-L262)

### Hybrid Classification and Confidence Routing
- Multi-tier inference: lexicon → ML → ensemble → cloud LLM fallback
- Confidence-aware routing determines when to escalate to higher tiers
- Cached classification memory reduces latency and supports semantic cache lookups

```mermaid
flowchart TD
Start(["New text input"]) --> LexCheck["Lexicon risk assessment"]
LexCheck --> RiskHigh{"Risk high?"}
RiskHigh --> |Yes| ReturnLex["Return lexicon decision"]
RiskHigh --> |No| MLInf["Run ML model"]
MLInf --> ConfCheck{"Confident pair?<br/>Margin ≥ threshold"}
ConfCheck --> |Yes| ReturnML["Return ML decision"]
ConfCheck --> |No| EnsInf["Run ensemble (ML+Transformer)"]
EnsInf --> EnsConf{"Confident pair?"}
EnsConf --> |Yes| ReturnEns["Return ensemble decision"]
EnsConf --> |No| LLMInf["Query cloud LLM"]
LLMInf --> ReturnLLM["Return LLM decision"]
ReturnLex --> Cache["Save to memory/cache"]
ReturnML --> Cache
ReturnEns --> Cache
ReturnLLM --> Cache
Cache --> End(["Return HybridResponse"])
```

**Diagram sources**
- [predictor.py:308-440](file://cyberbullying_api/classifier/predictor.py#L308-L440)
- [confidence.py:72-109](file://cyberbullying_api/classifier/confidence.py#L72-L109)
- [db_memory.py:17-124](file://cyberbullying_api/classifier/db_memory.py#L17-L124)

**Section sources**
- [predictor.py:308-440](file://cyberbullying_api/classifier/predictor.py#L308-L440)
- [confidence.py:1-221](file://cyberbullying_api/classifier/confidence.py#L1-L221)
- [db_memory.py:17-124](file://cyberbullying_api/classifier/db_memory.py#L17-L124)

### Training Pipeline Orchestration and Automated Retraining
- Admin endpoints start training, stream logs, and show history
- Celery task runs retraining scripts and publishes reload signals
- Retraining ingests validated data, augments, calibrates thresholds, and applies rollback safety
- Settings store manages ensemble weights persisted in Redis and local file

```mermaid
sequenceDiagram
participant Admin as "Admin UI"
participant Train as "routes/training.py"
participant Celery as "tasks.py"
participant RT as "retrain.py"
participant Redis as "Redis"
participant DB as "PostgreSQL/SQLite"
Admin->>Train : POST /api/train/start (model_type)
Train->>Redis : training_status=running
Train->>Celery : run_retrain_task(model_type)
Celery->>RT : Execute scripts
RT->>DB : Save retraining history
RT-->>Celery : Success/Failure
Celery->>Redis : training_status=completed/failed
Celery->>Redis : publish model_reload
Train-->>Admin : Logs stream + completion
```

**Diagram sources**
- [training.py:29-178](file://cyberbullying_api/routes/training.py#L29-L178)
- [tasks.py:26-82](file://cyberbullying_api/tasks.py#L26-L82)
- [retrain.py:426-490](file://cyberbullying_api/retrain.py#L426-L490)
- [db_memory.py:676-705](file://cyberbullying_api/classifier/db_memory.py#L676-L705)
- [settings_store.py:33-73](file://cyberbullying_api/classifier/settings_store.py#L33-L73)

**Section sources**
- [training.py:1-259](file://cyberbullying_api/routes/training.py#L1-L259)
- [tasks.py:1-95](file://cyberbullying_api/tasks.py#L1-L95)
- [retrain.py:1-513](file://cyberbullying_api/retrain.py#L1-L513)
- [settings_store.py:1-73](file://cyberbullying_api/classifier/settings_store.py#L1-L73)

### Data Augmentation Techniques
- LLM-based paraphrasing augmentation using a Gemini-compatible endpoint
- Rule-based perturbations (leet speak, censor, typo, repetition) targeting abusive words
- Templates for sarcasm and slang-praise patterns to balance class distributions

```mermaid
flowchart TD
A["Ambiguous prediction text"] --> B{"Has abusive words?"}
B --> |Yes| C["Apply perturb_text()<br/>leet/censor/repeat/typo"]
B --> |No| D["Skip perturbation"]
C --> E["Generate LLM paraphrases"]
D --> E
E --> F["Append augmented samples<br/>to training set"]
```

**Diagram sources**
- [augmentation.py:90-144](file://cyberbullying_api/training/augmentation.py#L90-L144)
- [augmentation.py:147-197](file://cyberbullying_api/training/augmentation.py#L147-L197)
- [retrain.py:198-255](file://cyberbullying_api/retrain.py#L198-L255)

**Section sources**
- [augmentation.py:1-197](file://cyberbullying_api/training/augmentation.py#L1-L197)
- [retrain.py:198-255](file://cyberbullying_api/retrain.py#L198-L255)

### Training Data Management and Quality Assurance
- Ingestion from scraped CSV files and validated classification memory
- Deduplication and normalization of text
- Oversampling validated records and stratified train/test splits
- Automatic rollback if new model performance degrades significantly
- Persistent training history with thresholds and active version tracking

```mermaid
flowchart TD
S["Scraped CSV + Validated Memory"] --> N["Normalize & deduplicate"]
N --> A["Augment (paraphrases + perturbations)"]
A --> V["Stratified split by label combinations"]
V --> T["Train MultiOutputClassifier"]
T --> C["Calibrate thresholds"]
C --> R{"Rollback check"}
R --> |Pass| W["Write artifacts & history"]
R --> |Fail| K["Keep old model"]
```

**Diagram sources**
- [data_loader.py:155-303](file://cyberbullying_api/training/data_loader.py#L155-L303)
- [retrain.py:329-380](file://cyberbullying_api/retrain.py#L329-L380)
- [retrain.py:420-425](file://cyberbullying_api/retrain.py#L420-L425)
- [db_memory.py:676-705](file://cyberbullying_api/classifier/db_memory.py#L676-L705)

**Section sources**
- [data_loader.py:1-385](file://cyberbullying_api/training/data_loader.py#L1-L385)
- [retrain.py:329-490](file://cyberbullying_api/retrain.py#L329-L490)
- [db_memory.py:676-705](file://cyberbullying_api/classifier/db_memory.py#L676-L705)

### Practical Active Learning Cycle Example
- Ambiguous prediction enters classification pipeline and is cached
- Admin retrieves categorized items and reviews ambiguous cases
- Reviewer reallocated items to correct categories
- Retraining pipeline ingests validated data, augments, retrains, and publishes reload
- New model hot-reloads and improves accuracy

```mermaid
sequenceDiagram
participant User as "Reviewer"
participant API as "routes/hitl.py"
participant CL as "classifier/db_memory.py"
participant Train as "routes/training.py"
participant Celery as "tasks.py"
participant RT as "retrain.py"
Note over CL : Predict hybrid and cache result
User->>API : GET categorized
API->>CL : get_categorized_memory(...)
CL-->>API : Items near thresholds
User->>API : POST reallocate (bulk/single)
API->>CL : update_validation_status(...)
User->>Train : Start training
Train->>Celery : run_retrain_task
Celery->>RT : Run pipeline
RT-->>Celery : Artifacts + history
Celery-->>Train : Reload signal
Train-->>User : Logs + completion
```

**Diagram sources**
- [predictor.py:421-440](file://cyberbullying_api/classifier/predictor.py#L421-L440)
- [hitl.py:14-84](file://cyberbullying_api/routes/hitl.py#L14-L84)
- [db_memory.py:460-674](file://cyberbullying_api/classifier/db_memory.py#L460-L674)
- [training.py:29-178](file://cyberbullying_api/routes/training.py#L29-L178)
- [tasks.py:26-82](file://cyberbullying_api/tasks.py#L26-L82)
- [retrain.py:426-490](file://cyberbullying_api/retrain.py#L426-L490)

**Section sources**
- [predictor.py:421-440](file://cyberbullying_api/classifier/predictor.py#L421-L440)
- [hitl.py:14-84](file://cyberbullying_api/routes/hitl.py#L14-L84)
- [db_memory.py:460-674](file://cyberbullying_api/classifier/db_memory.py#L460-L674)
- [training.py:29-178](file://cyberbullying_api/routes/training.py#L29-L178)
- [tasks.py:26-82](file://cyberbullying_api/tasks.py#L26-L82)
- [retrain.py:426-490](file://cyberbullying_api/retrain.py#L426-L490)

## Dependency Analysis
Key dependencies and coupling:
- Routes depend on classifier modules for memory and validation
- Training depends on augmentation and data loader utilities
- Redis provides distributed status and settings synchronization
- PostgreSQL/SQLite persist classification memory and training history

```mermaid
graph LR
API_HITL["routes/hitl.py"] --> DBMem["classifier/db_memory.py"]
API_TRAIN["routes/training.py"] --> TASKS["tasks.py"]
TASKS --> RETRAIN["retrain.py"]
RETRAIN --> AUG["training/augmentation.py"]
RETRAIN --> DATA["training/data_loader.py"]
PREDICT["classifier/predictor.py"] --> DBMem
PREDICT --> CONF["classifier/confidence.py"]
PREDICT --> SETTINGS["classifier/settings_store.py"]
DBMem --> REDIS["Redis"]
DBMem --> PG["PostgreSQL"]
DBMem --> SQLITE["SQLite"]
```

**Diagram sources**
- [hitl.py:1-84](file://cyberbullying_api/routes/hitl.py#L1-L84)
- [db_memory.py:1-756](file://cyberbullying_api/classifier/db_memory.py#L1-L756)
- [training.py:1-259](file://cyberbullying_api/routes/training.py#L1-L259)
- [tasks.py:1-95](file://cyberbullying_api/tasks.py#L1-L95)
- [retrain.py:1-513](file://cyberbullying_api/retrain.py#L1-L513)
- [augmentation.py:1-197](file://cyberbullying_api/training/augmentation.py#L1-L197)
- [data_loader.py:1-385](file://cyberbullying_api/training/data_loader.py#L1-L385)
- [predictor.py:1-639](file://cyberbullying_api/classifier/predictor.py#L1-L639)
- [confidence.py:1-221](file://cyberbullying_api/classifier/confidence.py#L1-L221)
- [settings_store.py:1-73](file://cyberbullying_api/classifier/settings_store.py#L1-L73)

**Section sources**
- [hitl.py:1-84](file://cyberbullying_api/routes/hitl.py#L1-L84)
- [training.py:1-259](file://cyberbullying_api/routes/training.py#L1-L259)
- [predictor.py:1-639](file://cyberbullying_api/classifier/predictor.py#L1-L639)
- [db_memory.py:1-756](file://cyberbullying_api/classifier/db_memory.py#L1-L756)
- [augmentation.py:1-197](file://cyberbullying_api/training/augmentation.py#L1-L197)
- [data_loader.py:1-385](file://cyberbullying_api/training/data_loader.py#L1-L385)
- [retrain.py:1-513](file://cyberbullying_api/retrain.py#L1-L513)
- [tasks.py:1-95](file://cyberbullying_api/tasks.py#L1-L95)
- [confidence.py:1-221](file://cyberbullying_api/classifier/confidence.py#L1-L221)
- [settings_store.py:1-73](file://cyberbullying_api/classifier/settings_store.py#L1-L73)

## Performance Considerations
- Confidence margin and threshold calibration reduce unnecessary escalations
- Cached classification memory and semantic cache minimize repeated computation
- Asynchronous training with streaming logs enables long-running jobs without blocking
- Stratified sampling and oversampling improve robustness for imbalanced datasets
- Rollback safety prevents regressions from impacting production

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and remedies:
- Training already running: Check Redis/Celery status and avoid duplicate starts
- Reallocation failures: Verify text hashing and encryption/decryption keys
- Classification cache misses: Confirm Redis connectivity and fallback to PostgreSQL/SQLite
- Low model performance: Inspect training logs, thresholds, and recent validation data

**Section sources**
- [training.py:34-61](file://cyberbullying_api/routes/training.py#L34-L61)
- [db_memory.py:17-124](file://cyberbullying_api/classifier/db_memory.py#L17-L124)
- [retrain.py:420-425](file://cyberbullying_api/retrain.py#L420-L425)

## Conclusion
BullyGuard ID’s active learning system integrates automated classification with human-in-the-loop validation and continuous model improvement. Through confidence-aware routing, structured HITL workflows, and robust training orchestration with augmentation and rollback safety, the system maintains high accuracy while preserving human oversight. The frontend quadrant interface streamlines reviewer tasks, and persistent training history ensures traceability and accountability.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### Database Schema for Training Records, Validation Workflows, and Performance Tracking
- classification_memory: stores text hash, encrypted text, predicted labels, reasons, decision source, confidence, probabilities, validation flag, optional embeddings
- retraining_history: captures F1 scores, thresholds, and active version metadata

```mermaid
erDiagram
CLASSIFICATION_MEMORY {
varchar text_hash PK
text encrypted_text
boolean is_toxic
boolean is_bully
text reason
text decision_source
real confidence
real probability_toxic
real probability_bully
integer is_validated
vector embedding
timestamp timestamp
}
RETRAINING_HISTORY {
bigint id PK
timestamp timestamp
real f1_toxic
real f1_bully
real threshold_toxic
real threshold_bully
varchar active_version
}
```

**Diagram sources**
- [db_memory.py:54-79](file://cyberbullying_api/classifier/db_memory.py#L54-L79)
- [db_memory.py:676-705](file://cyberbullying_api/classifier/db_memory.py#L676-L705)

### HITL Review Interface Details
- Quadrant-based layout organizes items by toxicity/bullying outcomes
- Checkbox selection and reallocation buttons enable quick corrections
- Drag-and-drop support for moving items across quadrants
- Confidence indicators and decision source metadata aid review decisions

**Section sources**
- [Quadrant.tsx:1-262](file://frontend/src/components/ActiveLearning/Quadrant.tsx#L1-L262)

### API Definitions for HITL and Training
- GET /api/data/categorized: filters and paginates ambiguous predictions
- POST /api/data/reallocate: single reallocation update
- POST /api/data/reallocate/bulk: bulk reallocation
- POST /api/train/start: start training with model type
- POST /api/train/reload: manually reload models
- GET /api/train/logs: stream training logs
- GET /api/train/history: training history with pagination

**Section sources**
- [hitl.py:14-84](file://cyberbullying_api/routes/hitl.py#L14-L84)
- [training.py:29-259](file://cyberbullying_api/routes/training.py#L29-L259)
- [models.py:196-220](file://cyberbullying_api/models.py#L196-L220)