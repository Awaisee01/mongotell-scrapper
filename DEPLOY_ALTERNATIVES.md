# Deployment Alternatives for Mongotel Scraper

Since this application uses **Selenium (Headless Chrome)**, it requires a hosting provider that supports Docker and has enough memory/CPU. Standard "Python Hosting" (like Vercel functions) will likely fail.

Here are the best alternatives to Render:

## 1. Railway.app (Easiest)
Railway is very similar to Render but often has better performance stability.
-   **Pros**: Zero config (detected Dockerfile automatically), very fast builds.
-   **Cons**: No perpetual free tier (Trial then Pay-as-you-go).
-   **How to Deploy**:
    1.  Login to [Railway.app](https://railway.app).
    2.  Click "New Project" -> "Deploy from GitHub repo".
    3.  Select `mongotel_scraper`.
    4.  Add your Environment Variables (`MONGOTEL_USERNAME`, etc.).
    5.  Railway will automatically build using your `Dockerfile`.

## 2. Fly.io (Good Free Tier)
Fly.io runs Docker containers near you. It has a generous free tier (3 VMs).
-   **Pros**: Good free usage, runs as a real VM (no weird sleeps if configured right).
-   **Cons**: Requires installing a CLI tool (`flyctl`).
-   **How to Deploy**:
    1.  Install flyctl: `iwr https://fly.io/install.ps1 -useb | iex` (PowerShell).
    2.  Login: `fly auth login`.
    3.  Launch: `fly launch` (detects Dockerfile).
    4.  **Important**: Set internal port to 8000 when asked.

## 3. VPS (DigitalOcean / Hetzner) - **RECOMMENDED FOR SCRAPING**
For scrapers, a cheap Virtual Private Server (VPS) is often the best choice because you have **full control** and **no timeout limits**.
-   **Cost**: ~$4-6/month.
-   **Pros**: usage is unlimited (scrapers can run 24/7), no "spin down", no 50s wake-up time.
-   **Cons**: You need to run commands to set it up.

### Quick VPS Setup (Ubuntu):
1.  **Get a Droplet/Server** (Ubuntu 22.04 or 24.04).
2.  SSH into it: `ssh root@your-ip`.
3.  **Install Docker**:
    ```bash
    apt update
    apt install -y docker.io
    ```
4.  **Run your Container**:
    ```bash
    # Run in background (-d), restart always
    docker run -d \
      --name scraper \
      -p 80:8000 \
      -e MONGOTEL_USERNAME="your-user" \
      -e MONGOTEL_PASSWORD="your-pass" \
      -e CLOUDINARY_CLOUD_NAME="..." \
      -e CLOUDINARY_API_KEY="..." \
      -e CLOUDINARY_API_SECRET="..." \
      --shm-size=2g \
      ghcr.io/awaisee01/mongotell-scrapper:latest
    ```
    *(Note: You'll need to build/push your image to a registry like GitHub Packages or DockerHub first, or just `git clone` and `docker build` directly on the VPS).*
