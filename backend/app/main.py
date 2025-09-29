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
import re

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
    response_type: int  # 1, 2, 3のどのパターンか
    user_info_updated: bool = False

def analyze_response_pattern(user_message: str, conversation_history: List[Dict]) -> int:
    """ユーザーメッセージを分析して、回答パターン(1,2,3)を判断する"""
    message = user_message.strip().lower()
    
    # パターン1: 短い返事や話の途中
    short_responses = ['はい', 'うん', 'そう', 'まあ', 'うーん', 'あー', 'えー', '...', '。', 'そうですね']
    if (len(message) <= 10 and any(resp in message for resp in short_responses)) or message.endswith('...'):
        return 1
    
    # 最近の会話履歴をチェック
    if len(conversation_history) >= 2:
        last_ai_response = conversation_history[-1].get('ai_response', '')
        if '？' in last_ai_response or '?' in last_ai_response:
            # 前回質問していて、短い回答の場合
            if len(message) <= 15:
                return 1
    
    # パターン3: 解決策を求めているか、具体的な悩みを表現している
    solution_keywords = ['どうすれば', 'どうしたら', 'どうやって', '方法', '解決', 'アドバイス', '助け', 'わからない']
    problem_keywords = ['困って', '悩んで', '辛い', '苦しい', 'もうだめ', '限界', '疲れた', 'ストレス', '不安', '心配']
    
    if any(keyword in message for keyword in solution_keywords + problem_keywords):
        return 3
    
    # デフォルトはパターン2（傾聴）
    return 2

