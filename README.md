# Mongotel Scraper API

This is a FastAPI-based service to scrape call history from Mongotel and upload recordings to Cloudinary.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    The project uses a `.env` file for configuration. This has been created for you with default values.
    ensure you have the following variables in `.env`:
    ```env
    MONGOTEL_USERNAME=...
    MONGOTEL_PASSWORD=...
    CLOUDINARY_CLOUD_NAME=...
    CLOUDINARY_API_KEY=...
    CLOUDINARY_API_SECRET=...
    ```

## Running the API

Start the server using Uvicorn:

```bash
python -m uvicorn main:app --reload
```

## API Endpoints

-   **Health Check**: `GET /`
    -   Returns status of the API.
    -   Example: `{"status": "ok", "service": "mongotel_scraper"}`

-   **Run Scraper**: `GET /call_history`
    -   Triggers the scraping process.
    -   Returns: JSON object with call history and audio links.

## Docker (Optional)

You can check `Dockerfile` if you wish to deploy via Docker.
