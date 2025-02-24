from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()

@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    """
    Returns a simple Privacy Policy page.
    Replace the placeholder text below with your actual privacy policy.
    """
    html_content = """
    <html>
        <head>
            <title>Privacy Policy</title>
        </head>
        <body>
            <h1>Privacy Policy</h1>
            <p>
                This Privacy Policy explains how our application collects, uses, and protects your data.
                We respect your privacy and are committed to protecting your personal information.
            </p>
            <p>
                For further details or any questions, please contact us at support@example.com.
            </p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/data-deletion", response_class=JSONResponse)
async def data_deletion(request: Request):
    """
    Provides a JSON response conforming to Facebook's requirements for a Data Deletion Callback URL.
    In a production scenario, you would also implement the logic to identify the user and delete their data.
    """
    # The 'url' field can point to a page where users can check the status of their deletion request.
    response_data = {
        "url": "http://localhost:8000/data-deletion-status",
        "confirmation_code": "abc123def456"  # Generate a unique confirmation code as needed.
    }
    return JSONResponse(content=response_data)

@app.get("/data-deletion-status", response_class=HTMLResponse)
async def data_deletion_status(request: Request):
    """
    An optional status page where a user can verify that their data deletion request has been processed.
    Replace this with your actual status or deletion confirmation details.
    """
    html_content = """
    <html>
        <head>
            <title>Data Deletion Status</title>
        </head>
        <body>
            <h1>Data Deletion Request Received</h1>
            <p>
                Your data deletion request is being processed.
                If you have any questions, please contact support@example.com.
            </p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# You can run your app with: uvicorn your_filename:app --reload
