# Deployment Guide — Quality Capture System

## Before You Deploy

### Step 1: Get Your Notion Integration Token

1. Go to https://www.notion.so/my-integrations
2. Click **"New integration"**
3. Name it "Quality Capture" and select your workspace
4. Under **Capabilities**, enable: Read content, Update content, Insert content
5. Click **Save** → copy the **Internal Integration Token** (starts with `secret_...`)

### Step 2: Share the Notion databases with your integration

1. Open your Notion workspace and navigate to the **🎨 Quality Capture System** page
2. Click **"..."** menu → **"Connect to"** → select your "Quality Capture" integration
3. This grants the integration access to all databases under that page

The Notion workspace is already set up with all 6 databases and seeded with baseline/goal KPI values.

## Deploy to Vercel

### Option A — Deploy via Vercel Dashboard (recommended)

1. Push the project to a GitHub repository
2. Go to https://vercel.com and click **"Add New Project"**
3. Import your repository
4. In the **"Environment Variables"** section, add:
   - `NOTION_TOKEN` = (paste your integration token from Step 1)
   - `NEXT_PUBLIC_ADMIN_PIN` = (your chosen 4-digit PIN)
5. Click **"Deploy"**
6. Vercel will build and deploy the app — takes ~2 minutes

### Option B — Deploy via CLI

Install Vercel CLI if needed: `npm install -g vercel`

```bash
cd quality-capture
vercel
```

Follow the prompts to link to your Vercel account. Set environment variables:
```bash
vercel env add NOTION_TOKEN
vercel env add NEXT_PUBLIC_ADMIN_PIN
```

## After Deployment

### Configure the System (Admin Panel)

1. Open `https://your-app.vercel.app/admin`
2. Enter your 4-digit PIN
3. **Staff Roster** tab → Add 4 assistants and 4 supervisors (names to be confirmed)
4. **Ford Cups** tab → Add ford cup types (confirm specs with production team)
5. **Viscosity Targets** tab → Set min/max seconds per product tier per ford cup
6. **Colour Library** tab → Add Olympic Paints colours with hex codes by product tier
7. **KPI Config** tab → Verify Baseline = 82, Goal = 92

> **Note:** All configuration is stored directly in your Notion workspace. You can also manage the data directly in Notion — changes are reflected immediately in the app.

### Tablet Setup

1. On the Android tablet, open Chrome and go to `https://your-app.vercel.app/tablet`
2. Tap the browser menu → **"Add to Home Screen"** → **"Install"**
3. The app will install as a standalone PWA on the tablet home screen
4. Open it from the home screen — it should launch in landscape fullscreen

### Supervisor Dashboard

1. Supervisors open `https://your-app.vercel.app/dashboard` in any browser
2. No login required — dashboard is read-only

## URLs at a Glance

| Who | URL | Purpose |
|-----|-----|---------|
| Assistants | `/tablet` | Record batch quality checks |
| Quintus / Supervisors | `/dashboard` | View KPI rates and batch results |
| Quintus (admin) | `/admin` | Configure the system |

## Notion Workspace

The data lives in your Notion workspace at:
**🎨 Quality Capture System** page → 6 linked databases

| Database | Purpose |
|----------|---------|
| Batches | One record per batch quality check |
| Colours | Olympic Paints colour reference library |
| Staff | Assistants and supervisors |
| Ford Cups | Cup configurations |
| Viscosity Targets | Target ranges per product tier |
| KPI Config | Baseline (82%) and goal (92%) |

You can view, filter, and export data directly in Notion at any time.

## Troubleshooting

**"Error loading batches"** on the tablet or dashboard:
- Check that `NOTION_TOKEN` is set correctly in Vercel environment variables
- Verify the integration has been connected to the Quality Capture System page in Notion (Step 2 above)

**Admin PIN not working:**
- Check `NEXT_PUBLIC_ADMIN_PIN` in Vercel environment variables
- Default PIN if env var is not set: `1234`

**Tablet app not installing as PWA:**
- Must be accessed over HTTPS (Vercel provides this automatically)
- Use Chrome on Android for best PWA support

## KPI Scoreboard

Once the system is live and batches are being recorded:
- Open `/dashboard` → **"This Month's Rate"** card shows the current KPI value
- Use **"Export CSV"** for detailed data for the monthly ChangeLab KPI meeting
- Or view the **Batches** database directly in Notion and filter/export there
