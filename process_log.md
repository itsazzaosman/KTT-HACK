# Process Log: AIMS KTT Hackathon T1.1

**Name:** Azza Osman  
**Date:** 22/04/2026

## 1. Hour-by-Hour Timeline
*The 4-hour build process.*

* **Hour 1 (10:45 AM - 11:45 AM):** * Setup (Repo, `SIGNED.md`, `process_log.md` initialized).
    * Wrote the synthetic data generator script using NumPy and Faker.
    * Verified data generation and train/test splits.
* **Hour 2 (11:45 AM - 12:45 PM):**
    * Merged member and group datasets for processing.
    * Engineered 9 predictive features including `feat_total_missed`, `feat_repayment_ratio`, recency-weighted miss scores, and on-time streaks.
    * Debugged and resolved pandas indexing issues (NaN alignment) during the train/test split.
* **Hour 3 (12:45 PM - 1:45 PM):**
    * Trained an XGBoost Classifier on the CPU.
    * Calibrated the probability outputs into a 0-100 Reliability Index, mapping to High Risk (0-40), Watch (41-70), and Low Risk (71-100) tiers.
    * Evaluated on the 100-member holdout, achieving an ROC-AUC of 0.982 and a Brier Score of 0.031.
    * Generated the 4 diagnostic charts (ROC Curve, Calibration Plot, Feature Importance, Per-District Heatmap).
* **Hour 4 (1:45 PM - 2:45 PM):**
    * Packaged the standalone `scorer.py` CLI tool.
    * Drafted the `ussd_flow.md` business artifact, including Kinyarwanda translations for offline users.
    * Deployed the model (`.pkl`) and formatted the Model Card on the Hugging Face Hub.
    * Finalized `README.md` and recorded the 4-minute video defense.

---

## 2. LLM & Assistant Tool Usage
*Declaring tools used and the reasoning behind them.* * **Tool 1: Gemini**
    * **Why I used it:** To debug a specific pandas NaN indexing error during my feature engineering phase, to translate the USSD fallback prompts into Kinyarwanda for the business artifact, and to figure out how to customize the Seaborn colormap (`cmap='RdYlGn'`) so my geographical heatmap intuitively displayed safe districts in green and risky districts in red.

---

## 3. Sample Prompts
*Three prompts actually used, and one discarded.* ### Used Prompts:
1.  *"Explain to me the deliverables in detila for the AIMS KTT Fellowship Hackathon based "*
2.  *"Correct it here: #initialize the Model model = XGBClassifier... test_results['actual_default'] = y_test"* (Used to fix the NaN bug in the results dataframe).
3.  *"Can I change the colour that these people have green... so that when it is safe than it green and when it becomes more risk then the more redish?"* (Used to customize the heatmap visualization).


---

## 4. The Single Hardest Decision
*A one-paragraph reflection.* The single hardest technical decision was balancing statistical granularity with business logic during model evaluation, specifically when creating the Calibration Plot. Because the designated holdout set was extremely small (exactly 100 members), plotting a standard calibration curve with 5 or 10 bins created wild, jagged spikes due to tiny sample sizes in the high-risk buckets. While dropping to `n_bins=2` created a mathematically flawless, smooth line, it erased the "Watch" tier completely. Ultimately, I made the decision to strictly use `n_bins=3`. This explicitly aligned the visualization with the three business tiers (Low Risk, Watch, High Risk), prioritizing business utility and transparency for stakeholders over a purely aesthetic chart, even if it meant showing a conservative bias in the middle tier. Also, it how to handle 'thin-file' members (those with < 4 months of history). I decided to implement a Shadow-Scoring system. Instead of giving a high-confidence integer, the system outputs a widened confidence interval (e.g., 96 with a range of 81-100). This communicates mathematical uncertainty to the Ikimina secretary, ensuring they don't over-rely on a score that hasn't been battle-tested by time. I also added a Group-Level Risk multiplier (5% penalty) for groups founded after 2024 to account for the lack of established social collateral in newer savings circles.