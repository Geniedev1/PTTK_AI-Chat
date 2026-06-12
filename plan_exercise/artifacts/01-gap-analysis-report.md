# Gap Analysis Report

## Scope lock

This report fixes the exercise scope against the current repository state so the remaining plans can be implemented with reproducible artifacts.

## Exercise-to-repo matrix

| Exercise requirement | Current repo state | Status | Concrete next step |
| --- | --- | --- | --- |
| `data_user500.csv` with at least `user_id, product_id, action, timestamp` | Repo had synthetic event generation and `data_100user.csv`, but no dedicated 500-user submission export | Partial | Add an orchestration command that generates 500-user events and exports both submission CSV and full CSV |
| Sequence dataset for sequence models | Repo had ranking dataset builder for actor-item MLP features, not sequence windows | Missing | Build an exercise sequence dataset artifact from full behavior CSV with train/valid/test split by actor |
| Train `RNN`, `LSTM`, `biLSTM` and choose `model_best` | Repo had only Plan 11B MLP training artifacts | Missing | Add a separate sequence-model training pipeline under `ai-service` for the exercise |
| Neo4j knowledge graph | Graph store, rebuild, and query APIs already exist in `interaction-service` | Done | Reuse current graph implementation and expose exercise evidence |
| Graph-grounded chat | Chat retrieval, graph context, and realtime routing already exist in `ai-service` | Done | Repackage evidence and make graph usage explicit in exercise artifacts |
| E-commerce UI integration | Frontend already has recommendation and chat entry points | Partial | Extend exercise evidence and tighten integration checkpoints |
| Evaluation and defense pack | Repo has scattered artifacts in `plan/artifacts` and `ai-service/artifacts` | Partial | Build a dedicated exercise artifact folder and summary/checklist files |

## Locked exercise decisions

### Submission CSV format

Submission CSV uses exactly these columns:

- `user_id`
- `product_id`
- `action`
- `timestamp`

`product_id` may be blank for actions that are not product-bound, such as `search` or some `chat` events. The full export remains separate and preserves richer context for graph/model pipelines.

### Behavior mapping

Exercise action vocabulary is locked to:

- `view`
- `click`
- `add_to_cart`
- `remove_from_cart`
- `checkout`
- `purchase`
- `search`
- `chat`

Mapping from current event schema:

- `product_viewed -> view`
- `product_clicked -> click`
- `cart_item_added -> add_to_cart`
- `cart_item_removed -> remove_from_cart`
- `checkout_started -> checkout`
- `order_paid/order_completed -> purchase`
- `search_performed -> search`
- `chat_message_sent -> chat`

### Sequence modeling task

The exercise sequence task is locked to:

- **Binary purchase-intent classification**

Definition:

- Given the recent behavior sequence of an actor, predict whether the near-future window contains high-intent conversion behavior, specifically `add_to_cart`, `checkout`, or `purchase`.

Why this task is locked:

- It is closer to the e-commerce business story than generic next-action classification.
- It fits the current repo's personalization and recommendation direction.
- It keeps the evaluation consistent across `RNN`, `LSTM`, and `biLSTM`.

### Artifact locations

Exercise artifacts are locked to these roots:

- Data export: `interaction-service/data_user500.csv`, `interaction-service/data_user500_full.csv`
- Data report: `interaction-service/data_user500_quality_report.json`
- Sequence dataset: `ai-service/artifacts/exercise_sequence/`
- Sequence models: `ai-service/artifacts/exercise_models/`
- Exercise plan evidence: `plan_exercise/artifacts/`

## Acceptance criteria

### Plan 01

- A single markdown file states what is done, partial, and missing.
- CSV schema and model task are explicitly locked.
- Artifact locations are fixed.

### Plan 02

- One command can regenerate the 500-user submission CSV and full CSV.
- Submission CSV has at least 500 distinct users.
- Submission CSV exposes at least 8 action types.
- A JSON quality report is written next to the CSV.

### Plan 03

- Sequence dataset artifacts can be regenerated from the full CSV.
- Train/valid/test splits are actor-separated.
- Preprocess config, vocab, and label map are saved.

### Plan 04

- `RNN`, `LSTM`, and `biLSTM` train from the same dataset and config family.
- Each model writes weights, config, metrics, and learning-curve artifacts.
- A comparison report declares the selection rule and names `model_best`.

## Canonical commands

These are the intended top-level commands after implementation:

```powershell
python manage.py build_exercise_data_user500
python manage.py build_exercise_sequence_dataset
python manage.py train_exercise_sequence_models
```
