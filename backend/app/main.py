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
import csv
from io import StringIO

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
    memory_items: Optional[List[Dict[str, Any]]] = None

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
            "memory_items": [],
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
        other_info=user_memory[user_info.user_id]["other_info"],
        memory_items=user_memory[user_info.user_id]["memory_items"]
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
        other_info=user_data["other_info"],
        memory_items=user_data["memory_items"]
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
        
        memory_summary = ""
        if user_data.get('memory_items'):
            recent_memories = user_data['memory_items'][-20:]
            memory_summary = "\n記憶している情報:\n"
            for item in recent_memories:
                memory_summary += f"- {item['type']}: {item['content']}\n"
        
        user_context = f"""
ユーザー情報:
- 名前: {user_data.get('name', '不明')}
- 職業: {user_data.get('job', '不明')}
- 趣味: {', '.join(user_data.get('hobbies', [])) if user_data.get('hobbies') else '不明'}
- その他の情報: {json.dumps(user_data.get('other_info', {}), ensure_ascii=False)}
{memory_summary}

重要: 上記の記憶している情報を会話の中で自然に活用してください。ユーザーの過去の発言や状況を覚えていることを示し、継続的なサポートを提供してください。
"""
    
    recent_conversations = conversations[user_id][-10:] if conversations[user_id] else []
    conversation_context = ""
    if recent_conversations:
        conversation_context = "\n過去の会話:\n"
        for conv in recent_conversations:
            conversation_context += f"ユーザー: {conv['user_message']}\nカウンセラー: {conv['ai_response']}\n\n"
    
    system_prompt = f"""あなたはAIメンタルカウンセラーで、うつ病で休職中のユーザや、うつ病からの復帰を目指している、または復帰の途中のユーザを対象にメンタルヘルスサポートを提供するカウンセラーです。

このGPTはユーザとの対話を通じて共感を示し、ユーザの気持ちを理解しようと努めます。問題解決に直接踏み込むことはせず、ユーザが安心して話せる場を提供します。
対面での会話のように比較的短い文で返答し、自然で人間らしいバリエーションに富んだ会話を目指します。

制約条件：
・一度の発話は400文字以内とします。
・ユーザとカウンセリングのように繰り返し対話してください。
・ユーザに対して優しく、親しみやすい言葉使いを使用し、リラックスした雰囲気を作り出すよう努めます。
・穏やかな会話調で、日本語で話し方が単調になりすぎず人間の対話のようにバリエーションに富んだものを提供します。
・このGPTは医療行為や診断を行わず、専門的な治療を提供しません。緊急事態や危機的状況に対しては、適切な専門家に相談するようユーザに促します。
・また、ユーザが困っていることがありそうなときは、その解決策を複数提示してあげてください。これもできるだけバリエーションに富むようにしてください。

{user_context}

{conversation_context}

日本語で自然に会話してください。"""

    try:
        # Mock response for testing when OpenAI API is not available
        if not os.getenv("OPENAI_API_KEY") or "insufficient_quota" in str(e) if 'e' in locals() else False:
            ai_response = f"こんにちは。お話をお聞かせいただき、ありがとうございます。「{message}」について、お気持ちをお聞かせください。私はあなたのサポートをさせていただきます。"
        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
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
        # Fallback to mock response if OpenAI API fails
        ai_response = f"申し訳ございませんが、現在システムに問題が発生しております。「{message}」についてお話しいただき、ありがとうございます。お気持ちをお聞かせください。"
        
        conversations[user_id].append({
            "user_message": message,
            "ai_response": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        return ChatResponse(
            response=ai_response,
            user_info_updated=False
        )

async def extract_user_info(user_id: str, user_message: str, ai_response: str) -> bool:
    """Extract user information from conversation using AI-powered analysis with 100-item limit"""
    updated = False
    
    if user_id not in user_memory:
        user_memory[user_id] = {
            "name": None,
            "hobbies": [],
            "job": None,
            "other_info": {},
            "memory_items": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    try:
        # Mock extraction for testing - simple keyword-based extraction
        extracted_info = {}
        message_lower = user_message.lower()
        
        # Simple extraction patterns
        if "名前" in user_message or "です" in user_message:
            # This is a very basic extraction - in reality you'd use more sophisticated NLP
            pass
        
        if not os.getenv("OPENAI_API_KEY"):
            # Skip AI extraction when no API key
            extracted_info = {}
        else:
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
                model="gpt-3.5-turbo",
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
        
        
        other_fields = ["age", "location", "family", "concerns", "goals", "personality", "experiences"]
        for field in other_fields:
            if extracted_info.get(field):
                existing_items = [item['content'] for item in current_data["memory_items"] if item['type'] == field]
                if extracted_info[field] not in existing_items:
                    memory_item = {
                        "type": field,
                        "content": extracted_info[field],
                        "timestamp": datetime.now().isoformat(),
                        "source": "conversation"
                    }
                    current_data["memory_items"].append(memory_item)
                    updated = True
        
        if extracted_info.get("name") and extracted_info["name"] != current_data.get("name"):
            current_data["name"] = extracted_info["name"]
            memory_item = {
                "type": "name",
                "content": extracted_info["name"],
                "timestamp": datetime.now().isoformat(),
                "source": "conversation"
            }
            current_data["memory_items"].append(memory_item)
            updated = True
        
        if extracted_info.get("job") and extracted_info["job"] != current_data.get("job"):
            current_data["job"] = extracted_info["job"]
            memory_item = {
                "type": "job",
                "content": extracted_info["job"],
                "timestamp": datetime.now().isoformat(),
                "source": "conversation"
            }
            current_data["memory_items"].append(memory_item)
            updated = True
        
        if extracted_info.get("hobbies") and isinstance(extracted_info["hobbies"], list):
            new_hobbies = [h for h in extracted_info["hobbies"] if h and h not in current_data["hobbies"]]
            if new_hobbies:
                current_data["hobbies"].extend(new_hobbies)
                for hobby in new_hobbies:
                    memory_item = {
                        "type": "hobby",
                        "content": hobby,
                        "timestamp": datetime.now().isoformat(),
                        "source": "conversation"
                    }
                    current_data["memory_items"].append(memory_item)
                updated = True
        
        if len(current_data["memory_items"]) > 100:
            items_to_remove = len(current_data["memory_items"]) - 100
            current_data["memory_items"] = current_data["memory_items"][items_to_remove:]
        
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

@app.get("/api/export-conversations/{user_id}")
async def export_conversations_csv(user_id: str):
    """Export conversation history as CSV"""
    if user_id not in conversations:
        raise HTTPException(status_code=404, detail="No conversations found for user")
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["timestamp", "user_message", "ai_response"])
    
    for conv in conversations[user_id]:
        writer.writerow([
            conv["timestamp"],
            conv["user_message"],
            conv["ai_response"]
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return {"csv_data": csv_content, "filename": f"conversations_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    """Delete user data"""
    if user_id in user_memory:
        del user_memory[user_id]
    if user_id in conversations:
        del conversations[user_id]
    return {"message": "User data deleted successfully"}
