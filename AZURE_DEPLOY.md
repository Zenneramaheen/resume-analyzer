# Deploy Resume Analyzer to Azure (free)

You need: VS Code, and your Azure for Students account — the Microsoft account you created with your **Gmail**. (Your college email was only used for the student-verification step; it is not a Microsoft account.)

## 1. Install the Azure tools

1. In VS Code, open Extensions (`Ctrl+Shift+X`).
2. Install **Azure Tools** (the extension pack by Microsoft).
3. Open the Azure panel (left sidebar, the blue "A" icon) and sign in with your **Gmail** — the Microsoft account you used to activate Azure for Students. Don't use your college email here: it isn't a Microsoft account, so signing in with it just bounces you back to the login screen.

## 2. Create the web app

1. In the Azure panel, find **App Service**, click **+** (Create).
2. Fill in:
   - **Name:** `resume-analyzer-zennera` (must be globally unique — add your name/numbers if taken)
   - **Runtime:** Python 3.12
   - **Pricing plan:** Free (F1) — costs nothing
   - **Region:** Central India (closest to Hyderabad)
3. Wait ~1 minute for it to be created.

## 3. Deploy your code

1. Right-click your new app in the Azure panel → **Deploy to Web App**.
2. Choose the folder: `~/workspace/projects/resume-analyzer` (or wherever you cloned it).
3. Confirm the deploy. It takes 2–5 minutes the first time.

## 4. Set the startup command (important — do this once)

1. In the Azure portal (portal.azure.com), open your app.
2. Go to **Configuration → General settings**.
3. Set **Startup Command** to:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. Click **Save**, then **Restart** the app.

## 5. Open it

- API docs: `https://resume-analyzer-zennera.azurewebsites.net/docs`
- Frontend: `https://resume-analyzer-zennera.azurewebsites.net/app`

(Replace `resume-analyzer-zennera` with whatever name you chose.)

## Optional but recommended

In **Configuration → Application settings**, add:

| Setting | Value | Why |
|---|---|---|
| `JWT_SECRET_KEY` | a long random string | Don't use the dev default in production |
| `OPENAI_API_KEY` | your key (if you have one) | Enables the AI bullet rewriter |

Generate a secret quickly: `python3 -c "import secrets; print(secrets.token_hex(32))"`

## Notes

- The **Free (F1)** plan is slow to wake up the first time someone visits (cold start ~30–60s). That's normal on free tiers.
- The database is SQLite stored on the app's disk — fine for a demo/portfolio. For real production you'd switch to Azure's free Postgres or Cosmos DB tier.
- Your $100 student credit covers this easily — the F1 plan itself is free, so you barely touch the credit.
