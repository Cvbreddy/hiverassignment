# Submission checklist

Repository-side work is complete. Before sending the assignment:

- [x] Kaggle dataset downloaded and verified at `data/archive/twcs/twcs.csv`
- [x] Brand selected: `AppleSupport`
- [x] Runnable agent, ingestion, evaluation, tests, report, and judge rubric
- [x] 200 real AppleSupport messages exported to `data/apple_support_review.csv`
- [ ] Reviewer 1 labels every `intent` and `expected_action`
- [ ] Reviewer 2 labels the same 200 rows independently
- [ ] Disagreements adjudicated; completed file saved as `data/golden.csv`
- [ ] Final metrics generated with `reports/final_metrics.json`
- [ ] 30 replies scored by the LLM judge and by humans
- [ ] Exact agreement and weighted Cohen kappa added to the report
- [ ] Repository link shared with `anurag@hiverhq.com`

Do not report the checked-in 92.5% baseline as final accuracy. It uses generated labels and exists only as a smoke test.
