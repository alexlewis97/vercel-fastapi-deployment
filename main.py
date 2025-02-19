from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from config import Settings
from langchain_ai21 import ChatAI21
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAI
import os
import json
import re

settings = Settings()

os.environ["GOOGLE_API_KEY"] = settings.gemini_key
llm_gemini = ChatGoogleGenerativeAI(model='gemini-2.0-flash-thinking-exp-01-21')

os.environ["AI21_API_KEY"] = settings.api_key
llm_ai21 = ChatAI21(model="jamba-1.5-large", temperature=0)

os.environ['ANTHROPIC_API_KEY'] = settings.anthropic_key
llm_claude = ChatAnthropic(model='claude-3-5-sonnet-20241022')

os.environ["OPENAI_API_KEY"] = settings.openai_key
llm_openai = OpenAI(model="o1-preview")

llm_mapping = {
    "Gemini": llm_gemini,
    "AI21": llm_ai21,
    "Claude": llm_claude,
    "OpenAI": llm_openai
}

app = FastAPI()

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
    
    intro = """Game: You are participating in an iterated Prisoner’s Dilemma..."""
    task = """Your Task: Based on the history and expected rounds..."""
    future = "This is round"
    
    history = ""
    score1 = 0
    score2 = 0

    for round_num in range(1, request.rounds + 1):
        prompt = f"{intro}\n{history}\n{future} {round_num} out of {request.rounds}.\n\n{task}"
        
        response1 = llm_mapping[request.player1].invoke(prompt + ' you are player1').content
        response2 = llm_mapping[request.player2].invoke(prompt + ' you are player2').content
        
        move1, reason1 = extract_json_data(response1)
        move2, reason2 = extract_json_data(response2)
        
        round_score1, round_score2 = calculate_score(move1, move2)
        score1 += round_score1
        score2 += round_score2
        
        history += f"Round {round_num}: Player1: {move1}, Player2: {move2}\n"
    
    return {
        "player1": {"score": score1, "reasoning": reason1},
        "player2": {"score": score2, "reasoning": reason2},
        "history": history.split("\n")
    }from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from config import Settings
from langchain_ai21 import ChatAI21
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAI
import os
import json
import re

settings = Settings()

os.environ["GOOGLE_API_KEY"] = settings.gemini_key
llm_gemini = ChatGoogleGenerativeAI(model='gemini-2.0-flash-thinking-exp-01-21')

os.environ["AI21_API_KEY"] = settings.api_key
llm_ai21 = ChatAI21(model="jamba-1.5-large", temperature=0)

os.environ['ANTHROPIC_API_KEY'] = settings.anthropic_key
llm_claude = ChatAnthropic(model='claude-3-5-sonnet-20241022')

os.environ["OPENAI_API_KEY"] = settings.openai_key
llm_openai = OpenAI(model="o1-preview")

llm_mapping = {
    "Gemini": llm_gemini,
    "AI21": llm_ai21,
    "Claude": llm_claude,
    "OpenAI": llm_openai
}

app = FastAPI()

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
    
    intro = """Game: You are participating in an iterated Prisoner’s Dilemma..."""
    task = """Your Task: Based on the history and expected rounds..."""
    future = "This is round"
    
    history = ""
    score1 = 0
    score2 = 0

    for round_num in range(1, request.rounds + 1):
        prompt = f"{intro}\n{history}\n{future} {round_num} out of {request.rounds}.\n\n{task}"
        
        response1 = llm_mapping[request.player1].invoke(prompt + ' you are player1').content
        response2 = llm_mapping[request.player2].invoke(prompt + ' you are player2').content
        
        move1, reason1 = extract_json_data(response1)
        move2, reason2 = extract_json_data(response2)
        
        round_score1, round_score2 = calculate_score(move1, move2)
        score1 += round_score1
        score2 += round_score2
        
        history += f"Round {round_num}: Player1: {move1}, Player2: {move2}\n"
    
    return {
        "player1": {"score": score1, "reasoning": reason1},
        "player2": {"score": score2, "reasoning": reason2},
        "history": history.split("\n")
    }

@app.get("/test")
def test_route():
    return {"message": "API is running!"}@app.get("/test")
