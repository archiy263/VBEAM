# VBEAM - VoiceMail AI Assistant 🎙️📧

[![Live Demo on Render](https://img.shields.io/badge/Live_Demo-Hosted_on_Render-blue?style=for-the-badge&logo=render)](https://vbeam-1.onrender.com/)

**VBEAM** is a state-of-the-art Multi-User SaaS platform that allows you to manage your Emails and Telegram messages entirely through your voice and a beautiful dark-mode interface. 

It is designed with complete Data Isolation, meaning hundreds of users can connect their Google and Telegram accounts simultaneously without any crossover. 

### 🌐 Live Production Demo
**Try it out here:** [https://vbeam-1.onrender.com/](https://vbeam-1.onrender.com/)

---

## 🔥 Key Features

- **True SaaS Multi-User Architecture**: Every user gets a personalized dashboard. Your contacts, email sessions, and Telegram dialogues are 100% isolated.
- **Voice Control & AI**: Send, read, and summarize emails or Telegram messages using intelligent NLP models and voice commands.
- **Custom Voice PINs**: Secure your send/reply operations with a customizable 4-digit Voice PIN to prevent accidental sending.
- **Google & Telegram Authentication**: Securely OAuth into Google and sync your phone with Telegram's core API (Telethon).
- **Admin Security Dashboard**: A live overview panel showcasing real-time active users and global platform metrics based on 10-minute session trackers.
- **Hybrid Database Engine**: Runs lightweight `SQLite` sequentially on your local machine, but natively transpiles queries to scale on `PostgreSQL 18` clusters in production!

---

## 🛠️ How to Run Locally (Development)

VBEAM uses a local `SQLite` database (`app_data.db`) out-of-the-box for rapid development.

1. **Clone the repository & Install Dependencies:**
   ```bash
   git clone https://github.com/your-username/vbeam.git
   cd vbeam
   pip install -r requirements.txt
   ```

2. **Environment Variables:**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   # Required Keys
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_BOT_TOKEN=your_bot_token
   GEMINI_API_KEY=your_gemini_key
   SECRET_KEY=super_secret_flask_key
   
   # Google Auth (Ensure credentials.json is in your root folder)
   GOOGLE_CREDENTIALS_PATH=credentials.json
   ```

3. **Run the Application:**
   ```bash
   python main.py
   ```
   Open `http://localhost:5000` in your browser.

---

## ☁️ How to Deploy to Render (Production)

The platform has a dynamic Hybrid Database Driver allowing it to bind to PostgreSQL instantly without any SQLAlchemy overhead.

1. **Push your code to GitHub.**
2. **Create a PostgreSQL Database on Render** (Select PostgreSQL 16/17/18). Copy the *Internal Database URL*.
3. **Create a "Web Service" on Render** connected to your GitHub repo.
4. **Environment Setup:** Set your Build Command to `pip install -r requirements.txt` and Start Command to `gunicorn -w 1 -b 0.0.0.0:$PORT main:app`.
5. **Inject Variables:** In your Render Environment Variables, paste all your `.env` keys. Crucially, add:
   ```env
   DATABASE_URL=postgres://... (Paste the Internal Database URL here)
   ```
6. **Deploy!** The `database.py` wrapper will detect `DATABASE_URL` and instantly port your entire architecture to the Postgres cluster!

---

### 🛡️ Built With
- **Backend**: Python 3, Flask, Gunicorn
- **Database**: SQLite (Local) / PostgreSQL 18 (Production)
- **Frontend**: HTML5, Vanilla JavaScript, TailwindCSS (Glassmorphism UI)
- **Integrations**: Google Gmail API, Telethon (Telegram), Google Gemini AI

**Developed by Dev & Archi Yadav**