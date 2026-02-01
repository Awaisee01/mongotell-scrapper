# Deploying to Render.com (Free & GitHub Integrated)

Render is a great choice because it allows you to deploy **Docker** containers directly from GitHub for free.

## Prerequisites
1.  Push your code to a **GitHub Repository**.
2.  Sign up for an account on [Render.com](https://render.com).

## Step-by-Step Deployment

1.  **New Web Service**:
    -   Go to your Render Dashboard.
    -   Click **"New +"** and select **"Web Service"**.

2.  **Connect GitHub**:
    -   Select "Build and deploy from a Git repository".
    -   Connect your GitHub account and select your `mongotel_scraper` repository.

3.  **Configure Service**:
    -   **Name**: Give it a name (e.g., `mongotel-api`).
    -   **Region**: Choose the one closest to you (e.g., Singapore, Frankfurt).
    -   **Branch**: `main` (or master).
    -   **Runtime**: Select **Docker**. (This is critical!).

4.  **Environment Variables (CRITICAL)**:
    -   Scroll down to "Environment Variables".
    -   Add the following keys and values (copy them from your `.env` file):

    | Key | Value |
    | --- | --- |
    | `MONGOTEL_USERNAME` | *Your Username* |
    | `MONGOTEL_PASSWORD` | *Your Password* |
    | `CLOUDINARY_CLOUD_NAME` | *Your Cloud Name* |
    | `CLOUDINARY_API_KEY` | *Your API Key* |
    | `CLOUDINARY_API_SECRET` | *Your API Secret* |
    | `LOCAL_DEV` | `False` |

5.  **Deploy**:
    -   Select the **Free** instance type.
    -   Click **"Create Web Service"**.

## Using Your Live API

Once deployed, Render will give you a URL like:
`https://mongotel-api.onrender.com`

### Update Frontend
Open your `index.html` file and change the fetch URL:

```javascript
// Old
const response = await fetch('http://127.0.0.1:8000/call_history');

// New (Example)
const response = await fetch('https://mongotel-api.onrender.com/call_history');
```

Now you can upload `index.html` to Vercel or Netlify, and it will talk to your Render backend!
