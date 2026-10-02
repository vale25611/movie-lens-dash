# MovieLens Dashboard

Streamlit app for the MovieLens 100K ratings file in this repo.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)

1. Push this repo to a **public** GitHub repository (`main` branch).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
3. Deploy: repository = this repo, branch = `main`, main file = `app.py`.
4. Open the `*.streamlit.app` URL in a private window to confirm it loads.
