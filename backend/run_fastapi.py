import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.fastapi_app:app", host="0.0.0.0", port=8000, reload=False)
