# Hiver SDE Intern Take-Home: Auditable Support Agent

This repo contains a runnable support agent for the selected `AppleSupport` brand. The reference system is deliberately deterministic: it classifies with transparent lexical rules, retrieves the closest historical resolution, drafts from that evidence, and escalates when confidence is low or the request is sensitive/high-risk. An optional OpenAI-compatible judge is included for reply-quality scoring.

## Current status

The repository is runnable, but the checked-in headline result is a **baseline smoke test**, not the final assignment evidence. The 160 labels in `data/golden.csv` are generated paraphrases, not hand-labeled real customer messages. Do not present the 92.5% number as a real-data result until `data/golden.csv` is replaced with reviewed examples from the selected brand.

## Baseline result

On the fixed, stratified 160-example golden set in [`data/golden.csv`](data/golden.csv):

| Metric | Result |
| --- | ---: |
| Intent accuracy | 92.5% |
| Macro intent recall | 92.5% |
| Action agreement with labels | 85.0% |
| Escalation rate | 40.0% |

These are baseline results on a small review set, not a claim about full Kaggle performance. The set has 20 examples for each of 8 intents and is intentionally easy to inspect. Before deployment, sample new conversations by time and customer thread, label them blind, and rerun the harness.

## Reproduce in under 15 minutes

Requires Python 3.10+ and no external packages.

```bash
python3 scripts/make_golden.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m hiver_agent.cli demo --text "I was charged twice and need a refund"
PYTHONPATH=src python3 -m hiver_agent.cli run \
  --input data/demo_conversations.csv \
  --golden data/golden.csv \
  --output reports/metrics.json

# Bounded run over the downloaded Kaggle file (adjust brand and row limit)
PYTHONPATH=src python3 -m hiver_agent.cli run \
  --input data/archive/twcs/twcs.csv \
  --brand AppleSupport \
  --brand-author-id AppleSupport \
  --max-rows 50000 \
  --golden data/golden.csv \
  --output reports/kaggle_smoke_metrics.json
```

The command writes JSON metrics to `reports/metrics.json`. The default demo corpus is intentionally tiny so the repository runs offline. To evaluate the Kaggle export, download `customer_support_on_twitter.csv`, then run the same command with `--input path/to/file.csv`. The loader accepts the usual Kaggle columns (`tweet_id`, `author_id`, `inbound`, `text`, `response_tweet_id`) and pairs inbound tweets with their response tweet. Use `--brand-author-id` when the export contains multiple support brands.

The checked-in `data/apple_support_review.csv` contains 200 real AppleSupport messages and their historical replies. The companion `data/golden.csv` is currently filled with **AI-assisted preliminary labels** so the pipeline can run; these are not independent human ground truth and must be reviewed before claiming final metrics. To recreate the unlabeled file:

```bash
PYTHONPATH=src python3 scripts/export_review_set.py \
  --input data/archive/twcs/twcs.csv \
  --brand-author-id AppleSupport \
  --output data/review_candidates.csv \
  --limit 200
```

Have two reviewers verify or correct `intent` and `expected_action`, adjudicate disagreements, and save the completed 150-250 rows as `data/golden.csv`. This human-labeling step cannot be automated honestly by the repository.

## Agent contract

Each prediction returns:

- `intent`: one of `billing_refund`, `delivery_tracking`, `technical_problem`, `account_access`, `product_information`, `cancellation`, `complaint`, or `other`.
- `reply`: a public-safe draft copied from the closest historical resolution pattern.
- `action`: `auto-handle` or `escalate`.
- `escalation_reason`: an explicit, human-readable reason.
- `evidence`: the historical resolution strings used by retrieval.

Sensitive requests never receive a request to post private data. The draft routes them to a specialist and tells the user to continue securely.

## Evaluation and judge

`hiver_agent.evaluate` computes accuracy, macro recall, confusion counts, and action agreement. The rubric in `hiver_agent.evaluate.judge_rubric()` scores grounding, helpfulness, tone, and safety from 1 to 5; a passing reply averages at least 4 and has safety at least 4. `hiver_agent.judge.score_with_openai` sends the candidate, evidence, and rubric to an OpenAI-compatible JSON judge when `OPENAI_API_KEY` is present. It uses temperature 0 and does not make the judge part of agent inference.

For human agreement, blind-score 30 predictions sampled across intents with two raters, then report exact agreement and weighted Cohen kappa between each rater and the judge. This protocol is intentionally explicit because judge agreement is evidence to collect, not a number to invent. The judge prompt and output schema are fully reproducible in [`src/hiver_agent/judge.py`](src/hiver_agent/judge.py).

## Sampling and labeling note

The golden set is a fixed, stratified review artifact: 20 prompts per intent, built from common request forms and paraphrases, with action labels assigned by the conservative policy above. It is separate from the demo retrieval corpus. In a production evaluation, replace these paraphrases with a random, time-sliced sample of real inbound threads, de-duplicate near-identical tweets, and have two people label intent, acceptable resolution, and escalation independently before adjudication.

## Report and decision log

1. **One brand, not a universal model:** a brand-specific corpus makes historical resolution behavior measurable and avoids pretending policies transfer across brands.
2. **Deterministic reference agent:** reproducibility and debuggability matter more than a black-box score for the first baseline.
3. **Eight intents:** these are operational buckets that map to distinct next actions; `other` prevents forced classifications.
4. **Historical evidence is mandatory:** every auto-draft must point to retrieved resolution text.
5. **Public-channel safety first:** passwords, card data, and sensitive identifiers trigger escalation rather than a public troubleshooting exchange.
6. **Conservative escalation:** ambiguity, complaints, and high-risk terms go to people even when an answer might be possible.
7. **Confidence is not probability:** the displayed score is a ranking heuristic and is not calibrated.
8. **Thread pairing uses dataset IDs:** response IDs are more reliable than adjacency in a noisy export.
9. **No synthetic full-dataset claim:** the headline metric is explicitly limited to the checked-in golden artifact.
10. **Judge is separated from inference:** an LLM can audit drafts without deciding production actions.
11. **Human agreement is required:** judge quality is reported against humans, not only against itself.
12. **No hidden dependencies:** the baseline and tests run with the Python standard library.

## Known limitations

The lexical classifier misses novel wording and overlapping intents; retrieval currently uses token overlap and sequence similarity; Kaggle brand identity must be supplied or inferred from the most common outbound author; and the included golden set is a review seed rather than a statistically representative sample. The next highest-value improvement is to label real, time-sliced examples and calibrate escalation thresholds on false-negative cost.
