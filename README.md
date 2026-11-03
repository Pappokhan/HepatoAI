# HepatoAI - AI-assisted liver function screening (Streamlit, MVC)

```
hepatoai/
├── app.py                         # entry point (wires M, V, C together)
├── requirements.txt
├── artifacts/                     # best_model.pkl, scaler.pkl, *.json
└── app/
    ├── config.py                  # paths, feature specs, label mapping
    ├── models/                    # MODEL: artifact loading + prediction logic
    │   ├── model_loader.py
    │   ├── predictor.py
    │   ├── analysis.py            # range flags, risk band, findings
    │   ├── report_builder.py      # PDF report
    │   └── llm_client.py          # Gemini / Groq REST client
    ├── views/                     # VIEW: all Streamlit UI code
    │   ├── styles.py (CSS)  layout.py  input_view.py  result_view.py  agent_view.py  about_view.py
    └── controllers/               # CONTROLLER: validation + coordination
        └── prediction_controller.py
```

## Run
```
pip install -r requirements.txt
streamlit run app.py        # run from this folder so .streamlit/config.toml (theme) is loaded
```

## Deploy (Streamlit Community Cloud)
Push this folder to GitHub, then create a new app on share.streamlit.io with `app.py` as the main file.

## PDF report
After **Analyze**, click **Download PDF report**. The report (ReportLab, `app/models/report_builder.py`) contains patient details, result and risk band, biomarker table with reference ranges, key findings, model note and disclaimer. Reference ranges and risk-band thresholds are in `app/config.py`.

## AI assistant
1. Open `local_settings.py` and paste your key: `GEMINI_API_KEY = "..."` (or `GROQ_API_KEY`).
2. Run the app, open the **AI assistant** tab and click **Test AI connection**.

The app finds a working model for your key automatically (it lists the models your key can use and
retries if a model name is not found). To force one, set `GEMINI_MODEL` / `GROQ_MODEL` in `local_settings.py`.
`local_settings.py` is in `.gitignore`; for deployment (Streamlit Cloud) put the same names in **Secrets** instead.

## Important
Set `POSITIVE_LABEL` in `app/config.py` to the class label that means "liver disease" in your training data.

## Known model limitation
The LightGBM model reports 99.84% development accuracy but is unstable: with every marker inside its
reference range, a large share of inputs still get a high disease probability (a ~36% flag rate in a
random test of all-normal profiles). The app now shows a warning whenever the model output contradicts the
reference-range check, and passes that warning to the AI assistant and the PDF. The real fix is retraining
(split train/test *before* any oversampling, then validate on an independent set).
