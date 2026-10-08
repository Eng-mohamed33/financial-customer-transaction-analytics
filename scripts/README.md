# Utility scripts

## Generate demo data

```bash
python scripts/generate_sample_data.py
```

The generator creates deterministic, synthetic CSV files in `data/raw/`. They are only for testing notebook execution and are not suitable for business conclusions. Replace them with the real source files before publishing insights.

## Run final QA

```bash
python scripts/validate_project.py
```

This checks the expected raw/processed files, notebook JSON, quality-report status, final dataset rows, and visualization count.

## Run everything without JupyterLab

```bash
python scripts/run_pipeline.py
```

This executes the notebooks in order in a background kernel, regenerates the chart catalog, and runs the final QA checks. It does not open a browser or JupyterLab window.
