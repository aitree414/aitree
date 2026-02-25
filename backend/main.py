from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as main_router
from api.ma_routes import router as ma_router
from api.screener_routes import router as screener_router

app = FastAPI(
    title="BackTester API",
    description="Investment backtesting API supporting lump sum, DCA, and MA strategies",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router, prefix="/api")
app.include_router(ma_router, prefix="/api")
app.include_router(screener_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "BackTester API", "docs": "/docs"}
