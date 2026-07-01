# Model Retraining and Deployment Pipeline

<cite>
**Referenced Files in This Document**
- [main.py](file://cyberbullying_api/main.py)
- [routes/training.py](file://cyberbullying_api/routes/training.py)
- [retrain.py](file://cyberbullying_api/retrain.py)
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [monitoring.py](file://cyberbullying_api/monitoring.py)
- [models/current_model_version.json](file://cyberbullying_api/models/current_model_version.json)
- [classifier/predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [classifier/database.py](file://cyberbullying_api/classifier/database.py)
- [classifier/db_cache.py](file://cyberbullying_api/classifier/db_cache.py)
- [classifier/settings_store.py](file://cyberbullying_api/classifier/settings_store.py)
- [training/data_loader.py](file://cyberbullying_api/training/data_loader.py)
- [training/augmentation.py](file://cyberbullying_api/training/augmentation.py)
- [tasks.py](file://cyberbullying_api/tasks.py)
- [Dockerfile](file://cyberbullying_api/Dockerfile)
- [docker-compose.yml](file://docker-compose.yml)
- [docker-compose.prod.yml](file://docker-compose.prod.yml)
- [scripts/benchmark_inference.py](file://scripts/benchmark_inference.py)
- [docs/ROLLBACK_PLAN.md](file://docs/ROLLBACK_PLAN.md)
- [docs/FINAL_INTEGRATION_GUIDE.md](file://docs/FINAL_INTEGRATION_GUIDE.md)
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
This document describes the end-to-end model retraining and deployment pipeline for the cyberbullying detection system. It covers training orchestration, job management, ONNX export and optimization, deployment verification, monitoring, rollback, and automated retraining triggers. It also documents the integration between training results and model serving, including A/B testing readiness, and the relationship between active learning feedback and retraining triggers.

## Project Structure
The pipeline spans backend services, training utilities, monitoring, and deployment configurations:
- API entrypoint and route registration
- Training orchestration and job management
- Retraining automation and ONNX export
- Monitoring and alerting
- Model metadata and serving integration
- Containerization and orchestration

```mermaid
graph TB
subgraph "API Layer"
MAIN["main.py"]
ROUTE_TRAIN["routes/training.py"]
end
subgraph "Training"
RETRAIN["retrain.py"]
DATA["training/data_loader.py"]
AUG["training/augmentation.py"]
end
subgraph "Export & Serving"
EXPORT["export_onnx.py"]
PREDICTOR["classifier/predictor.py"]
DB["classifier/database.py"]
CACHE["classifier/db_cache.py"]
SETTINGS["classifier/settings_store.py"]
end
subgraph "Monitoring & Ops"
MON["monitoring.py"]
VERSION["models/current_model_version.json"]
DOCKER["Dockerfile"]
DC_DEV["docker-compose.yml"]
DC_PROD["docker-compose.prod.yml"]
end
MAIN --> ROUTE_TRAIN
ROUTE_TRAIN --> RETRAIN
RETRAIN --> DATA
RETRAIN --> AUG
RETRAIN --> EXPORT
EXPORT --> PREDICTOR
PREDICTOR --> DB
PREDICTOR --> CACHE
PREDICTOR --> SETTINGS
PREDICTOR --> VERSION
MON --> PREDICTOR
DOCKER --> MAIN
DC_DEV --> MAIN
DC_PROD --> MAIN
```

**Diagram sources**
- [main.py](file://cyberbullying_api/main.py)
- [routes/training.py](file://cyberbullying_api/routes/training.py)
- [retrain.py](file://cyberbullying_api/retrain.py)
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [classifier/predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [classifier/database.py](file://cyberbullying_api/classifier/database.py)
- [classifier/db_cache.py](file://cyberbullying_api/classifier/db_cache.py)
- [classifier/settings_store.py](file://cyberbullying_api/classifier/settings_store.py)
- [training/data_loader.py](file://cyberbullying_api/training/data_loader.py)
- [training/augmentation.py](file://cyberbullying_api/training/augmentation.py)
- [monitoring.py](file://cyberbullying_api/monitoring.py)
- [models/current_model_version.json](file://cyberbullying_api/models/current_model_version.json)
- [Dockerfile](file://cyberbullying_api/Dockerfile)
- [docker-compose.yml](file://docker-compose.yml)
- [docker-compose.prod.yml](file://docker-compose.prod.yml)

**Section sources**
- [main.py](file://cyberbullying_api/main.py)
- [routes/training.py](file://cyberbullying_api/routes/training.py)
- [retrain.py](file://cyberbullying_api/retrain.py)
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [classifier/predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [classifier/database.py](file://cyberbullying_api/classifier/database.py)
- [classifier/db_cache.py](file://cyberbullying_api/classifier/db_cache.py)
- [classifier/settings_store.py](file://cyberbullying_api/classifier/settings_store.py)
- [training/data_loader.py](file://cyberbullying_api/training/data_loader.py)
- [training/augmentation.py](file://cyberbullying_api/training/augmentation.py)
- [monitoring.py](file://cyberbullying_api/monitoring.py)
- [models/current_model_version.json](file://cyberbullying_api/models/current_model_version.json)
- [Dockerfile](file://cyberbullying_api/Dockerfile)
- [docker-compose.yml](file://docker-compose.yml)
- [docker-compose.prod.yml](file://docker-compose.prod.yml)

## Core Components
- API entrypoint and route registration define the training orchestration surface.
- Training orchestration coordinates data loading, augmentation, model training, and export.
- Export pipeline produces optimized ONNX artifacts for serving.
- Model serving integrates with predictor, cache, and settings stores.
- Monitoring tracks performance and triggers automated retraining.
- Versioning and rollback plans ensure safe deployments.

**Section sources**
- [main.py](file://cyberbullying_api/main.py)
- [routes/training.py](file://cyberbullying_api/routes/training.py)
- [retrain.py](file://cyberbullying_api/retrain.py)
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [classifier/predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [monitoring.py](file://cyberbullying_api/monitoring.py)
- [models/current_model_version.json](file://cyberbullying_api/models/current_model_version.json)

## Architecture Overview
The pipeline orchestrates training jobs via the API, executes training and export, updates model metadata, and verifies deployment readiness. Monitoring informs automated retraining triggers.

```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "API Server"
participant TrainRoute as "POST /api/train/start"
participant Retrain as "Retraining Orchestrator"
participant Export as "ONNX Export"
participant Predictor as "Predictor"
participant Monitor as "Monitoring"
Client->>API : "POST /api/train/start"
API->>TrainRoute : "Dispatch training job"
TrainRoute->>Retrain : "Start training workflow"
Retrain->>Retrain : "Load data, augment, train"
Retrain->>Export : "Export to ONNX"
Export-->>Retrain : "ONNX artifact"
Retrain->>Predictor : "Update model metadata"
Predictor-->>Monitor : "Deployment verification"
Monitor-->>Client : "Training result and metrics"
```

**Diagram sources**
- [routes/training.py](file://cyberbullying_api/routes/training.py)
- [retrain.py](file://cyberbullying_api/retrain.py)
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [classifier/predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [monitoring.py](file://cyberbullying_api/monitoring.py)

## Detailed Component Analysis

### Training Orchestration and Job Management
- Endpoint: POST /api/train/start initiates training workflows.
- Responsibilities:
  - Validate training parameters and datasets.
  - Trigger data loading and augmentation.
  - Execute training loop and evaluation.
  - Persist model artifacts and metadata.
  - Publish training progress and outcomes.
- Job lifecycle:
  - Enqueue training job.
  - Stream progress to clients.
  - On completion, trigger export and deployment verification.

```mermaid
flowchart TD
Start(["POST /api/train/start"]) --> Validate["Validate inputs and datasets"]
Validate --> Enqueue["Enqueue training job"]
Enqueue --> Load["Load and augment data"]
Load --> Train["Run training and evaluation"]
Train --> Export["Export to ONNX"]
Export --> UpdateMeta["Update model metadata"]
UpdateMeta --> Verify["Deployment verification"]
Verify --> Complete(["Training complete"])
```

**Diagram sources**
- [routes/training.py](file://cyberbullying_api/routes/training.py)
- [retrain.py](file://cyberbullying_api/retrain.py)
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [models/current_model_version.json](file://cyberbullying_api/models/current_model_version.json)

**Section sources**
- [routes/training.py](file://cyberbullying_api/routes/training.py)
- [retrain.py](file://cyberbullying_api/retrain.py)
- [training/data_loader.py](file://cyberbullying_api/training/data_loader.py)
- [training/augmentation.py](file://cyberbullying_api/training/augmentation.py)

### ONNX Export and Deployment Preparation
- Export pipeline converts trained models to ONNX for inference optimization.
- Deployment preparation includes:
  - Artifact validation and benchmarking.
  - Model metadata update.
  - Serving readiness checks.
- Benchmarking script validates performance characteristics post-export.

```mermaid
flowchart TD
ExportStart["Export to ONNX"] --> ValidateONNX["Validate ONNX model"]
ValidateONNX --> Benchmark["Run inference benchmark"]
Benchmark --> Metadata["Update model metadata"]
Metadata --> Ready["Mark as deployable"]
```

**Diagram sources**
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [models/current_model_version.json](file://cyberbullying_api/models/current_model_version.json)
- [scripts/benchmark_inference.py](file://scripts/benchmark_inference.py)

**Section sources**
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [models/current_model_version.json](file://cyberbullying_api/models/current_model_version.json)
- [scripts/benchmark_inference.py](file://scripts/benchmark_inference.py)

### Model Serving Integration and Rollback
- Serving integrates with predictor, cache, and settings stores.
- Rollback plan ensures safe rollbacks to previous model versions.
- A/B testing readiness can be achieved by maintaining multiple model versions and routing strategies.

```mermaid
graph LR
Predictor["Predictor"] --> Cache["db_cache"]
Predictor --> DB["database"]
Predictor --> Settings["settings_store"]
Predictor --> Version["current_model_version.json"]
Rollback["Rollback Plan"] --> Version
```

**Diagram sources**
- [classifier/predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [classifier/db_cache.py](file://cyberbullying_api/classifier/db_cache.py)
- [classifier/database.py](file://cyberbullying_api/classifier/database.py)
- [classifier/settings_store.py](file://cyberbullying_api/classifier/settings_store.py)
- [models/current_model_version.json](file://cyberbullying_api/models/current_model_version.json)
- [docs/ROLLBACK_PLAN.md](file://docs/ROLLBACK_PLAN.md)

**Section sources**
- [classifier/predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [classifier/db_cache.py](file://cyberbullying_api/classifier/db_cache.py)
- [classifier/database.py](file://cyberbullying_api/classifier/database.py)
- [classifier/settings_store.py](file://cyberbullying_api/classifier/settings_store.py)
- [models/current_model_version.json](file://cyberbullying_api/models/current_model_version.json)
- [docs/ROLLBACK_PLAN.md](file://docs/ROLLBACK_PLAN.md)

### Automated Retraining Triggers
- Triggers include:
  - Performance degradation thresholds.
  - Data drift detection signals.
  - Quality metric regressions.
- Monitoring module emits alerts and events consumed by the retraining orchestrator.
- Active learning feedback can feed drift and quality signals to trigger retraining.

```mermaid
flowchart TD
Observe["Observe Metrics & Drift"] --> Thresholds{"Exceed thresholds?"}
Thresholds --> |Yes| Queue["Queue Retraining"]
Thresholds --> |No| Wait["Continue monitoring"]
Queue --> Retrain["Automated Retrain"]
Retrain --> Verify["Verify deployment"]
Verify --> Alert["Alert stakeholders"]
```

**Diagram sources**
- [monitoring.py](file://cyberbullying_api/monitoring.py)
- [retrain.py](file://cyberbullying_api/retrain.py)

**Section sources**
- [monitoring.py](file://cyberbullying_api/monitoring.py)
- [retrain.py](file://cyberbullying_api/retrain.py)

### Practical Retraining Cycle Example
- Data validation: Ensure dataset integrity and label distributions.
- Training: Run training with configured hyperparameters and augmentations.
- Export: Convert to ONNX and benchmark inference.
- Deployment verification: Confirm serving readiness and performance targets.
- Monitoring: Track metrics and set up automated triggers for future cycles.

```mermaid
sequenceDiagram
participant Admin as "Admin"
participant API as "API"
participant Train as "Training Orchestrator"
participant Export as "ONNX Export"
participant Serve as "Predictor"
participant Mon as "Monitoring"
Admin->>API : "Start training"
API->>Train : "Execute workflow"
Train->>Export : "Export model"
Export->>Serve : "Deploy model"
Serve->>Mon : "Report metrics"
Mon-->>Admin : "Cycle summary"
```

**Diagram sources**
- [routes/training.py](file://cyberbullying_api/routes/training.py)
- [retrain.py](file://cyberbullying_api/retrain.py)
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [classifier/predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [monitoring.py](file://cyberbullying_api/monitoring.py)

**Section sources**
- [routes/training.py](file://cyberbullying_api/routes/training.py)
- [retrain.py](file://cyberbullying_api/retrain.py)
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [classifier/predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [monitoring.py](file://cyberbullying_api/monitoring.py)

### Training Resource Management and GPU Utilization
- Containerization supports GPU-accelerated training environments.
- Compose configurations define development and production runtime environments.
- Tasks orchestration coordinates long-running training jobs.

```mermaid
graph TB
Dev["docker-compose.yml"] --> API["API Service"]
Prod["docker-compose.prod.yml"] --> API
API --> GPU["GPU-enabled training"]
Tasks["tasks.py"] --> GPU
```

**Diagram sources**
- [docker-compose.yml](file://docker-compose.yml)
- [docker-compose.prod.yml](file://docker-compose.prod.yml)
- [tasks.py](file://cyberbullying_api/tasks.py)
- [Dockerfile](file://cyberbullying_api/Dockerfile)

**Section sources**
- [docker-compose.yml](file://docker-compose.yml)
- [docker-compose.prod.yml](file://docker-compose.prod.yml)
- [tasks.py](file://cyberbullying_api/tasks.py)
- [Dockerfile](file://cyberbullying_api/Dockerfile)

## Dependency Analysis
The pipeline exhibits clear separation of concerns:
- Routes depend on retraining orchestrator.
- Retraining depends on data loader and augmentation.
- Export depends on trained model artifacts.
- Serving depends on predictor, cache, database, and settings.
- Monitoring depends on metrics and alerting systems.

```mermaid
graph LR
Routes["routes/training.py"] --> Retrain["retrain.py"]
Retrain --> Data["training/data_loader.py"]
Retrain --> Aug["training/augmentation.py"]
Retrain --> Export["export_onnx.py"]
Export --> Predictor["classifier/predictor.py"]
Predictor --> DB["classifier/database.py"]
Predictor --> Cache["classifier/db_cache.py"]
Predictor --> Settings["classifier/settings_store.py"]
Monitor["monitoring.py"] --> Retrain
Monitor --> Predictor
```

**Diagram sources**
- [routes/training.py](file://cyberbullying_api/routes/training.py)
- [retrain.py](file://cyberbullying_api/retrain.py)
- [training/data_loader.py](file://cyberbullying_api/training/data_loader.py)
- [training/augmentation.py](file://cyberbullying_api/training/augmentation.py)
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [classifier/predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [classifier/database.py](file://cyberbullying_api/classifier/database.py)
- [classifier/db_cache.py](file://cyberbullying_api/classifier/db_cache.py)
- [classifier/settings_store.py](file://cyberbullying_api/classifier/settings_store.py)
- [monitoring.py](file://cyberbullying_api/monitoring.py)

**Section sources**
- [routes/training.py](file://cyberbullying_api/routes/training.py)
- [retrain.py](file://cyberbullying_api/retrain.py)
- [training/data_loader.py](file://cyberbullying_api/training/data_loader.py)
- [training/augmentation.py](file://cyberbullying_api/training/augmentation.py)
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [classifier/predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [classifier/database.py](file://cyberbullying_api/classifier/database.py)
- [classifier/db_cache.py](file://cyberbullying_api/classifier/db_cache.py)
- [classifier/settings_store.py](file://cyberbullying_api/classifier/settings_store.py)
- [monitoring.py](file://cyberbullying_api/monitoring.py)

## Performance Considerations
- Use ONNX export to optimize inference latency and footprint.
- Benchmark inference performance post-export to validate improvements.
- Monitor GPU utilization and adjust batch sizes or parallelism accordingly.
- Employ caching and efficient data loaders to reduce I/O bottlenecks during training.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- Training failures: Inspect training logs, validate dataset integrity, and confirm augmentation parameters.
- Export errors: Verify model compatibility and ONNX export steps.
- Serving issues: Check model metadata updates and predictor configuration.
- Rollback procedures: Follow documented rollback steps to revert to a known-good model version.
- Monitoring anomalies: Review alert thresholds and metric baselines.

**Section sources**
- [retrain.py](file://cyberbullying_api/retrain.py)
- [export_onnx.py](file://cyberbullying_api/export_onnx.py)
- [classifier/predictor.py](file://cyberbullying_api/classifier/predictor.py)
- [monitoring.py](file://cyberbullying_api/monitoring.py)
- [docs/ROLLBACK_PLAN.md](file://docs/ROLLBACK_PLAN.md)

## Conclusion
The pipeline integrates training orchestration, export and optimization, deployment verification, and monitoring to enable reliable and repeatable model retraining. Automated triggers and rollback mechanisms ensure robustness, while containerized environments support scalable GPU utilization. The documented processes and diagrams provide a blueprint for extending A/B testing and incorporating active learning feedback loops.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices
- Integration checklist: See FINAL_INTEGRATION_GUIDE for deployment verification steps.
- Benchmarking: Use the included benchmark script to measure inference performance after export.

**Section sources**
- [docs/FINAL_INTEGRATION_GUIDE.md](file://docs/FINAL_INTEGRATION_GUIDE.md)
- [scripts/benchmark_inference.py](file://scripts/benchmark_inference.py)