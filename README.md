# 🌳 TreeWatch Melbourne

Real-time fallen tree incident dashboard for arborists.
Pulls from VicEmergency/SES feed + Twitter/X social reports.

---

## Project structure

```
treewatch-melbourne/
├── index.html        ← Frontend dashboard (deploy to Netlify)
├── api.py            ← FastAPI backend (deploy to Railway)
├── requirements.txt  ← Python dependencies
├── Procfile          ← Tells Railway how to start the server
└── README.md
```

---

## Step 1 — Deploy the backend to Railway (free)

Railway hosts your Python API and gives you a public URL.

### Install Railway CLI
```bash
npm install -g @railway/cli
```

### Deploy
```bash
cd treewatch-melbourne
railway login          # opens browser to authenticate
railway init           # creates a new Railway project, name it "treewatch-api"
railway up             # deploys api.py
```

Railway will give you a URL like:
```
https://treewatch-api-production.up.railway.app
```

Test it works:
```bash
curl https://your-url.railway.app/incidents
```

You should see a JSON response with incidents.

---

## Step 2 — Connect the frontend to your API

Open `index.html` and find this line near the top of the `<script>` block:

```javascript
const API_URL = null; // Set to null to use demo data
```

Replace `null` with your Railway URL:

```javascript
const API_URL = 'https://treewatch-api-production.up.railway.app/incidents';
```

Save the file.

---

## Step 3 — Deploy the frontend to Netlify (free, 60 seconds)

### Option A — Drag and drop (easiest)
1. Go to https://app.netlify.com/drop
2. Drag your `index.html` file onto the page
3. Netlify gives you a URL instantly — share it with your team!

### Option B — Netlify CLI
```bash
npm install -g netlify-cli
netlify login
netlify deploy --prod --dir . --filter index.html
```

Your dashboard will be live at something like:
```
https://treewatch-melbourne.netlify.app
```

---

## Step 4 — Share with your team

Send them the Netlify URL. That's it — they open it in any browser,
no installation needed.

---

## Adding Twitter/X reports (optional, later)

To add social media data, you'll need an X API Basic account (~$100/month).
Once you have a Bearer Token, add to `api.py`:

```python
import tweepy

client = tweepy.Client(bearer_token="YOUR_BEARER_TOKEN")

def get_social_reports():
    query = '(fallen tree OR tree down) melbourne -is:retweet lang:en'
    tweets = client.search_recent_tweets(query=query, max_results=20,
                tweet_fields=["created_at","geo","text"])
    return [{"type": "social", "desc": t.text, ...} for t in tweets.data or []]
```

A cheaper alternative: monitor @VicEmergency and @SES_Victoria official accounts,
which are public and free.

---

## Refreshing data

The frontend auto-refreshes every 2 minutes when connected to the live API.
The VicEmergency feed updates roughly every 5-10 minutes during incidents.

---

## Support

Built with FastAPI + Netlify + VicEmergency open data.
VicEmergency feed: https://emergency.vic.gov.au/public/osom-feed.json
