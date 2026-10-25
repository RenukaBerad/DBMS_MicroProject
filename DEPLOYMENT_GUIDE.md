# Deployment & Hosting Guide — Internal Marks Management System

This guide outlines how to deploy and run your **Internal Marks Management System** web dashboard, both locally on your machine and online using free cloud hosting platforms.

---

## 1. Quick Local Web Deployment (1-Click)

Your web server is currently configured and running at:
👉 **[http://localhost:5000](http://localhost:5000)** (or `http://127.0.0.1:5000`)

To launch it at any time on your Windows computer:
- Double-click [`run_web.bat`](file:///c:/Users/Lenovo/OneDrive/Desktop/DBMS_MicroProject/run_web.bat) in the project folder.
- Or run in terminal:
  ```bash
  python server.py
  ```
The script starts the Flask server and opens the dashboard directly in your default browser.

---

## 2. Deploying Online for Free (Live URL Anywhere)

To share a live URL with your faculty or classmates, you need two free services:
1. **Free Cloud PostgreSQL Database** (to store data online 24/7)
2. **Free Web App Host** (to run the Flask web dashboard online)

---

### Phase A: Setup Free Cloud PostgreSQL (Takes ~2 Minutes)

We recommend **[Neon.tech](https://neon.tech)** (free tier, no credit card required) or **[Supabase](https://supabase.com)**:

1. Go to **[https://neon.tech](https://neon.tech)** and click **Sign Up**.
2. Click **Create Project** (Name: `internal-marks-db`).
3. Neon will display your **Connection String**:
   ```
   postgresql://username:password@ep-cool-sample.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. Copy the connection details:
   - **Host:** `ep-cool-sample.us-east-2.aws.neon.tech`
   - **Database:** `neondb`
   - **User:** `username`
   - **Password:** `password`
   - **Port:** `5432`
5. Open the **SQL Editor** tab in Neon and paste the contents of:
   - [`database/schema.sql`](file:///c:/Users/Lenovo/OneDrive/Desktop/DBMS_MicroProject/database/schema.sql) (Click **Run** to create tables and triggers)
   - [`database/sample_data.sql`](file:///c:/Users/Lenovo/OneDrive/Desktop/DBMS_MicroProject/database/sample_data.sql) (Click **Run** to load initial sample data)

---

### Phase B: Deploy Web Dashboard on Render.com (Takes ~3 Minutes)

**Render** gives you a free HTTPS URL (e.g. `https://marks-management-system.onrender.com`):

1. **Push your code to GitHub:**
   - Initialize git in your project folder (if not done):
     ```bash
     git init
     git add .
     git commit -m "Internal Marks Management System Web App"
     ```
   - Push to your GitHub account repository.

2. **Create a Free Web Service on Render:**
   - Go to **[https://render.com](https://render.com)** and sign in with GitHub.
   - Click **New +** → **Web Service**.
   - Select your GitHub repository.
   - Configure the service settings:
     - **Name:** `marks-management-system`
     - **Environment:** `Python 3`
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `python server.py`
     - **Instance Type:** `Free`

3. **Set Environment Variables on Render:**
   Under **Environment Variables**, add the keys corresponding to your cloud PostgreSQL database:
   - `DB_HOST`: `[your-cloud-db-host]`
   - `DB_PORT`: `5432`
   - `DB_NAME`: `neondb`
   - `DB_USER`: `[your-cloud-db-user]`
   - `DB_PASSWORD`: `[your-cloud-db-password]`
   - `PORT`: `10000`

4. Click **Deploy Web Service**!
   Render will build the project and assign a public URL:
   `https://marks-management-system.onrender.com`

---

## 3. Alternative: Deploying to Railway.app

1. Go to **[https://railway.app](https://railway.app)** and log in with GitHub.
2. Click **New Project** → **Deploy from GitHub Repo**.
3. Select your repository.
4. Add the PostgreSQL environment variables in Railway's **Variables** tab.
5. Railway automatically reads [`Procfile`](file:///c:/Users/Lenovo/OneDrive/Desktop/DBMS_MicroProject/Procfile) and generates a public domain.

---

## 4. Key Web Dashboard Features to Highlight in Faculty Viva

1. **Dashboard Tab:** 6 Animated KPI cards + live marks ledger stream.
2. **Student Management Tab:** Real-time form with `SERIAL` auto-increment ID generation and `UNIQUE(class_name, division, roll_no)` constraint protection.
3. **Marks Allocation Tab:** Dynamic subject dropdown displaying live max marks limit, preventing scores exceeding subject maximums via PL/pgSQL triggers.
4. **Marksheet & Results Tab:** Print-ready academic marksheet generator with percentage progress bars, GPA categories, and distinction badges.
5. **Interactive SQL Console Tab:** Pre-configured viva queries and a live SQL editor for faculty-directed ad-hoc queries.
6. **DBMS & Viva Guide Tab:** 3NF normalization proof and trigger code breakdowns.
