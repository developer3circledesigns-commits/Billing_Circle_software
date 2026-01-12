# 🚀 Full Step-by-Step Deployment Guide: Billing Software (100% Free)

This guide provides the complete process to deploy your Billing Software for free using **MongoDB Atlas** and **Render**.

## 📋 Prerequisites
1. **GitHub Account**: To host your code.
2. **Render Account**: To host the web application. [Sign up here](https://render.com/).
3. **MongoDB Atlas Account**: To host your database. [Sign up here](https://www.mongodb.com/cloud/atlas).

---

## 🛠️ Step 1: Push Code to GitHub
1. Create a new **Private** repository on GitHub.
2. Open your terminal in the project folder and run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

---

## 🍃 Step 2: Setup MongoDB Atlas (Free Database)
1. **Create Cluster**: Log in, click **"Create"**, and select the **M0 Free** tier. Pick a region near you (e.g., AWS N. Virginia).
2. **Set Credentials**:
   - Go to **Database Access** > **Add New Database User**.
   - Create a user (e.g., `admin`) and a password. **Remember these.**
3. **Network Access**:
   - Go to **Network Access** > **Add IP Address**.
   - Click **"Allow Access from Anywhere"** (0.0.0.0/0). *Note: This is required for Render free tier.*
4. **Get Connection String**:
   - Go to **Database** > **Connect** > **Drivers**.
   - Copy the string. It looks like:
     `mongodb+srv://admin:<password>@cluster0.abc.mongodb.net/?retryWrites=true&w=majority`
   - Replace `<password>` with your actual password.

---

## ⚙️ Step 3: Deploy Backend on Render (FastAPI)
1. Log in to Render and click **New +** > **Web Service**.
2. Connect your GitHub repository.
3. **Configuration**:
   - **Name**: `billing-api`
   - **Runtime**: `Python 3`
   - **Root Directory**: `.`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.backend.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Free**
4. **Environment Variables**: Click **Advanced** > **Add Environment Variable**:
   - `MONGO_URI`: (Your string from Step 2)
   - `DATABASE_NAME`: `billing_db`
   - `SECRET_KEY`: (Any random long string)
   - `ALGORITHM`: `HS256`
5. Click **Create Web Service**. 
6. **Wait**: Once it says "Live", copy your Backend URL (e.g., `https://billing-api.onrender.com`).

---

## 🖥️ Step 4: Deploy Frontend on Render (Flask)
1. Go back to Render Dashboard > **New +** > **Web Service**.
2. Connect the **same** GitHub repository.
3. **Configuration**:
   - **Name**: `billing-frontend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`
   - **Instance Type**: **Free**
4. **Environment Variables**:
   - `APP_API_URL`: `https://billing-api.onrender.com/api/v1` (Use your actual URL from Step 3 + `/api/v1`)
   - `SECRET_KEY`: (Same random string you used for backend)
5. Click **Create Web Service**.

---

## ✅ Step 5: Final Check
1. Open your Frontend URL (e.g., `https://billing-frontend.onrender.com`).
2. **Note on Free Tier**: Render's free tier "sleeps" after 15 minutes of inactivity. When you first open the site, it may take **30-60 seconds** to wake up. This is normal for free hosting.

---

## 💡 Troubleshooting
* **Backend Timeout**: If the backend takes too long to start, Render might fail. Ensure your `requirements.txt` is updated.
* **Database Connection**: If you get a "Connection Error", double-check that you added `0.0.0.0/0` in MongoDB Network Access.
* **Mix Content Error**: Always use `https://` for the `APP_API_URL`.
