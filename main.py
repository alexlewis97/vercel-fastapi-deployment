from time import time
from fastapi import FastAPI, __version__
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

html = f"""
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI on Vercel</title>
        <link rel="icon" href="/static/favicon.ico" type="image/x-icon" />
    </head>
    <body>
        <div class="bg-gray-200 p-4 rounded-lg shadow-lg">
            <h1>Hello from FastAPI@{__version__}</h1>
            <ul>
                <li><a href="/docs">/docs</a></li>
                <li><a href="/redoc">/redoc</a></li>
            </ul>
            <p>Powered by <a href="https://vercel.com" target="_blank">Vercel</a></p>
        </div>
    </body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(html)

@app.get('/ping')
async def hello():
    return {'res': 'pong', 'version': __version__, "time": time()}



from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_ai21 import ChatAI21
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAI
import os
import json
import re

llm_gemini = ChatGoogleGenerativeAI(model='gemini-2.0-flash-thinking-exp-01-21')

llm_ai21 = ChatAI21(model="jamba-1.5-large", temperature=0)

llm_claude = ChatAnthropic(model='claude-3-5-sonnet-20241022')

llm_openai = OpenAI(model="o1-preview")

llm_mapping = {
    "Gemini": llm_gemini,
    "AI21": llm_ai21,
    "Claude": llm_claude,
    "OpenAI": llm_openai
}
class GameRequest(BaseModel):
    player1: str
    player2: str
    rounds: int

def calculate_score(move1, move2):
    if move1 == 'C' and move2 == 'C':
        return 3, 3
    elif move1 == 'C' and move2 == 'D':
        return -10, 10
    elif move1 == 'D' and move2 == 'C':
        return 10, -10
    elif move1 == 'D' and move2 == 'D':
        return -3, -3

def extract_json_data(response):
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            return data.get("move", "C"), data.get("reason", "")
        except json.JSONDecodeError:
            return "C", "Failed to parse response."
    return "C", "Invalid response format."

@app.post("/play_game")
def play_game(request: GameRequest):
    if request.player1 not in llm_mapping or request.player2 not in llm_mapping:
        raise HTTPException(status_code=400, detail="Invalid model selection")
    
    # Game Setup
    history = []
    score1 = 0
    score2 = 0
    
    # Game Loop
    for round_num in range(1, request.rounds + 1):
        prompt = f"Game: Iterated Prisoner's Dilemma\nHistory: {history}\nRound {round_num} out of {request.rounds}." 
        
        response1 = llm_mapping[request.player1].invoke(prompt + ' You are player1').content
        response2 = llm_mapping[request.player2].invoke(prompt + ' You are player2').content
        
        move1, reason1 = extract_json_data(response1)
        move2, reason2 = extract_json_data(response2)
        
        round_score1, round_score2 = calculate_score(move1, move2)
        score1 += round_score1
        score2 += round_score2
        
        history.append({
            "round": round_num,
            "player1_move": move1,
            "player2_move": move2,
            "player1_score": round_score1,
            "player2_score": round_score2
        })
    
    return {
        "rounds": request.rounds,
        "history": history,
        "player1": {"model": request.player1, "score": score1, "reasoning": reason1},
        "player2": {"model": request.player2, "score": score2, "reasoning": reason2}
    }

@app.get("/test")
def test_route():
    return {"message": "API is running!"}