def generate_system_prompt(user_context: str, conversation_context: str, response_pattern: int) -> str:
    """回答パターンに応じたシステムプロンプトを生成"""
    
    base_prompt = f"""あなたは「メンタルバリアフリー」というビジョンを持つAIメンタルカウンセラーです。

## あなたのビジョンと基本スタンス
- 不安や悩みを抱える人の感情も、それが個性であると捉えてください
- 無理に更生させようとせず、あなた自身がユーザーに合わせて変わってください
- ユーザーにとって「ここだけは自分らしくいられる」「居心地が良い」場所を提供してください

## 制約条件
- うつ病で休職中のユーザや復職を目指している方、その他メンタルヘルスに関する方を主な対象とします
- 医療行為や診断は行わず、緊急事態では専門家への相談を促します
- 対面での会話のように自然で人間らしいバリエーションに富んだ会話を目指します
- 記憶しているユーザの情報を会話の中で自然に活用してください
- 適度に改行を入れて読みやすくしてください

{user_context}

{conversation_context}"""

    if response_pattern == 1:
        return base_prompt + """

## 回答方針（パターン1: 応答のみ）
- ユーザーの話が途中で途切れており、続きがありそうな状況です
- 「はい」「なるほど」「そうなんですね」など適切な相槌だけしてください
- 特に質問をする必要はありません
- 15文字以下で回答してください
- ユーザーが話を続けやすい雰囲気を作ってください"""

    elif response_pattern == 2:
        return base_prompt + """

## 回答方針（パターン2: 傾聴）
- 傾聴型で、ユーザーが気軽に話せるように質問してください
- 共感が第一：「〜してくれてありがとう」「〜なのは自然なこと」「〜という気持ち、すごくわかります」
- 評価しない・急がない：「〜すべき」「〜が悪い」は避け、ただ話を「受け止める」
- 安心・安全の場づくり：「ここでは〜しても大丈夫」「一人じゃないです」
- ポジティブもネガティブも尊重：「その報告うれしいです」「苦しい中でよく話してくれました」
- 100文字以下で回答してください"""

    else:  # pattern 3
        return base_prompt + """

## 回答方針（パターン3: 解決策提案・客観的視点）
- ユーザーが悩んで周りが見えなくなっている状況かもしれません
- 客観的で冷静な視点を入れてあげてください
- 客観的に、ユーザーの良さを見つけて褒めてください
- 解決を急がず、ユーザーが安心して話せる感覚を持たせてください
- 解決策の押し付けはせず、どんなことができそうか一緒に考える姿勢を持ってください
- 200文字以下で回答してください"""

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
    
    # 回答パターンを判断
    response_pattern = analyze_response_pattern(message, conversations[user_id])
    
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
    
    system_prompt = generate_system_prompt(user_context, conversation_context, response_pattern)

    try:
        # Mock response for testing when OpenAI API is not available
        if not os.getenv("OPENAI_API_KEY"):
            if response_pattern == 1:
                ai_response = "はい。"
            elif response_pattern == 2:
                ai_response = f"「{message}」についてお話しいただき、ありがとうございます。\n\nその気持ち、とてもよくわかります。もう少し詳しく聞かせていただけますか？"
            else:  # pattern 3
                ai_response = f"お話ししていただき、ありがとうございます。\n\n{message}について悩んでいらっしゃるのですね。一人で抱え込まずに話してくださって、とても勇気があると思います。\n\n一緒にどんなことができそうか考えてみませんか？"
        else:
            response = client.chat.completions.create(
                model="gpt-4o",
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
            "response_pattern": response_pattern,
            "timestamp": datetime.now().isoformat()
        })
        
        user_info_updated = await extract_user_info(user_id, message, ai_response)
        
        return ChatResponse(
            response=ai_response,
            response_type=response_pattern,
            user_info_updated=user_info_updated
        )
        
    except Exception as e:
        # Fallback to mock response if OpenAI API fails
        if response_pattern == 1:
            ai_response = "はい。"
        elif response_pattern == 2:
            ai_response = f"お話しいただき、ありがとうございます。その気持ち、よくわかります。"
        else:
            ai_response = f"申し訳ございませんが、現在システムに問題が発生しております。お話しいただき、ありがとうございます。"
        
        conversations[user_id].append({
            "user_message": message,
            "ai_response": ai_response,
            "response_pattern": response_pattern,
            "timestamp": datetime.now().isoformat()
        })
        
        user_info_updated = await extract_user_info(user_id, message, ai_response)
        
        return ChatResponse(
            response=ai_response,
            response_type=response_pattern,
            user_info_updated=user_info_updated
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
        if not os.getenv("OPENAI_API_KEY"):
            # モック抽出：基本的なキーワードベースの抽出
            extracted_info = {}
            message_lower = user_message.lower()
            
            # メンタルヘルスに特化した抽出パターン
            if any(word in message_lower for word in ['不安', '心配', '悩み', '困って', '辛い', '苦しい']):
                extracted_info['concerns'] = user_message
            if any(word in message_lower for word in ['目標', 'やりたい', '頑張り', '復職', '改善']):
                extracted_info['goals'] = user_message
            if any(word in message_lower for word in ['眠れない', '食欲', '体調', '症状', '痛み', '疲れ']):
                extracted_info['symptoms'] = user_message
            if any(word in message_lower for word in ['ストレス', 'プレッシャー', '原因', 'きっかけ', '職場']):
                extracted_info['triggers'] = user_message
            if any(word in message_lower for word in ['散歩', 'リラックス', '気分転換', '対処', '趣味']):
                extracted_info['coping_methods'] = user_message
            if any(word in message_lower for word in ['家族', '友達', 'サポート', '支え', '相談']):
                extracted_info['support_system'] = user_message
            if any(word in message_lower for word in ['薬', '通院', '病院', '治療', '診察']):
                extracted_info['medication'] = user_message
            if any(word in message_lower for word in ['会社', '職場', '休職', '復職', '仕事', '上司']):
                extracted_info['work_status'] = user_message
            if any(word in message_lower for word in ['朝', '夜', '生活', '日常', 'ルーティン', '時間']):
                extracted_info['daily_routine'] = user_message
            if any(word in message_lower for word in ['気持ち', '感情', '落ち込み', '嬉しい', '悲しい', '怒り']):
                extracted_info['emotional_state'] = user_message
            
            print(f"Mock extraction result: {extracted_info}")
        else:
            extraction_prompt = f"""
以下のユーザーメッセージからメンタルヘルス関連情報と個人情報を抽出してください。
メンタルバリアフリーの観点から、ユーザーの感情や状況を個性として捉え、細かな変化も記録してください。

ユーザーメッセージ: "{user_message}"

以下のフォーマットで回答してください（JSONのみ）:
{{
    "name": "名前（明確に述べられた場合のみ）",
    "job": "職業・仕事内容",
    "hobbies": ["趣味1", "趣味2"],
    "age": "年齢",
    "location": "住んでいる場所",
    "family": "家族構成に関する情報",
    "concerns": "現在の悩みや不安・心配事",
    "goals": "目標や願望・やりたいこと",
    "personality": "性格的特徴・個性",
    "experiences": "重要な体験や出来事",
    "symptoms": "メンタル・身体的症状（睡眠、食欲、気分変化等）",
    "triggers": "ストレス要因・きっかけ",
    "coping_methods": "対処法・リラックス方法・気分転換",
    "support_system": "サポート体制・相談相手",
    "medication": "服薬・通院状況",
    "work_status": "勤務・休職・復職状況",
    "daily_routine": "日常の過ごし方・生活リズム",
    "emotional_state": "現在の気持ち・感情状態・心境"
}}

注意:
- 明確に言及されていない情報は null にしてください
- 小さな変化や気づきも記録してください
- 感情の変化は特に丁寧に抽出してください
- 推測ではなく、実際に述べられた内容のみ抽出してください
"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたはメンタルヘルス情報を正確に抽出するAIアシスタントです。JSONフォーマットでのみ回答してください。"},
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
        
        # メンタルヘルス関連情報の抽出と保存
        mental_health_fields = ["concerns", "goals", "personality", "experiences", 
                               "symptoms", "triggers", "coping_methods", "support_system", 
                               "medication", "work_status", "daily_routine", "emotional_state"]
        
        other_fields = ["age", "location", "family"]
        
        for field in mental_health_fields + other_fields:
            if extracted_info.get(field):
                field_value = extracted_info[field].strip()
                if field_value and len(field_value) > 3:  # より意味のある情報のみ保存
                    existing_items = [item['content'] for item in current_data["memory_items"] if item['type'] == field]
                    
                    # 重複チェック（完全一致および類似チェック）
                    is_duplicate = any(
                        field_value.lower().strip() == existing.lower().strip() or
                        (len(field_value) > 10 and field_value.lower() in existing.lower())
                        for existing in existing_items
                    )
                    
                    if not is_duplicate:
                        memory_item = {
                            "type": field,
                            "content": field_value,
                            "timestamp": datetime.now().isoformat(),
                            "source": "conversation"
                        }
                        current_data["memory_items"].append(memory_item)
                        updated = True
                        print(f"Added memory item: {field} = {field_value}")
        
        # 基本情報の更新
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
        
        # メモリ制限（100個まで）
        if len(current_data["memory_items"]) > 100:
            items_to_remove = len(current_data["memory_items"]) - 100
            current_data["memory_items"] = current_data["memory_items"][items_to_remove:]
        
        if updated:
            current_data["updated_at"] = datetime.now().isoformat()
        
        return updated
        
    except Exception as e:
        print(f"Error in extract_user_info: {e}")
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
    
    writer.writerow(["timestamp", "user_message", "ai_response", "response_pattern"])
    
    for conv in conversations[user_id]:
        writer.writerow([
            conv["timestamp"],
            conv["user_message"],
            conv["ai_response"],
            conv.get("response_pattern", "unknown")
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return {"csv_data": csv_content, "filename": f"conversations_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}

@app.delete("/api/conversations/{user_id}")
async def clear_conversations(user_id: str):
    """Clear conversation history while keeping user memory"""
    if user_id in conversations:
        del conversations[user_id]
    return {"message": "Conversation history cleared successfully"}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    """Delete user data"""
    if user_id in user_memory:
        del user_memory[user_id]
    if user_id in conversations:
        del conversations[user_id]
    return {"message": "User data deleted successfully"}

# 新しいエンドポイント：回答パターンの統計を取得
@app.get("/api/analytics/{user_id}")
async def get_user_analytics(user_id: str):
    """Get user conversation analytics"""
    if user_id not in conversations:
        raise HTTPException(status_code=404, detail="User not found")
    
    convs = conversations[user_id]
    pattern_counts = {1: 0, 2: 0, 3: 0}
    
    for conv in convs:
        pattern = conv.get("response_pattern", 2)
        pattern_counts[pattern] += 1
    
    return {
        "user_id": user_id,
        "total_conversations": len(convs),
        "pattern_distribution": pattern_counts,
        "recent_patterns": [conv.get("response_pattern", 2) for conv in convs[-10:]]
    }