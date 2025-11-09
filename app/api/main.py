from fastapi import FastAPI

app = FastAPI(title="Green Cloud Repository Scanner")

@app.get("/")
async def root():
    return {"message": "Green Cloud Repository Scanner"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/version")
async def version():
    return {"version": "0.1.0"}
