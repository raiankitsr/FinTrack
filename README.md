# 💰 FinTrack — Personal Finance & Crypto Portfolio Tracker

A modern, interactive personal finance dashboard built with Python and Streamlit.
Upload your own transaction CSV or explore with the built-in demo data.
Live crypto prices powered by the CoinGecko API (free, no key required).

## 🚀 Live Demo
[➡ Open App on Streamlit Cloud](#) ← replace with your deployed URL

## 📸 Features
- **KPI cards** — Total income, expenses, net savings, savings rate
- **Monthly trend** — Income vs expense line chart + savings bar chart
- **Expense breakdown** — Donut chart + horizontal bar by category
- **Waterfall chart** — Visual income → expenses → savings flow
- **Smart insights** — Auto-generated data-backed recommendations
- **Live crypto tracker** — Real-time BTC, ETH, SOL, BNB prices via CoinGecko
- **Upload your own data** — Bring your bank export CSV and see instant analysis

## 🛠 Tech Stack
| Tool | Purpose |
|------|---------|
| Python 3.11 | Core language |
| pandas | Data cleaning & analysis |
| Streamlit | Web app framework |
| Plotly | Interactive charts |
| CoinGecko API | Live crypto prices (free) |

## ⚡ Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/fintrack.git
cd fintrack

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate demo data (first time only)
python generate_data.py

# 4. Run the app
streamlit run app.py
```

## ☁️ Deploy to Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set main file as `app.py`
5. Click Deploy — live in 2 minutes ✅

## 📂 CSV Format (for your own data)

Your CSV needs these columns:
```
date, category, subcategory, amount, type, description
```
- `date` — YYYY-MM-DD format
- `type` — "income" or "expense"
- `amount` — positive number (INR)

## 📊 Sample Insights This Dashboard Reveals
- Which month had the highest spending?
- What % of income goes to each category?
- Is your savings rate above the 20% benchmark?
- How much is your crypto portfolio worth right now?

---
Built for Upwork portfolio · [Hire me on Upwork](#)
