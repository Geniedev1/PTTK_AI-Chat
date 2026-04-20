# Exercise Sequence Model Comparison

Selection rule: highest validation F1, then validation AUC, then model name.

| Model | Valid Accuracy | Valid Precision | Valid Recall | Valid F1 | Valid AUC | Test F1 | Test AUC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rnn | 0.8951 | 0.8687 | 1.0000 | 0.9297 | 0.8983 | 0.9231 | 0.8945 |
| lstm | 0.8951 | 0.8687 | 1.0000 | 0.9297 | 0.8977 | 0.9231 | 0.8948 |
| bilstm | 0.8951 | 0.8687 | 1.0000 | 0.9297 | 0.8945 | 0.9231 | 0.8928 |

## model_best

Selected model: `rnn`

Reason: it achieved the highest validation F1 under the locked comparison rule.
