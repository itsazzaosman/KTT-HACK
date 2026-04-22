# Ikimina Digital Trust Index

This repository contains the complete machine learning pipeline and business adaptation for the KTT Hackathon. We built an offline-first, USSD-ready predictive model that evaluates the financial reliability of Ikimina (savings group) members.

## 📁 Repository Structure
* `ikimina_members.csv` & `ikimina_groups.csv` - The generated tabular dataset.
* `train.ipynb` - The full pipeline: Feature engineering, XGBoost training, calibration, and all diagnostic charts (ROC curve, heatmap, etc.).
* `scorer.py` - The standalone command-line script to score individual members.
* `ussd_flow.md` - The business and product adaptation document designing the Kinyarwanda USSD interface.
* `requirements.txt` - Python dependencies.

## 🔗 Hosted Model
The trained XGBoost model (`.pkl`) and its formal Model Card are hosted publicly on Hugging Face:
👉 **https://huggingface.co/itsazza/ikimina-xgboost-scorer**

## 🚀 How to Run the Scorer (Live Demo)
This project strictly adheres to the 2-command rule and runs entirely on the CPU. 

**Install dependencies:**
```bash
pip install -r requirements.txt