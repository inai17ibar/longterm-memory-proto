from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import openai
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import uuid

load_dotenv()

app = FastAPI()

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

user_memory: Dict[str, Dict[str, Any]] = {}
conversations: Dict[str, List[Dict[str, Any]]] = {}

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class UserInfo(BaseModel):
    user_id: str
    name: Optional[str] = None
    hobbies: Optional[List[str]] = None
    job: Optional[str] = None
    other_info: Optional[Dict[str, Any]] = None

class ChatMessage(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    user_info_updated: bool = False

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/api/users", response_model=UserInfo)
async def create_or_update_user(user_info: UserInfo):
    """Create or update user information"""
    if user_info.user_id not in user_memory:
        user_memory[user_info.user_id] = {
            "name": user_info.name,
            "hobbies": user_info.hobbies or [],
            "job": user_info.job,
            "other_info": user_info.other_info or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    else:
        if user_info.name:
            user_memory[user_info.user_id]["name"] = user_info.name
        if user_info.hobbies:
            user_memory[user_info.user_id]["hobbies"] = user_info.hobbies
        if user_info.job:
            user_memory[user_info.user_id]["job"] = user_info.job
        if user_info.other_info:
            user_memory[user_info.user_id]["other_info"].update(user_info.other_info)
        user_memory[user_info.user_id]["updated_at"] = datetime.now().isoformat()
    
    return UserInfo(
        user_id=user_info.user_id,
        name=user_memory[user_info.user_id]["name"],
        hobbies=user_memory[user_info.user_id]["hobbies"],
        job=user_memory[user_info.user_id]["job"],
        other_info=user_memory[user_info.user_id]["other_info"]
    )

@app.get("/api/users/{user_id}", response_model=UserInfo)
async def get_user(user_id: str):
    """Get user information"""
    if user_id not in user_memory:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = user_memory[user_id]
    return UserInfo(
        user_id=user_id,
        name=user_data["name"],
        hobbies=user_data["hobbies"],
        job=user_data["job"],
        other_info=user_data["other_info"]
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_counselor(chat_message: ChatMessage):
    """Chat with AI counselor with long-term memory"""
    user_id = chat_message.user_id
    message = chat_message.message
    
    if user_id not in conversations:
        conversations[user_id] = []
    
    user_context = ""
    if user_id in user_memory:
        user_data = user_memory[user_id]
        user_context = f"""
ユーザー情報:
- 名前: {user_data.get('name', '不明')}
- 職業: {user_data.get('job', '不明')}
- 趣味: {', '.join(user_data.get('hobbies', [])) if user_data.get('hobbies') else '不明'}
- その他の情報: {json.dumps(user_data.get('other_info', {}), ensure_ascii=False)}
"""
    
    recent_conversations = conversations[user_id][-10:] if conversations[user_id] else []
    conversation_context = ""
    if recent_conversations:
        conversation_context = "\n過去の会話:\n"
        for conv in recent_conversations:
            conversation_context += f"ユーザー: {conv['user_message']}\nカウンセラー: {conv['ai_response']}\n\n"
    
    system_prompt = f"""あなたは経験豊富で共感的なメンタルヘルスカウンセラーです。以下の点を心がけてください：

1. 温かく、理解のある態度で接する
2. ユーザーの感情を受け入れ、判断しない
3. 適切な質問をして、ユーザーが自分の気持ちを整理できるよう支援する
4. 必要に応じて実用的なアドバイスやコーピング戦略を提供する
5. 深刻な状況では専門家への相談を勧める
6. ユーザーの過去の情報や会話内容を覚えて、継続的なサポートを提供する

{user_context}

{conversation_context}

日本語で自然に会話してください。"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        conversations[user_id].append({
            "user_message": message,
            "ai_response": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        user_info_updated = await extract_user_info(user_id, message, ai_response)
        
        return ChatResponse(
            response=ai_response,
            user_info_updated=user_info_updated
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI API: {str(e)}")

async def extract_user_info(user_id: str, user_message: str, ai_response: str) -> bool:
    """Extract user information from conversation using AI-powered analysis"""
    updated = False
    
    if user_id not in user_memory:
        user_memory[user_id] = {
            "name": None,
            "hobbies": [],
            "job": None,
            "other_info": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    try:
        extraction_prompt = f"""
以下のユーザーメッセージから個人情報を抽出してください。JSONフォーマットで回答してください。
情報が明確でない場合は null を返してください。

ユーザーメッセージ: "{user_message}"

以下のフォーマットで回答してください:
{{
    "name": "抽出された名前（フルネームまたは名前のみ）",
    "job": "職業・仕事内容",
    "hobbies": ["趣味1", "趣味2", "趣味3"],
    "age": "年齢（数字のみ）",
    "location": "住んでいる場所",
    "family": "家族構成に関する情報",
    "concerns": "悩みや心配事",
    "goals": "目標や願望",
    "personality": "性格的特徴",
    "experiences": "重要な体験や出来事"
}}

注意: 
- 明確に言及されていない情報は null にしてください
- 趣味は配列で複数返してください
- 推測ではなく、明確に述べられた情報のみ抽出してください
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは日本語テキストから個人情報を正確に抽出するAIアシスタントです。JSONフォーマットでのみ回答してください。"},
                {"role": "user", "content": extraction_prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        extracted_text = response.choices[0].message.content.strip()
        
        if extracted_text.startswith('```json'):
            extracted_text = extracted_text[7:-3].strip()
        elif extracted_text.startswith('```'):
            extracted_text = extracted_text[3:-3].strip()
        
        try:
            extracted_info = json.loads(extracted_text)
        except json.JSONDecodeError:
            return False
        
        current_data = user_memory[user_id]
        
        if extracted_info.get("name") and extracted_info["name"] != current_data.get("name"):
            current_data["name"] = extracted_info["name"]
            updated = True
        
        if extracted_info.get("job") and extracted_info["job"] != current_data.get("job"):
            current_data["job"] = extracted_info["job"]
            updated = True
        
        if extracted_info.get("hobbies") and isinstance(extracted_info["hobbies"], list):
            new_hobbies = [h for h in extracted_info["hobbies"] if h and h not in current_data["hobbies"]]
            if new_hobbies:
                current_data["hobbies"].extend(new_hobbies)
                updated = True
        
        other_fields = ["age", "location", "family", "concerns", "goals", "personality", "experiences"]
        for field in other_fields:
            if extracted_info.get(field) and extracted_info[field] != current_data["other_info"].get(field):
                current_data["other_info"][field] = extracted_info[field]
                updated = True
        
        if updated:
            current_data["updated_at"] = datetime.now().isoformat()
        
        return updated
        
    except Exception as e:
        return False

@app.get("/api/conversations/{user_id}")
async def get_conversation_history(user_id: str):
    """Get conversation history for a user"""
    if user_id not in conversations:
        return {"conversations": []}
    
    return {"conversations": conversations[user_id]}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    """Delete user data"""
    if user_id in user_memory:
        del user_memory[user_id]
    if user_id in conversations:
        del conversations[user_id]
    return {"message": "User data deleted successfully"}
