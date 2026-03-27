from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from edge_finder import get_plays

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/plays")
def get_bets():
    return get_plays()
