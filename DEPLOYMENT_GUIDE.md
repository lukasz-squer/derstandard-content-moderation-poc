# 🚀 Streamlit Cloud Deployment Guide

This guide will help you deploy your DER STANDARD AI Moderation Demo to Streamlit Cloud.

## 📋 Pre-requisites

1. **GitHub Account**: You need a GitHub account to host your repository
2. **Groq API Key**: Get a free API key from [Groq Console](https://console.groq.com/keys)
3. **Streamlit Community Cloud Account**: Sign up at [share.streamlit.io](https://share.streamlit.io/)

## 🔧 Step 1: Prepare Your Repository

### 1.1 Push to GitHub

If you haven't already, push your code to a GitHub repository:

```bash
# If this is a new repository
git init
git add .
git commit -m "Initial commit: DER STANDARD AI Moderation Demo"
git branch -M main
git remote add origin https://github.com/yourusername/derstandard-demo.git
git push -u origin main

# If you already have a repository
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push
```

### 1.2 Verify Repository Structure

Your repository should have this structure:
```
derstandard-demo/
├── derstandard-demo-app.py      # Main application
├── requirements.txt             # Dependencies
├── .streamlit/
│   ├── config.toml             # Streamlit configuration
│   └── secrets.toml.template   # Template for secrets
├── .gitignore                  # Git ignore file
├── API_KEY_SETUP.md           # API key setup guide
└── DEPLOYMENT_GUIDE.md        # This file
```

## 🌐 Step 2: Deploy to Streamlit Cloud

### 2.1 Create Streamlit Cloud Account

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Sign in with your GitHub account
3. Authorize Streamlit to access your repositories

### 2.2 Deploy Your App

1. **Click "Create app"** in Streamlit Cloud
2. **Fill in the deployment form**:
   - **Repository**: `yourusername/derstandard-demo`
   - **Branch**: `main`
   - **Main file path**: `derstandard-demo-app.py`
   - **App URL**: Choose a custom subdomain (e.g., `derstandard-ai-demo`)

3. **Configure Secrets** (IMPORTANT):
   - Click on "Advanced settings"
   - In the "Secrets" section, add:
   ```toml
   GROQ_API_KEY = "your_actual_groq_api_key_here"
   ```
   - Replace `your_actual_groq_api_key_here` with your real Groq API key

4. **Click "Deploy!"**

## ⚙️ Step 3: Configure Secrets (Alternative Method)

If you missed adding secrets during deployment:

1. Go to your app's dashboard in Streamlit Cloud
2. Click on "Manage app" → "Settings"
3. Go to the "Secrets" tab
4. Add your secrets in TOML format:
```toml
GROQ_API_KEY = "your_actual_groq_api_key_here"
```
5. Click "Save"

## 🔍 Step 4: Verify Deployment

### 4.1 Check App Status

1. Your app will be available at: `https://your-app-name.streamlit.app/`
2. The deployment process usually takes 2-5 minutes
3. Check the deployment logs if there are any issues

### 4.2 Test Functionality

1. **API Key**: Verify that the API key loads automatically (you should see "✅ API Key aus Streamlit Secrets geladen")
2. **Article Loading**: Test loading a DER STANDARD article
3. **AI Analysis**: Test the posting analysis functionality

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. **ModuleNotFoundError**
- **Problem**: Missing dependencies
- **Solution**: Check `requirements.txt` and ensure all packages are listed

#### 2. **API Key Not Found**
- **Problem**: Secrets not properly configured
- **Solution**: Double-check secrets configuration in Streamlit Cloud dashboard

#### 3. **App Won't Start**
- **Problem**: Code errors or configuration issues
- **Solution**: Check the deployment logs in Streamlit Cloud

#### 4. **Slow Performance**
- **Problem**: Cold starts or resource limitations
- **Solution**: This is normal for free Streamlit Cloud apps

### Debugging Steps

1. **Check Logs**: View deployment logs in Streamlit Cloud dashboard
2. **Test Locally**: Ensure app works locally before deploying
3. **Verify Dependencies**: Make sure all required packages are in `requirements.txt`
4. **Check Secrets**: Verify API key is correctly set in secrets

## 🔄 Step 5: Updates and Maintenance

### Updating Your App

1. Make changes to your code locally
2. Commit and push to GitHub:
```bash
git add .
git commit -m "Update: description of changes"
git push
```
3. Streamlit Cloud will automatically redeploy your app

### Managing Secrets

- **Update API Key**: Go to app settings → Secrets tab in Streamlit Cloud
- **Add New Secrets**: Add them in TOML format in the secrets section

## 📱 Step 6: Sharing Your App

Once deployed, you can share your app by:

1. **Public URL**: Share the `https://your-app-name.streamlit.app/` link
2. **Embedding**: Use the embed code provided by Streamlit
3. **Social Media**: Share directly from the Streamlit Cloud dashboard

## 🔒 Security Best Practices

1. **Never commit secrets**: Always use `.gitignore` for sensitive files
2. **Use environment variables**: Keep API keys in Streamlit secrets
3. **Monitor usage**: Keep track of API usage and costs
4. **Regular updates**: Keep dependencies updated

## 📞 Support and Resources

- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io/)
- **Community Forum**: [discuss.streamlit.io](https://discuss.streamlit.io/)
- **Groq Documentation**: [console.groq.com/docs](https://console.groq.com/docs)

## ✅ Deployment Checklist

- [ ] Repository pushed to GitHub
- [ ] `requirements.txt` includes all dependencies
- [ ] `.gitignore` excludes sensitive files
- [ ] Streamlit Cloud account created
- [ ] App deployed with correct settings
- [ ] Secrets (API key) configured
- [ ] App functionality tested
- [ ] Public URL shared

---

🎉 **Congratulations!** Your DER STANDARD AI Moderation Demo is now live on Streamlit Cloud!
