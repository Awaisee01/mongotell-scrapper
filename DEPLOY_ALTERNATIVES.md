# Deployment Alternatives

Agar Render pasand nahi hai, toh yeh 2 best alternatives hain:

## Option 1: Railway (Best Performance & Ease)
Railway bohat fast aur stable hai, lekin iska "Trial" hota hai ($5 credit). Baad mein pay karna pad sakta hai, par setup bohat easy hai.

1.  **Railway.app** par account banayein (GitHub se).
2.  "New Project" > "Deploy from GitHub repo" select karein.
3.  Apna repo select karein.
4.  **Variables** tab mein jayein aur apni `.env` wali values add karein (`MONGOTEL_USERNAME`, etc.).
5.  Railway automatically `Dockerfile` detect karke deploy kar dega.

## Option 2: Hugging Face Spaces (Completely Free & Good for Scrapers)
Hugging Face mostly AI ke liye hai, par woh **Docker Spaces** free mein host karte hain. Yeh scrapers ke liye bohat acha hai.

1.  [Hugging Face](https://huggingface.co/) par account banayein.
2.  **New Space** click karein.
3.  **Space Name**: `mongotel-api` (kuch bhi).
4.  **License**: `mit`.
5.  **SDK**: Select **Docker**. (Blank Docker template).
6.  **Create Space** par click karein.
7.  **Files Upload Karein**:
    *   Hugging Face aapko ek Git repo dega.
    *   Apna code wahan push karein (ya website se manually files upload kar dein: `Dockerfile`, `requirements.txt`, python files).
8.  **Settings** > **Variables** mein jayein aur apne secrets add karein.

## Option 3: Fly.io (Good Free Tier)
Fly.io thoda technical hai (CLI tool install karna padta hai), par free tier acha hai.

1.  `flyctl` install karein.
2.  `fly launch` command run karein project folder mein.
3.  Yeh automatically Dockerfile detect karega aur deploy kar dega.
