# 🚀 Deployment Guide - Crop Portal

This guide will help you deploy your Crop Portal online for **FREE** so everyone can access it!

## 📋 What You'll Deploy

- **Frontend** (HTML/CSS/JS) → Netlify (Free)
- **Backend** (Flask API) → Render (Free)

---

## 🔧 Step 1: Deploy Backend (Render.com)

### 1.1 Create Render Account
1. Go to [render.com](https://render.com)
2. Click **"Get Started"** and sign up (use GitHub for easier deployment)

### 1.2 Deploy Backend
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository OR choose **"Public Git repository"**
3. If using public repo, paste: `your-github-repo-url`
4. Fill in these details:
   - **Name**: `crop-portal-backend`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: `Backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app_production:app`

5. **Environment Variables** (Click "Add Environment Variable"):
   ```
   FLASK_ENV = production
   SECRET_KEY = (click "Generate" button)
   JWT_SECRET = (click "Generate" button)
   FRONTEND_URL = https://your-app.netlify.app (add later)
   ```

6. Click **"Create Web Service"**
7. Wait 2-3 minutes for deployment
8. **Copy your backend URL**: `https://crop-portal-backend-xxxx.onrender.com`

---

## 🎨 Step 2: Update Frontend Config

### 2.1 Update API URL
Open `Frontend/config.js` and update line 7:

```javascript
API_URL_PROD: 'https://crop-portal-backend-xxxx.onrender.com',
```
Replace with YOUR actual Render backend URL!

### 2.2 Add Config Script to HTML Files

Add this line to ALL HTML files (index.html, analysis.html, advisories.html, etc.) 
**BEFORE** the `<script src="script.js"></script>` line:

```html
<script src="config.js"></script>
<script src="script.js"></script>
```

### 2.3 Update script.js API Calls

In `script.js`, find all `fetch()` calls and update them to use:
```javascript
const API_URL = window.API_CONFIG.API_URL;

// Example:
fetch(`${API_URL}/api/detect`, {
    method: 'POST',
    body: formData
})
```

---

## 🌐 Step 3: Deploy Frontend (Netlify)

### 3.1 Create Netlify Account
1. Go to [netlify.com](https://netlify.com)
2. Click **"Sign Up"** (use GitHub for easier deployment)

### 3.2 Deploy Frontend

**Option A: Drag & Drop (Easiest)**
1. Click **"Sites"** → **"Add new site"** → **"Deploy manually"**
2. Drag your entire **Frontend** folder into the upload box
3. Wait 30 seconds for deployment
4. **Copy your frontend URL**: `https://your-app-name.netlify.app`

**Option B: GitHub (Automatic Updates)**
1. Push your code to GitHub
2. In Netlify: **"Add new site"** → **"Import from Git"**
3. Choose your repository
4. Set **Base directory**: `Frontend`
5. Click **"Deploy site"**

### 3.3 Update Backend CORS
1. Go back to Render.com
2. Open your backend service
3. Go to **"Environment"** tab
4. Update `FRONTEND_URL` to your Netlify URL: `https://your-app-name.netlify.app`
5. Click **"Save Changes"** (backend will redeploy automatically)

---

## ✅ Step 4: Test Your Live App!

1. Visit your Netlify URL: `https://your-app-name.netlify.app`
2. Test image upload on the Detection page
3. Check if Advisories load from crops.json
4. Share the link with friends! 🎉

---

## 🔐 Important Notes

### Free Tier Limitations
- **Render Free Tier**: 
  - App sleeps after 15 minutes of inactivity
  - First request after sleep takes ~30 seconds to wake up
  - 750 hours/month free
  
- **Netlify Free Tier**: 
  - 100GB bandwidth/month
  - Unlimited sites
  - Always on (no sleep)

### Custom Domain (Optional)
- Buy domain from Namecheap, GoDaddy, etc. (~$10/year)
- In Netlify: **Domain Settings** → **Add custom domain**
- In Render: **Settings** → **Custom Domain**

---

## 🐛 Troubleshooting

### Backend Issues
- Check logs: Render Dashboard → Your Service → **"Logs"** tab
- Verify all environment variables are set
- Make sure `gunicorn` is in requirements.txt

### Frontend Issues
- Open browser console (F12) to see errors
- Verify API_URL_PROD is correct in config.js
- Check CORS errors (update FRONTEND_URL in Render)

### Database Not Persisting
- Render free tier doesn't persist files on disk
- Upgrade to paid tier ($7/month) for persistent storage
- Or use external database (PostgreSQL on Render free tier)

---

## 📚 Alternative Deployment Options

### Other Backend Hosts (Free)
- **Railway.app** - 500 hours/month free
- **PythonAnywhere** - Always on, limited
- **Fly.io** - 3 VMs free

### Other Frontend Hosts (Free)
- **Vercel** - Similar to Netlify
- **GitHub Pages** - For static sites only
- **Cloudflare Pages** - Fast CDN

---

## 🎯 Next Steps After Deployment

1. ✅ Add real AI model (TensorFlow/PyTorch)
2. ✅ Implement password hashing
3. ✅ Add PostgreSQL database (Render free tier)
4. ✅ Set up email notifications
5. ✅ Add analytics (Google Analytics)
6. ✅ Custom domain name

---

## 📞 Need Help?

If you get stuck:
1. Check Render/Netlify logs first
2. Google the error message
3. Check Stack Overflow
4. Ask on Reddit r/webdev or r/flask

---

**Your URLs After Deployment:**
- Frontend: `https://your-app-name.netlify.app`
- Backend: `https://crop-portal-backend-xxxx.onrender.com`
- API Health: `https://crop-portal-backend-xxxx.onrender.com/api/health`

🎉 **Congratulations!** Your app is now live and accessible worldwide!
