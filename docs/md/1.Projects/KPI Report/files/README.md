# Olympic Paints — Sales Rep Portal

A secure, single-page portal for Olympic Paints Sales Managers to access forms, marketing materials and merchandising reports.

---

## 🚀 Deployment

This project is deployed automatically to **Vercel** on every push to the `main` branch.

**Live URL:** *(set after first Vercel deployment)*

---

## 📁 Project Structure

```
olympic-paints-portal/
├── index.html        # Main portal (single-page app)
├── vercel.json       # Vercel deployment config
├── .gitignore
└── README.md
```

---

## 🔐 Login Credentials

Each Sales Manager logs in with their name and a 4-digit PIN.

| SM Ref | Name            | Default PIN |
|--------|-----------------|-------------|
| AC     | Aboo Cassim     | 1234        |
| AP     | Amit Patel      | 2345        |
| BV     | Bhadresh Vallabh| 3456        |
| BM     | Byron Minnie    | 4567        |
| NP     | Nikhil Panchal  | 5678        |

> ⚠️ **Change the default PINs before going live.** Edit the `PINS` object in the `<script>` section of `index.html`.

---

## 📋 Forms

All forms are embedded via **JotForm** and submit directly to your JotForm account:

| Form | JotForm ID |
|------|-----------|
| Email Subscription | 260551758128057 |
| Store Visit Booking | 260431710573046 |
| Stock Return | 260113502715040 |
| Complaints & Feedback | *(built-in — connect to Google Sheets)* |

---

## 📦 Marketing Materials

Placeholder slots are ready in the **Marketing** page. To add real links:

1. Open `index.html`
2. Find the `mat-card` elements under each section (Price Lists, TDS, MSDS, Guides)
3. Replace the `+ Add link` button with an `<a href="YOUR_LINK">` tag pointing to your Google Drive or hosted PDF

---

## 📊 Merchandising Reports

Each SM can add Google Drive report links from within the portal. Reports are stored in session memory — for persistent storage across sessions, connect to a backend (e.g. Google Sheets via Apps Script, Supabase, or Airtable).

---

## 🛠️ Local Development

No build step required — this is a pure HTML/CSS/JS project.

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/olympic-paints-portal.git
cd olympic-paints-portal

# Open directly in browser
open index.html

# Or use a local server (recommended for JotForm iframes)
npx serve .
```

---

## ☁️ Deploy to Vercel

### Option A — Vercel Dashboard (easiest)
1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **Add New → Project**
3. Import your GitHub repository
4. Leave all settings as default — Vercel auto-detects the static site
5. Click **Deploy**

### Option B — Vercel CLI
```bash
npm i -g vercel
vercel --prod
```

---

## 🔄 Updating the Portal

1. Edit `index.html` locally
2. Commit and push to `main`
3. Vercel auto-deploys within ~30 seconds

```bash
git add .
git commit -m "Update portal"
git push origin main
```

---

## 📞 Support

Built for Olympic Paints internal use. For changes or additions, edit `index.html` directly or contact your developer.
