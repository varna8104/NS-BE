# Render Deployment Guide for NS-BE

This guide will help you deploy the NS-BE Django backend to Render.

## Prerequisites

1. A GitHub account with the NS-BE repository
2. A Render account (free tier available)
3. API keys for Groq and Hugging Face

## Step 1: Create a PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "PostgreSQL"
3. Configure the database:
   - **Name**: `ns-be-db` (or your preferred name)
   - **Database**: `nyayasathi`
   - **User**: `nyayasathi_user`
   - **Region**: Choose closest to your users
4. Click "Create Database"
5. **Save the connection details** - you'll need them later

## Step 2: Create a Web Service

1. In Render Dashboard, click "New" → "Web Service"
2. Connect your GitHub repository: `varna8104/NS-BE`
3. Configure the service:

### Basic Settings
- **Name**: `ns-be` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Same as your database
- **Branch**: `main`

### Build & Deploy Settings
- **Root Directory**: `nyayasathi`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn nyayasathi.wsgi:application`

### Advanced Settings
- **Auto-Deploy**: Yes
- **Health Check Path**: `/api/` (optional)

## Step 3: Configure Environment Variables

In your web service settings, add these environment variables:

### Required Variables
- **SECRET_KEY**: Generate a secure Django secret key
- **DATABASE_URL**: Copy from your PostgreSQL service
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

## Step 4: Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Run the build script
   - Start the application

## Step 5: Verify Deployment

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
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:port/db` |
| `DEBUG` | Debug mode | `False` |
| `GROQ_API_KEY` | Groq API key | `gsk_...` |
| `HUGGINGFACE_API_KEY` | Hugging Face API key | `hf_...` |

### Optional Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CORS_ALLOWED_ORIGINS` | Frontend domains | `https://ns-fe.vercel.app` |

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check build logs in Render dashboard
   - Verify `build.sh` has execute permissions
   - Ensure all dependencies are in `requirements.txt`

2. **Database Connection Issues**
   - Verify `DATABASE_URL` is correct
   - Check if database is accessible from web service
   - Ensure database is in the same region

3. **Environment Variable Issues**
   - Verify all required variables are set
   - Check variable names match exactly
   - Ensure no extra spaces in values

4. **Static Files Issues**
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

3. **Test Locally**
   - Clone the repository locally
   - Set up environment variables
   - Run the application locally to test

## Performance Optimization

### Database Optimization
- Use connection pooling
- Optimize database queries
- Add database indexes

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