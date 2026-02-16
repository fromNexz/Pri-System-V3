from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from routers import appointments, customers, settings, chatbot

app = FastAPI(title="PriSystem API")

origins = [
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appointments.router)
app.include_router(customers.router)
app.include_router(settings.router)
app.include_router(chatbot.router)


@app.get("/api-status")
def root():
    return {"message": "PriSystem API online"}


@app.get("/painel")
def painel_index():
    return FileResponse("painel/index.html")


@app.get("/painel/clientes")
def painel_clientes():
    return FileResponse("painel/clientes.html")


@app.get("/painel/settings")
def painel_settings():
    return FileResponse("painel/settings.html")
