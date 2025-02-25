import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from apify_client import ApifyClient

# Import the nightclub CMS generator function
from generate_cms import generate_nightclub_page

# Initialize FastAPI and templates.
# (If you still want to serve static files from a folder named "nightclub", mount that folder.)
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
load_dotenv()

# Apify configuration: set your APIFY_TOKEN in the .env file.
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "your_apify_token")
print("APIFY_TOKEN:", APIFY_TOKEN)

# Create an ApifyClient instance.
client = ApifyClient(APIFY_TOKEN)

def run_instagram_scraper_sync(instagram_url: str, results_limit: int = 12) -> dict:
    run_input = {
        "directUrls": [instagram_url],
        "resultsType": "posts",
        "resultsLimit": results_limit,
        "scrapeComments": False,
    }
    run = client.actor("apify/instagram-scraper").call(run_input=run_input)
    return run

def get_dataset_items(default_dataset_id: str) -> list:
    dataset = client.dataset(default_dataset_id)
    items_response = dataset.list_items(limit=10000)
    return items_response.items

# Main function to run the scraping and write the JSON file in the nightclub folder.
async def run_apify_and_write_to_file(instagram_url: str, results_limit: int = 12) -> str:
    # Run the actor call in a separate thread.
    run = await asyncio.to_thread(run_instagram_scraper_sync, instagram_url, results_limit)
    print("DEBUG: run data type:", type(run))
    print("DEBUG: run data content:", run)
    
    # Extract the dataset ID from the run output.
    default_dataset_id = run.get("defaultDatasetId")
    if not default_dataset_id:
        raise HTTPException(status_code=500, detail="No dataset ID returned from Apify run")
    
    # Retrieve the dataset items in a thread.
    items = await asyncio.to_thread(get_dataset_items, default_dataset_id)
    print("DEBUG: Retrieved", len(items), "items.")
    
    # Save JSON output in the "nightclub" folder.
    filename = f"scraped_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    output_dir = "static"  # use this folder for output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(items, f)
        print("File written successfully to:", filepath)
    except Exception as e:
        print("Error writing file:", e)
        raise HTTPException(status_code=500, detail=f"Failed to write data file: {e}")
    return filename

@app.get("/health", response_class=PlainTextResponse)
async def health(request: Request):
    return PlainTextResponse("OK")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("first_dashboard.html", {"request": request, "download_link": None})

@app.post("/scrape", response_class=HTMLResponse)
async def scrape(request: Request, instagram_url: str = Form(...)):
    try:
        filename = await run_apify_and_write_to_file(instagram_url, results_limit=12)
    except Exception as e:
        print("Error during scraping and file writing:", e)
        raise HTTPException(status_code=500, detail=f"Scraping error: {e}")
    
    # Path to the JSON file in the nightclub folder.
    json_file = os.path.join("static", filename)
    # Generate a CMS HTML file also in the nightclub folder.
    cms_output = os.path.join("static", f"cms_{datetime.now().strftime('%Y%m%d%H%M%S')}.html")
    
    # Get the GCS bucket name from the environment.
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    if not bucket_name:
        raise HTTPException(status_code=500, detail="GCS_BUCKET_NAME not set in environment")
    
    # Call the nightclub CMS generator.
    await asyncio.to_thread(generate_nightclub_page, json_file, cms_output, bucket_name)
    
    file_size = os.path.getsize(json_file)
    print(f"File {filename} size: {file_size} bytes")
    
    # Return a response with a link to the generated CMS page.
    return templates.TemplateResponse("first_dashboard.html", {
        "request": request,
        "download_link": f"/static/{os.path.basename(cms_output)}",
        "total_items": file_size
    })

@app.post("/scrape-text", response_class=PlainTextResponse)
async def scrape_text(instagram_url: str = Form(...)):
    try:
        filename = await run_apify_and_write_to_file(instagram_url, results_limit=12)
    except Exception as e:
        return PlainTextResponse(f"Error: {e}", status_code=500)
    return PlainTextResponse(f"File created: /static/{filename}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
