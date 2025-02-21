from time import time
from fastapi import FastAPI, HTTPException, __version__
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from langchain_ai21 import ChatAI21
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAI
import os
import json
import re

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

class RoundRequest(BaseModel):
    player1: str
    player2: str
    rounds: int
    current_round: int
    history: list
    payouts: dict

def calculate_score(move1, move2, payouts):
    if move1 == 'C' and move2 == 'C':
        return payouts["CC"], payouts["CC"]
    elif move1 == 'C' and move2 == 'D':
        return payouts["CD"], payouts["DC"]
    elif move1 == 'D' and move2 == 'C':
        return payouts["DC"], payouts["CD"]
    elif move1 == 'D' and move2 == 'D':
        return payouts["DD"], payouts["DD"]

def extract_json_data(response):
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            return data.get("move", "C"), data.get("reason", "")
        except json.JSONDecodeError:
            return "C", "Failed to parse response."
    return "C", "Invalid response format."

@app.post("/play_round")
def play_round(request: RoundRequest):
    if request.player1 not in llm_mapping or request.player2 not in llm_mapping:
        raise HTTPException(status_code=400, detail="Invalid model selection")
    
     intro = '''Game:
                        You are participating in an iterated Prisoner’s Dilemma. You and an opponent each choose one of two actions:
                        
                        Cooperate (C): You both gain a moderate reward
                        Defect (D): If one defects while the other cooperates, the defector gains a large reward , and the cooperator suffers a penalty
                        Mutual Defection (D, D) results in a loss for both . '''

    instructions = '''Your Task: Based on the history and expected rounds, choose your next move: C (Cooperate) or D (Defect).
                        The format of the answer should be in a json format the first part of the json should be move: with the options D or C and the next should be reason: with the reasoning behind the move, don't include any \n in the json format'''
        
    task = """Your Task: Based on the history and expected rounds..."""
    payouts= """The payouts for the game are the following: CC - {payouts["CC"]} CD - {payouts["CD"]} DC - {payouts["DC"]} DD - {payouts["DD"]} """
    prompt = f"{intro}{payouts} \nHistory: {request.history}\nRound {request.current_round} out of {request.rounds}.\n\n{instructions}"
    
    response1 = llm_mapping[request.player1].invoke(prompt + ' You are player1').content
    response2 = llm_mapping[request.player2].invoke(prompt + ' You are player2').content
    
    move1, reason1 = extract_json_data(response1)
    move2, reason2 = extract_json_data(response2)
    
    round_score1, round_score2 = calculate_score(move1, move2, request.payouts)
    
    return {
        "current_round": request.current_round,
        "player1": {"move": move1, "score": round_score1, "reason": reason1},
        "player2": {"move": move2, "score": round_score2, "reason": reason2},
        "history": request.history + [{
            "round": request.current_round,
            "player1_move": move1,
            "player2_move": move2,
            "player1_score": round_score1,
            "player2_score": round_score2
        }]
    }

@app.get("/test")
def test_route():
    return {"message": "API is running!"}
