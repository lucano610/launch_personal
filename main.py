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

# Import the CMS generator function from generate_cms.py
from generate_cms import generate_cms_page

# Initialize FastAPI and templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
load_dotenv()

# Apify configuration: set your APIFY_TOKEN in the .env file
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "your_apify_token")
print("APIFY_TOKEN:", APIFY_TOKEN)

# Create an ApifyClient instance
client = ApifyClient(APIFY_TOKEN)

# Function to start the Instagram Scraper actor run using the ApifyClient.
def run_instagram_scraper_sync(instagram_url: str, results_limit: int = 100) -> dict:
    run_input = {
        "directUrls": [instagram_url],
        "resultsType": "posts",
        "resultsLimit": results_limit,
        "scrapeComments": False,  # adjust as needed
    }
    # Start the actor run synchronously
    run = client.actor("apify/instagram-scraper").call(run_input=run_input)
    return run

# Function to retrieve dataset items given a dataset ID.
def get_dataset_items(default_dataset_id: str) -> list:
    dataset = client.dataset(default_dataset_id)
    items_response = dataset.list_items(limit=10000)
    return items_response.items

# Main function: runs the entire process and writes output to a JSON file.
async def run_apify_and_write_to_file(instagram_url: str, results_limit: int = 100) -> str:
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
    
    # Write the items to a JSON file.
    filename = f"scraped_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    filepath = os.path.join("static", filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(items, f)
        print("File written successfully to:", filepath)
    except Exception as e:
        print("Error writing file:", e)
        raise HTTPException(status_code=500, detail=f"Failed to write data file: {e}")
    return filename

# Define FastAPI endpoints.
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("first_dashboard.html", {"request": request, "download_link": None})

@app.post("/scrape", response_class=HTMLResponse)
async def scrape(request: Request, instagram_url: str = Form(...)):
    try:
        filename = await run_apify_and_write_to_file(instagram_url, results_limit=100)
    except Exception as e:
        print("Error during scraping and file writing:", e)
        raise HTTPException(status_code=500, detail=f"Scraping error: {e}")
    
    # Determine the full path to the generated JSON file.
    json_file = os.path.join("static", filename)
    # Create an output filename for the CMS HTML page.
    cms_output = os.path.join("static", f"cms_{datetime.now().strftime('%Y%m%d%H%M%S')}.html")
    
    # Get the GCS bucket name from the environment.
    bucket_name = os.environ.get("GCS_BUCKET_NAME")
    if not bucket_name:
        raise HTTPException(status_code=500, detail="GCS_BUCKET_NAME not set in environment")
    
    # Call the CMS generator function in a separate thread.
    await asyncio.to_thread(generate_cms_page, json_file, cms_output, bucket_name)
    
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
        filename = await run_apify_and_write_to_file(instagram_url, results_limit=100)
    except Exception as e:
        return PlainTextResponse(f"Error: {e}", status_code=500)
    return PlainTextResponse(f"File created: /static/{filename}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
