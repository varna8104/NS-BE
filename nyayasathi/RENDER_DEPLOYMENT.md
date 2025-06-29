# Render Deployment Guide for NS-BE (College Project - SQLite)

This guide will help you deploy the NS-BE Django backend to Render using SQLite (perfect for college projects).

## Prerequisites

1. A GitHub account with the NS-BE repository
2. A Render account (free tier available)
3. API keys for Groq and Hugging Face

## Step 1: Create a Web Service (No Database Setup Required!)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository: `varna8104/NS-BE`
4. Configure the service:

### Basic Settings
- **Name**: `ns-be` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `main`

### Build & Deploy Settings
- **Root Directory**: `nyayasathi`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn nyayasathi.wsgi:application`

### Advanced Settings
- **Auto-Deploy**: Yes
- **Health Check Path**: `/api/` (optional)

## Step 2: Configure Environment Variables

In your web service settings, add these environment variables:

### Required Variables
- **SECRET_KEY**: Generate a secure Django secret key
- **DEBUG**: `False`
- **GROQ_API_KEY**: Your Groq API key
- **HUGGINGFACE_API_KEY**: Your Hugging Face API key

### Optional Variables
- **CORS_ALLOWED_ORIGINS**: Your frontend domain (e.g., `https://ns-fe.vercel.app`)

### How to add environment variables:

1. Go to your web service dashboard
2. Click "Environment" tab
3. Add each variable:
   - **Key**: Variable name
   - **Value**: Variable value
   - **Environment**: Production

## Step 3: Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Run the build script
   - Start the application

## Step 4: Verify Deployment

1. Check the deployment logs for any errors
2. Visit your service URL (e.g., `https://ns-be.onrender.com`)
3. Test the API endpoints:
   - `GET /api/` - Should return API information
   - `POST /api/register/` - Test user registration

## Build Script Details

The `build.sh` script performs these steps:

```bash
#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate
```

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DEBUG` | Debug mode | `False` |
| `GROQ_API_KEY` | Groq API key | `gsk_...` |
| `HUGGINGFACE_API_KEY` | Hugging Face API key | `hf_...` |

### Optional Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CORS_ALLOWED_ORIGINS` | Frontend domains | `https://ns-fe.vercel.app` |

## Important Notes for SQLite Deployment

### Advantages for College Projects:
- ✅ **No database setup required**
- ✅ **Faster deployment**
- ✅ **No additional costs**
- ✅ **Perfect for demonstrations**

### Limitations:
- ⚠️ **Data resets on service restart** (Render's ephemeral file system)
- ⚠️ **No concurrent database access**
- ⚠️ **Not suitable for high traffic**

### For College Project Demo:
- The database will be recreated each time the service restarts
- Perfect for showing functionality without persistent data
- You can always migrate to PostgreSQL later if needed

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check build logs in Render dashboard
   - Verify `build.sh` has execute permissions
   - Ensure all dependencies are in `requirements.txt`

2. **Environment Variable Issues**
   - Verify all required variables are set
   - Check variable names match exactly
   - Ensure no extra spaces in values

3. **Static Files Issues**
   - Check if `STATIC_ROOT` is properly configured
   - Verify `collectstatic` command runs successfully

### Debugging Steps

1. **Check Build Logs**
   - Go to your service dashboard
   - Click on the latest deployment
   - Review build and deploy logs

2. **Check Application Logs**
   - Go to "Logs" tab in your service dashboard
   - Look for error messages
   - Check for missing environment variables

## Performance Optimization

### Application Optimization
- Enable caching
- Optimize static file serving
- Use CDN for static files

## Monitoring

- **Logs**: Available in Render dashboard
- **Metrics**: Basic metrics provided by Render
- **Health Checks**: Configure health check endpoints

## Scaling

- **Free Tier**: Limited to 750 hours/month
- **Paid Plans**: Available for higher usage
- **Auto-scaling**: Available on paid plans

## Support

- [Render Documentation](https://render.com/docs)
- [Django Deployment Guide](https://docs.djangoproject.com/en/5.2/howto/deployment/)
- [Render Support](https://render.com/support) 