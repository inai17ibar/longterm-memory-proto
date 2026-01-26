import csv
import json
import logging
import os
import sys
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

import openai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .analysis_layer import analysis_layer
from .extended_profile import ExtendedUserProfile, extended_profile_system
from .knowledge_base import knowledge_base
from .memory_system import MemoryItem, memory_system
from .user_profile import UserProfile, user_profile_system

# Windowsコンソールでの文字化け対策
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# ログディレクトリの作成
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

# ログファイルの設定（日付ごとにファイルを分ける）
log_file = log_dir / f"server_{datetime.now().strftime('%Y%m%d')}.log"

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

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

user_memory: dict[str, dict[str, Any]] = {}
conversations: dict[str, list[dict[str, Any]]] = {}

# ユーザー状態管理（感情・ニーズ・モード）
# スキーマ:
# {
#   "mood": 0-10 (全体的な気分),
#   "energy": 0-10 (エネルギー・やる気),
#   "anxiety": 0-10 (不安の強さ),
#   "main_topics": ["テーマ1", "テーマ2"],
#   "need": "共感してほしい / 解決のヒント / 話を整理したい 等",
#   "modes": ["empathy", "emotion_labeling", ...],  # このターンで優先するカウンセリングモード
#   "state_comment": "状態の簡単な説明"
# }
user_states: dict[str, dict[str, Any]] = {}

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class UserInfo(BaseModel):
    user_id: str
    name: str | None = None
    hobbies: list[str] | None = None
    job: str | None = None
    other_info: dict[str, Any] | None = None
    memory_items: list[dict[str, Any]] | None = None


class ChatMessage(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    response_type: int  # 1, 2, 3のどのパターンか
    user_info_updated: bool = False


async def analyze_user_state(
    user_id: str,
    user_message: str,
    recent_conversations: list[dict[str, Any]],
    relevant_memories: list[MemoryItem],
) -> dict[str, Any]:
    """
    ユーザーの現在の感情・ニーズ・推奨モードをLLMで推定して user_states に保存する
    新しい分析層とプロファイルシステムを使用
    """
    # ユーザープロファイルを取得
    user_profile = user_profile_system.get_profile(user_id)

    # 分析層を使用して状態推定
    state = await analysis_layer.analyze_user_state(
        user_id=user_id,
        user_message=user_message,
        user_profile=user_profile,
        recent_conversations=recent_conversations,
        relevant_memories=relevant_memories,
    )

    user_states[user_id] = state
    return state


def analyze_response_pattern(user_message: str, conversation_history: list[dict]) -> int:
    """ユーザーメッセージを分析して、回答パターン(1,2,3)を判断する"""
    message = user_message.strip().lower()

    # 最近のAIの応答を確認
    last_ai_response = ""
    if conversation_history:
        last_ai_response = conversation_history[-1].get("ai_response", "")

    # パターン3: 解決策を求めているか、具体的な悩みを表現している
    solution_keywords = [
        "どうすれば",
        "どうしたら",
        "どうやって",
        "方法",
        "解決",
        "アドバイス",
        "助け",
        "わからない",
    ]
    problem_keywords = [
        "困って",
        "悩んで",
        "辛い",
        "苦しい",
        "もうだめ",
        "限界",
        "疲れた",
        "ストレス",
        "不安",
        "心配",
    ]

    if any(keyword in message for keyword in solution_keywords + problem_keywords):
        return 3

    # パターン1: 短い返事や話の途中（相槌のみ）
    # 非常に短い返答は基本的にパターン1（相槌）として扱う
    short_responses = [
        "はい",
        "うん",
        "そう",
        "いいえ",
        "ええ",
        "うーん",
        "あー",
        "えー",
        "まあ",
        "ん",
        "ふむ",
        "へえ",
        "ほう",
    ]

    # 5文字以下の短い返答、または「...」で終わる場合はパターン1
    if len(message) <= 5:
        # 短い返答リストに完全一致する場合
        if any(resp == message for resp in short_responses):
            return 1
        # 3文字以下の超短文の場合も相槌とみなす
        if len(message) <= 3:
            return 1

    # 「...」で終わる場合も相槌（話の途中）
    if message.endswith("..."):
        return 1

    # 短い肯定的な返答でAIが提案していた場合のみパターン2
    affirmative_responses = [
        "はい",
        "うん",
        "そう",
        "いいです",
        "お願い",
        "そうですね",
        "ええ",
        "お願いします",
    ]
    is_affirmative = any(resp in message for resp in affirmative_responses)

    if is_affirmative and len(message) > 5 and len(message) <= 15:
        # AIが提案していた場合のみパターン2に
        proposal_keywords = ["ませんか", "考えて", "試して", "工夫", "一緒に", "できそう", "方法"]
        if any(keyword in last_ai_response for keyword in proposal_keywords):
            return 2

    # デフォルトはパターン2（傾聴）
    return 2


def generate_system_prompt(
    conversation_context: str, response_pattern: int, extended_profile=None
) -> str:
    """回答パターンに応じたシステムプロンプトを生成"""

    # 拡張プロファイルから設定を取得
    ai_name = "カウンセラー"
    ai_personality = "優しく寄り添うガイド"
    response_length_style = "medium"

    if extended_profile:
        settings = extended_profile.profile_settings
        ai_name = settings.ai_name
        ai_personality = settings.ai_personality
        response_length_style = settings.response_length_style

    # カスタムプロンプト機能は削除されました
    # if custom_prompt:
    #     # カスタムプロンプトに変数を置換
    #     prompt = custom_prompt
    #     prompt = prompt.replace("{conversation_context}", conversation_context)
    #     prompt = prompt.replace("{ai_name}", ai_name)
    #     prompt = prompt.replace("{ai_personality}", ai_personality)
    #     prompt = prompt.replace("{response_pattern}", str(response_pattern))
    #     return prompt

    # 応答スタイルに応じた文字数制限
    length_limits = {
        "short": {"pattern1": 15, "pattern2": 80, "pattern3": 150},
        "medium": {"pattern1": 15, "pattern2": 100, "pattern3": 200},
        "long": {"pattern1": 15, "pattern2": 150, "pattern3": 300},
    }
    limits = length_limits.get(response_length_style, length_limits["medium"])

    base_prompt = f"""あなたは{ai_name}という名前のAIメンタルカウンセラーです。
あなたの性格・役割は「{ai_personality}」です。

## あなたのビジョンと基本スタンス
「メンタルバリアフリー」というビジョンを持っています。
- 不安や悩みを抱える人の感情も、それが個性であると捉えてください
- 無理に更生させようとせず、あなた自身がユーザーに合わせて変わってください
- ユーザーにとって「ここでは自分らしくいられる」「居心地が良い」場所を提供してください

## 会話モード
ユーザーコンテキストメッセージ内には「このターンで優先したいモード」が含まれます。
modesに含まれるものを優先して使ってください：

- empathy: 共感・受容を前面に出し、「わかってもらえた感」を最優先にする
- emotion_labeling: ユーザーの感情に名前をつけてあげる（不安、悲しみ、怒り、戸惑い など）
- problem_sorting: 状況を一緒に整理し、「何が起きているか」を一緒に言語化する
- small_action: 今日〜数日のあいだにできそうな、負担の小さい行動を一緒に考える
- psychoeducation: 必要に応じて、メンタルヘルスに関する情報や考え方のヒントを優しく共有する

必ずしも全部を使う必要はありません。modesに含まれる2つを中心にしてください。

## 制約条件
- うつ病で休職中のユーザや復職を目指している方、その他メンタルヘルスに関する方を主な対象とします
- 医療行為や診断は行わず、緊急事態では専門家への相談を促します
- 対面での会話のように自然で人間らしいバリエーションに富んだ会話を目指します
- 記憶しているユーザの情報を会話の中で自然に活用してください
- 適度に改行を入れて読みやすくしてください

重要指示:
- 上記のプロファイル・記憶を会話の中で**能動的かつ自然に**活用してください
- 「～さんは以前〇〇とおっしゃっていましたね」「～について頑張っていますね」のように、こちらから記憶を参照してください
- ユーザーが「私の名前は？」と聞かなくても、適切なタイミングで記憶している情報を使って声をかけてください
- 過去の悩みや目標の進捗を気にかけ、継続的なサポートを示してください
- 関連する専門知識がある場合は、それを自然に会話に織り込んでください（専門用語の押し付けは避ける）
- プロファイルに記録された症状やストレス要因を踏まえて、個別化された応答を心がけてください

{conversation_context}"""

    if response_pattern == 1:
        return (
            base_prompt
            + f"""

## 回答方針（パターン1: 応答のみ）
- ユーザーの話が途中で途切れており、続きがありそうな状況です
- 「はい」「なるほど」「そうなんですね」「うんうん」「うん」など適切な相槌だけしてください
- 特に質問をする必要はありません
- {limits['pattern1']}文字以下で回答してください
- ユーザーが話を続けやすい雰囲気を作ってください"""
        )

    elif response_pattern == 2:
        return (
            base_prompt
            + f"""

## 回答方針（パターン2: 傾聴）
- 傾聴型で、ユーザーが気軽に話せるように質問してください
- 共感が第一：「〜してくれてありがとう」「〜という気持ち、すごくわかります」
- 評価しない・急がない：「〜すべき」「〜が悪い」は避け、ただ話を「受け止める」
- 安心・安全の場づくり：「ここでは〜しても大丈夫」「一人じゃないです」
- ポジティブもネガティブも尊重：「その報告うれしいです」「苦しい中でよく話してくれました」
- {limits['pattern2']}文字以下で回答してください"""
        )

    else:  # pattern 3
        return (
            base_prompt
            + f"""

## 回答方針（パターン3: 解決策提案・客観的視点）
- ユーザーが悩んで周りが見えなくなっている状況かもしれません
- 客観的で冷静な視点を入れてあげてください
- 客観的に、ユーザーの良さを見つけて褒めてください
- 解決を急がず、ユーザーが安心して話せる感覚を持たせてください
- 解決策の押し付けはせず、どんなことができそうか一緒に考える姿勢を持ってください
- {limits['pattern3']}文字以下で回答してください"""
        )


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
            "updated_at": datetime.now().isoformat(),
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
        memory_items=user_memory[user_info.user_id]["memory_items"],
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
        memory_items=user_data["memory_items"],
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_counselor(chat_message: ChatMessage):
    """Chat with AI counselor with long-term memory"""
    user_id = chat_message.user_id
    message = chat_message.message

    # ログ: リクエスト内容を表示
    logger.info("\n" + "=" * 80)
    logger.info("[CHAT REQUEST - RAW JSON]")
    logger.info(json.dumps({"user_id": user_id, "message": message}, indent=2, ensure_ascii=False))
    logger.info("=" * 80)

    if user_id not in conversations:
        conversations[user_id] = []

    # 回答パターンを判断
    response_pattern = analyze_response_pattern(message, conversations[user_id])
    logger.info("\n[RESPONSE PATTERN ANALYSIS]")
    logger.info(f"Response Pattern: {response_pattern}")
    logger.info("  - Pattern 1: 短い相槌（15文字以内）")
    logger.info("  - Pattern 2: 傾聴型・共感（100文字程度）")
    logger.info("  - Pattern 3: 解決策提案・客観的視点（200文字程度）")

    # LangChainベースの記憶システムから関連する記憶を検索
    relevant_memories = await memory_system.retrieve_relevant_memories(user_id, message, limit=10)

    # ★ ユーザー状態の分析（メタ推論ステップ）
    recent_conversations = conversations[user_id][-100:] if conversations[user_id] else []
    user_state = await analyze_user_state(
        user_id=user_id,
        user_message=message,
        recent_conversations=recent_conversations,
        relevant_memories=relevant_memories,
    )

    logger.info("\n[USER STATE ANALYSIS]")
    if user_state:
        logger.info(json.dumps(user_state, indent=2, ensure_ascii=False))
    else:
        logger.info("No state analysis available")

    # ★ RAG: 知識ベースから関連知識を検索
    relevant_knowledge = knowledge_base.search_knowledge(message, limit=3)

    # ★ ユーザープロファイルを取得して拡張プロファイルに統合
    user_profile = user_profile_system.get_profile(user_id)

    # 旧来のプロファイルがある場合は拡張プロファイルに同期
    if user_profile:
        extended_profile_system.sync_from_user_profile(user_id, user_profile)

    # 拡張プロファイルを取得（同期後なので必ず存在する）
    extended_profile = extended_profile_system.get_profile(user_id)

    # プロファイルがまだない場合は新規作成
    if not extended_profile:
        extended_profile = ExtendedUserProfile(user_id=user_id)
        extended_profile_system.create_or_update_profile(extended_profile)

    user_context = ""

    # ★ プロファイル情報の構築（拡張プロファイルを使用）
    profile_summary = "\n" + extended_profile_system.generate_profile_summary(user_id)

    # 従来のメモリシステムも維持（後方互換性）
    memory_summary = ""
    if user_id in user_memory:
        user_data = user_memory[user_id]
        if user_data.get("memory_items"):
            recent_memories = user_data["memory_items"][-10:]
            memory_summary = "\n\n最近の記憶（旧システム）:\n"
            for item in recent_memories:
                memory_summary += f"- {item['type']}: {item['content']}\n"

    # LangChainベースの関連記憶（時間減衰を考慮した重要度順）
    relevant_memory_summary = ""
    if relevant_memories:
        # 時間減衰を考慮した重要度で再ソート
        sorted_memories = sorted(
            relevant_memories, key=lambda m: m.get_current_importance(), reverse=True
        )

        relevant_memory_summary = (
            "\n\n現在の会話に関連する重要な記憶（時間減衰を考慮した重要度順）:\n"
        )
        for idx, memory in enumerate(sorted_memories[:5], 1):
            days_ago = (datetime.now() - memory.timestamp).days
            current_importance = memory.get_current_importance()
            time_info = f"{days_ago}日前" if days_ago > 0 else "今日"
            relevant_memory_summary += f"{idx}. [{memory.memory_type}] {memory.content}\n   (保存時: {memory.importance_score:.2f} → 現在: {current_importance:.2f}, {time_info})\n"

    # ★ 状態情報の追加（文脈パターン分析を含む）
    state_text = ""
    if user_state:
        contextual_info = ""
        if user_state.get("contextual_patterns"):
            patterns = user_state["contextual_patterns"]
            if patterns:
                contextual_info = "\n文脈パターン:\n"
                for _key, value in patterns.items():
                    contextual_info += f"  - {value}\n"

        state_text = f"""
推定される現在の状態:
- 気分(mood): {user_state.get('mood')}
- エネルギー(energy): {user_state.get('energy')}
- 不安(anxiety): {user_state.get('anxiety')}
- 主なテーマ: {', '.join(user_state.get('main_topics', []))}
- いま求めていそうなこと: {user_state.get('need')}
- このターンで優先したいモード: {', '.join(user_state.get('modes', []))}
- 状態コメント: {user_state.get('state_comment')}
{contextual_info}
"""

    # ★ RAG: 関連知識の要約を追加
    knowledge_summary = ""
    if relevant_knowledge:
        knowledge_summary = "\n\n関連する専門知識（参考情報）:\n"
        for idx, knowledge in enumerate(relevant_knowledge, 1):
            knowledge_summary += f"{idx}. 【{knowledge.title}】\n   {knowledge.content[:200]}...\n"

    user_context = f"""
     ユーザープロフィールに含まれる、嗜好、過去の出来事、感情や体調の傾向を積極的に参照し、一般論ではなく、そのユーザーに合わせた応答を行ってください。
{profile_summary}
{memory_summary}
{relevant_memory_summary}
{state_text}
{knowledge_summary}

"""

    # 会話履歴にユーザー名とAI名を反映
    user_display_name = (
        extended_profile.profile_settings.display_name if extended_profile else "ユーザー"
    )
    ai_name = extended_profile.profile_settings.ai_name if extended_profile else "カウンセラー"

    recent_conversations = conversations[user_id][-100:] if conversations[user_id] else []
    conversation_context = ""
    if recent_conversations:
        conversation_context = "\n過去の会話:\n"
        for conv in recent_conversations:
            conversation_context += (
                f"{user_display_name}: {conv['user_message']}\n{ai_name}: {conv['ai_response']}\n\n"
            )

    system_prompt = generate_system_prompt(conversation_context, response_pattern, extended_profile)

    # デバッグログ
    if extended_profile:
        logger.info("\n[EXTENDED PROFILE SETTINGS]")
        logger.info(f"  - AI Name: {extended_profile.profile_settings.ai_name}")
        logger.info(f"  - AI Personality: {extended_profile.profile_settings.ai_personality}")
        logger.info(f"  - Display Name: {extended_profile.profile_settings.display_name}")
        logger.info(
            f"  - Response Style: {extended_profile.profile_settings.response_length_style}"
        )

    logger.info("\n[SYSTEM PROMPT]")
    logger.info("-" * 80)
    logger.info(system_prompt)
    logger.info("-" * 80)

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
            # ユーザーのモデル設定を取得
            user_model_settings = model_settings_storage.get(
                user_id, {"model": "gpt-4.1-mini-2025-04-14", "temperature": 0.7, "max_tokens": 500}
            )

            # 会話履歴をmessages配列に追加
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_context},
            ]

            # 過去の会話をmessages配列に追加（最新100件）
            for conv in recent_conversations:
                messages.append({"role": "user", "content": conv["user_message"]})
                messages.append({"role": "assistant", "content": conv["ai_response"]})

            # 現在のユーザーメッセージを追加
            messages.append({"role": "user", "content": message})

            # OpenAI API リクエストのログ
            api_request = {
                "model": user_model_settings["model"],
                "messages": messages,
                "max_tokens": user_model_settings["max_tokens"],
                "temperature": user_model_settings["temperature"],
            }

            # メッセージ配列を表示
            logger.info("\n[Chat] Final prompt messages")
            logger.info(json.dumps(api_request["messages"], indent=2, ensure_ascii=False))

            # APIリクエストメタデータ
            logger.info("\n[OPENAI API REQUEST METADATA]")
            logger.info(
                json.dumps(
                    {
                        "model": api_request["model"],
                        "max_tokens": api_request["max_tokens"],
                        "temperature": api_request["temperature"],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )

            response = client.chat.completions.create(**api_request)
            ai_response = response.choices[0].message.content

            # OpenAI API レスポンスのログ
            logger.info("\n[OPENAI API RESPONSE]")
            logger.info(
                json.dumps(
                    {
                        "model": response.model,
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens,
                        },
                        "finish_reason": response.choices[0].finish_reason,
                        "response": ai_response,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )

        conversations[user_id].append(
            {
                "user_message": message,
                "ai_response": ai_response,
                "response_pattern": response_pattern,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # 旧システム：メモリアイテム抽出
        user_info_updated = await extract_user_info(user_id, message, ai_response)

        # ★ 新システム：プロファイルシステムで抽出・更新
        profile_updated = await user_profile_system.extract_and_update_profile(
            user_id=user_id, user_message=message, ai_response=ai_response
        )

        # ★ プロファイル更新後に拡張プロファイルに同期
        if profile_updated:
            updated_user_profile = user_profile_system.get_profile(user_id)
            if updated_user_profile:
                extended_profile_system.sync_from_user_profile(user_id, updated_user_profile)

        user_info_updated = user_info_updated or profile_updated

        # 最終レスポンスのログ
        logger.info("\n[FINAL RESPONSE TO CLIENT]")
        response_data = {
            "response": ai_response,
            "response_type": response_pattern,
            "user_info_updated": user_info_updated,
        }
        logger.info(json.dumps(response_data, indent=2, ensure_ascii=False))
        logger.info("=" * 80 + "\n")

        return ChatResponse(
            response=ai_response,
            response_type=response_pattern,
            user_info_updated=user_info_updated,
        )

    except Exception:
        # Fallback to mock response if OpenAI API fails
        if response_pattern == 1:
            ai_response = "はい。"
        elif response_pattern == 2:
            ai_response = "お話しいただき、ありがとうございます。その気持ち、よくわかります。"
        else:
            ai_response = "申し訳ございませんが、現在システムに問題が発生しております。お話しいただき、ありがとうございます。"

        conversations[user_id].append(
            {
                "user_message": message,
                "ai_response": ai_response,
                "response_pattern": response_pattern,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # 旧システム：メモリアイテム抽出
        user_info_updated = await extract_user_info(user_id, message, ai_response)

        # ★ 新システム：プロファイルシステムで抽出・更新
        profile_updated = await user_profile_system.extract_and_update_profile(
            user_id=user_id, user_message=message, ai_response=ai_response
        )

        # ★ プロファイル更新後に拡張プロファイルに同期
        if profile_updated:
            updated_user_profile = user_profile_system.get_profile(user_id)
            if updated_user_profile:
                extended_profile_system.sync_from_user_profile(user_id, updated_user_profile)

        user_info_updated = user_info_updated or profile_updated

        return ChatResponse(
            response=ai_response,
            response_type=response_pattern,
            user_info_updated=user_info_updated,
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
            "updated_at": datetime.now().isoformat(),
        }

    try:
        if not os.getenv("OPENAI_API_KEY"):
            # モック抽出：基本的なキーワードベースの抽出
            extracted_info = {}
            message_lower = user_message.lower()

            # メンタルヘルスに特化した抽出パターン
            if any(
                word in message_lower
                for word in ["不安", "心配", "悩み", "困って", "辛い", "苦しい"]
            ):
                extracted_info["concerns"] = user_message
            if any(
                word in message_lower for word in ["目標", "やりたい", "頑張り", "復職", "改善"]
            ):
                extracted_info["goals"] = user_message
            if any(
                word in message_lower
                for word in ["眠れない", "食欲", "体調", "症状", "痛み", "疲れ"]
            ):
                extracted_info["symptoms"] = user_message
            if any(
                word in message_lower
                for word in ["ストレス", "プレッシャー", "原因", "きっかけ", "職場"]
            ):
                extracted_info["triggers"] = user_message
            if any(
                word in message_lower for word in ["散歩", "リラックス", "気分転換", "対処", "趣味"]
            ):
                extracted_info["coping_methods"] = user_message
            if any(word in message_lower for word in ["家族", "友達", "サポート", "支え", "相談"]):
                extracted_info["support_system"] = user_message
            if any(word in message_lower for word in ["薬", "通院", "病院", "治療", "診察"]):
                extracted_info["medication"] = user_message
            if any(
                word in message_lower for word in ["会社", "職場", "休職", "復職", "仕事", "上司"]
            ):
                extracted_info["work_status"] = user_message
            if any(
                word in message_lower for word in ["朝", "夜", "生活", "日常", "ルーティン", "時間"]
            ):
                extracted_info["daily_routine"] = user_message
            if any(
                word in message_lower
                for word in ["気持ち", "感情", "落ち込み", "嬉しい", "悲しい", "怒り"]
            ):
                extracted_info["emotional_state"] = user_message

            logger.debug(f"Mock extraction result: {extracted_info}")
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
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたはメンタルヘルス情報を正確に抽出するAIアシスタントです。JSONフォーマットでのみ回答してください。",
                    },
                    {"role": "user", "content": extraction_prompt},
                ],
                max_tokens=500,
                temperature=0.1,
            )

            extracted_text = response.choices[0].message.content.strip()

            if extracted_text.startswith("```json"):
                extracted_text = extracted_text[7:-3].strip()
            elif extracted_text.startswith("```"):
                extracted_text = extracted_text[3:-3].strip()

            try:
                extracted_info = json.loads(extracted_text)
            except json.JSONDecodeError:
                return False

        current_data = user_memory[user_id]

        # メンタルヘルス関連情報の抽出と保存
        mental_health_fields = [
            "concerns",
            "goals",
            "personality",
            "experiences",
            "symptoms",
            "triggers",
            "coping_methods",
            "support_system",
            "medication",
            "work_status",
            "daily_routine",
            "emotional_state",
        ]

        other_fields = ["age", "location", "family"]

        for field in mental_health_fields + other_fields:
            if extracted_info.get(field):
                field_value = extracted_info[field].strip()
                if field_value and len(field_value) > 3:  # より意味のある情報のみ保存
                    existing_items = [
                        item["content"]
                        for item in current_data["memory_items"]
                        if item["type"] == field
                    ]

                    # 重複チェック（完全一致および類似チェック）
                    is_duplicate = any(
                        field_value.lower().strip() == existing.lower().strip()
                        or (len(field_value) > 10 and field_value.lower() in existing.lower())
                        for existing in existing_items
                    )

                    if not is_duplicate:
                        memory_item = {
                            "type": field,
                            "content": field_value,
                            "timestamp": datetime.now().isoformat(),
                            "source": "conversation",
                        }
                        current_data["memory_items"].append(memory_item)
                        updated = True
                        logger.debug(f"Added memory item: {field} = {field_value}")

                        # LangChain memory_systemにも保存
                        await memory_system.store_memory(
                            user_id=user_id,
                            content=field_value,
                            memory_type=field,
                            metadata={
                                "timestamp": datetime.now().isoformat(),
                                "source": "conversation",
                            },
                        )

        # 基本情報の更新
        if extracted_info.get("name") and extracted_info["name"] != current_data.get("name"):
            current_data["name"] = extracted_info["name"]
            memory_item = {
                "type": "name",
                "content": extracted_info["name"],
                "timestamp": datetime.now().isoformat(),
                "source": "conversation",
            }
            current_data["memory_items"].append(memory_item)
            updated = True

            # LangChain memory_systemにも保存
            await memory_system.store_memory(
                user_id=user_id,
                content=extracted_info["name"],
                memory_type="name",
                metadata={"timestamp": datetime.now().isoformat(), "source": "conversation"},
            )

        if extracted_info.get("job") and extracted_info["job"] != current_data.get("job"):
            current_data["job"] = extracted_info["job"]
            memory_item = {
                "type": "job",
                "content": extracted_info["job"],
                "timestamp": datetime.now().isoformat(),
                "source": "conversation",
            }
            current_data["memory_items"].append(memory_item)
            updated = True

            # LangChain memory_systemにも保存
            await memory_system.store_memory(
                user_id=user_id,
                content=extracted_info["job"],
                memory_type="job",
                metadata={"timestamp": datetime.now().isoformat(), "source": "conversation"},
            )

        if extracted_info.get("hobbies") and isinstance(extracted_info["hobbies"], list):
            new_hobbies = [
                h for h in extracted_info["hobbies"] if h and h not in current_data["hobbies"]
            ]
            if new_hobbies:
                current_data["hobbies"].extend(new_hobbies)
                for hobby in new_hobbies:
                    memory_item = {
                        "type": "hobby",
                        "content": hobby,
                        "timestamp": datetime.now().isoformat(),
                        "source": "conversation",
                    }
                    current_data["memory_items"].append(memory_item)

                    # LangChain memory_systemにも保存
                    await memory_system.store_memory(
                        user_id=user_id,
                        content=hobby,
                        memory_type="hobby",
                        metadata={
                            "timestamp": datetime.now().isoformat(),
                            "source": "conversation",
                        },
                    )
                updated = True

        # メモリ制限（100個まで）
        if len(current_data["memory_items"]) > 100:
            items_to_remove = len(current_data["memory_items"]) - 100
            current_data["memory_items"] = current_data["memory_items"][items_to_remove:]

        if updated:
            current_data["updated_at"] = datetime.now().isoformat()

        return updated

    except Exception as e:
        logger.error(f"Error in extract_user_info: {e}")
        return False


@app.get("/api/conversations/{user_id}")
async def get_conversation_history(user_id: str):
    """Get conversation history for a user"""
    if user_id not in conversations:
        return {"conversations": []}

    return {"conversations": conversations[user_id]}


@app.get("/api/export-conversations/{user_id}")
async def export_conversations_csv(user_id: str):
    """Export conversation history as CSV in index, role, content, timestamp, response_pattern format"""
    if user_id not in conversations:
        raise HTTPException(status_code=404, detail="No conversations found for user")

    output = StringIO()
    writer = csv.writer(output)

    # ヘッダー行
    writer.writerow(["index", "role", "content", "timestamp", "response_pattern"])

    index = 1
    for conv in conversations[user_id]:
        timestamp = conv.get("timestamp", "")
        response_pattern = conv.get("response_pattern", "")

        # ユーザーメッセージ（改行を\nに置換）
        user_message = conv["user_message"].replace("\n", "\\n").replace("\r", "")
        writer.writerow([index, "user", user_message, timestamp, ""])
        index += 1

        # AIレスポンス（改行を\nに置換）
        ai_response = conv["ai_response"].replace("\n", "\\n").replace("\r", "")
        writer.writerow([index, "assistant", ai_response, timestamp, response_pattern])
        index += 1

    csv_content = output.getvalue()
    output.close()

    return {
        "csv_data": csv_content,
        "filename": f"conversations_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    }


@app.get("/api/export-system-prompt/{user_id}")
async def export_system_prompt_csv(user_id: str):
    """Export system prompt settings as CSV"""
    profile = extended_profile_system.get_profile(user_id)

    if not profile:
        # プロファイルが存在しない場合は新規作成
        from .extended_profile import ExtendedUserProfile

        profile = ExtendedUserProfile(user_id=user_id)
        extended_profile_system.create_or_update_profile(profile)

    output = StringIO()
    writer = csv.writer(output)

    # ヘッダー行
    writer.writerow(["setting", "value"])

    # プロファイル設定
    settings = profile.profile_settings
    writer.writerow(["display_name", settings.display_name])
    writer.writerow(["ai_name", settings.ai_name])
    writer.writerow(["ai_personality", settings.ai_personality])
    writer.writerow(["ai_expectation", settings.ai_expectation])
    writer.writerow(["response_length_style", settings.response_length_style])

    csv_content = output.getvalue()
    output.close()

    return {
        "csv_data": csv_content,
        "filename": f"system_prompt_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    }


@app.get("/api/export-prompt-debug/{user_id}")
async def export_prompt_debug(user_id: str):
    """Export full system prompt and context for debugging purposes"""
    try:
        logger.info(f"Starting export-prompt-debug for user_id: {user_id}")

        # 拡張プロファイルを取得（存在しない場合は新規作成）
        extended_profile = extended_profile_system.get_profile(user_id)

        if not extended_profile:
            logger.info(f"Profile not found for {user_id}, creating new profile")
            # プロファイルが存在しない場合は新規作成
            from .extended_profile import ExtendedUserProfile

            extended_profile = ExtendedUserProfile(user_id=user_id)
            extended_profile_system.create_or_update_profile(extended_profile)

        # 最近の会話履歴を取得
        recent_conversations = conversations[user_id][-100:] if user_id in conversations else []

        # LangChainベースの記憶システムから関連する記憶を検索（最新のメッセージがあれば）
        relevant_memories = []
        if recent_conversations:
            last_message = recent_conversations[-1].get("user_message", "")
            relevant_memories = await memory_system.retrieve_relevant_memories(
                user_id, last_message, limit=10
            )

        # プロファイル情報の構築
        profile_summary = extended_profile_system.generate_profile_summary(user_id)

        # メモリシステム（旧システム）
        memory_summary = ""
        if user_id in user_memory:
            user_data = user_memory[user_id]
            if user_data.get("memory_items"):
                recent_memories_old = user_data["memory_items"][-10:]
                memory_summary = "\n\n最近の記憶（旧システム）:\n"
                for item in recent_memories_old:
                    memory_summary += f"- {item['type']}: {item['content']}\n"

        # LangChainベースの関連記憶
        relevant_memory_summary = ""
        if relevant_memories:
            sorted_memories = sorted(
                relevant_memories, key=lambda m: m.get_current_importance(), reverse=True
            )
            relevant_memory_summary = (
                "\n\n現在の会話に関連する重要な記憶（時間減衰を考慮した重要度順）:\n"
            )
            for idx, memory in enumerate(sorted_memories[:5], 1):
                days_ago = (datetime.now() - memory.timestamp).days
                current_importance = memory.get_current_importance()
                time_info = f"{days_ago}日前" if days_ago > 0 else "今日"
                relevant_memory_summary += f"{idx}. [{memory.memory_type}] {memory.content}\n   (保存時: {memory.importance_score:.2f} → 現在: {current_importance:.2f}, {time_info})\n"

        # 状態情報（最新があれば）
        state_text = ""
        if user_id in user_states:
            user_state = user_states[user_id]
            contextual_info = ""
            if user_state.get("contextual_patterns"):
                patterns = user_state["contextual_patterns"]
                if patterns:
                    contextual_info = "\n文脈パターン:\n"
                    for _key, value in patterns.items():
                        contextual_info += f"  - {value}\n"

            state_text = f"""
推定される現在の状態:
- 気分(mood): {user_state.get('mood')}
- エネルギー(energy): {user_state.get('energy')}
- 不安(anxiety): {user_state.get('anxiety')}
- 主なテーマ: {', '.join(user_state.get('main_topics', []))}
- いま求めていそうなこと: {user_state.get('need')}
- このターンで優先したいモード: {', '.join(user_state.get('modes', []))}
- 状態コメント: {user_state.get('state_comment')}
{contextual_info}
"""

        # ユーザーコンテキスト
        user_context = f"""
ユーザープロフィールに含まれる、嗜好、過去の出来事、感情や体調の傾向を積極的に参照し、一般論ではなく、そのユーザーに合わせた応答を行ってください。
{profile_summary}
{memory_summary}
{relevant_memory_summary}
{state_text}
"""

        # 会話履歴コンテキスト
        user_display_name = (
            extended_profile.profile_settings.display_name if extended_profile else "ユーザー"
        )
        ai_name = extended_profile.profile_settings.ai_name if extended_profile else "カウンセラー"

        conversation_context = ""
        if recent_conversations:
            conversation_context = "\n過去の会話:\n"
            for conv in recent_conversations:
                conversation_context += f"{user_display_name}: {conv['user_message']}\n{ai_name}: {conv['ai_response']}\n\n"

        # システムプロンプトを3つのパターンで生成
        logger.info("Generating system prompts...")
        system_prompt_pattern1 = generate_system_prompt(conversation_context, 1, extended_profile)
        system_prompt_pattern2 = generate_system_prompt(conversation_context, 2, extended_profile)
        system_prompt_pattern3 = generate_system_prompt(conversation_context, 3, extended_profile)

        # CSV形式で出力
        logger.info("Creating CSV output...")
        output = StringIO()
        writer = csv.writer(output)

        # ヘッダー行
        writer.writerow(["section", "content"])

        # プロファイル設定
        try:
            if hasattr(extended_profile.profile_settings, "to_dict"):
                profile_settings_dict = extended_profile.profile_settings.to_dict()
            else:
                # Fallback: dataclassの場合
                from dataclasses import asdict

                profile_settings_dict = asdict(extended_profile.profile_settings)
            writer.writerow(
                ["profile_settings", json.dumps(profile_settings_dict, ensure_ascii=False)]
            )
        except Exception as e:
            logger.error(f"Error serializing profile_settings: {e}")
            writer.writerow(["profile_settings", f"Error: {str(e)}"])

        # カスタムシステムプロンプト（JSONファイルから直接読み取り）
        custom_prompt = None
        try:
            # 拡張プロファイルのJSONファイルパスを取得
            from app.config import EXTENDED_PROFILES_JSON_PATH

            profiles_path = Path(EXTENDED_PROFILES_JSON_PATH)

            if profiles_path.exists():
                with open(profiles_path, encoding="utf-8") as f:
                    all_profiles = json.load(f)
                    if user_id in all_profiles:
                        profile_data = all_profiles[user_id]
                        # profile_settingsからcustom_system_promptを取得
                        if "profile_settings" in profile_data and isinstance(
                            profile_data["profile_settings"], dict
                        ):
                            custom_prompt = profile_data["profile_settings"].get(
                                "custom_system_prompt"
                            )
        except Exception as e:
            logger.warning(f"カスタムプロンプトの読み取りに失敗: {e}")

        if custom_prompt:
            writer.writerow(["custom_system_prompt", custom_prompt.replace("\n", "\\n")])
            writer.writerow(["using_custom_prompt", "true"])
        else:
            writer.writerow(["custom_system_prompt", ""])
            writer.writerow(["using_custom_prompt", "false"])

        # ユーザーコンテキスト
        writer.writerow(["user_context", user_context.replace("\n", "\\n")])

        # 会話履歴コンテキスト
        writer.writerow(["conversation_context", conversation_context.replace("\n", "\\n")])

        # システムプロンプト（パターン1）
        writer.writerow(["system_prompt_pattern1", system_prompt_pattern1.replace("\n", "\\n")])

        # システムプロンプト（パターン2）
        writer.writerow(["system_prompt_pattern2", system_prompt_pattern2.replace("\n", "\\n")])

        # システムプロンプト（パターン3）
        writer.writerow(["system_prompt_pattern3", system_prompt_pattern3.replace("\n", "\\n")])

        # モデル設定
        user_model_settings = model_settings_storage.get(
            user_id, {"model": "gpt-4.1-mini-2025-04-14", "temperature": 0.7, "max_tokens": 500}
        )
        writer.writerow(["model_settings", json.dumps(user_model_settings, ensure_ascii=False)])

        # プロファイル詳細（JSON形式）
        try:
            if hasattr(extended_profile, "to_dict"):
                profile_full_dict = extended_profile.to_dict()
            else:
                from dataclasses import asdict

                profile_full_dict = asdict(extended_profile)
            writer.writerow(["profile_full", json.dumps(profile_full_dict, ensure_ascii=False)])
        except Exception as e:
            logger.error(f"Error serializing profile_full: {e}")
            writer.writerow(["profile_full", f"Error: {str(e)}"])

        csv_content = output.getvalue()
        output.close()

        logger.info(f"CSV export completed successfully for {user_id}")

        return {
            "csv_data": csv_content,
            "filename": f"prompt_debug_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        }

    except Exception as e:
        logger.error(f"Error in export_prompt_debug for {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.get("/api/export-profile/{user_id}")
async def export_profile_csv(user_id: str):
    """Export user profile as JSON"""
    profile = extended_profile_system.get_profile(user_id)

    if not profile:
        # プロファイルが存在しない場合は新規作成
        from .extended_profile import ExtendedUserProfile

        profile = ExtendedUserProfile(user_id=user_id)
        extended_profile_system.create_or_update_profile(profile)

    # 拡張プロファイルを新しいJSON形式にマッピング
    # recent_concerns を work と mental に分類
    recent_concerns_dict = {}
    for category, concerns in profile.recent_concerns.items():
        if concerns and len(concerns) > 0:
            # 最初の懸念事項を文字列として追加
            recent_concerns_dict[category] = (
                concerns[0].summary if hasattr(concerns[0], "summary") else str(concerns[0])
            )

    export_data = {
        "user_id": profile.user_id,
        "profile_settings": {
            "display_name": profile.profile_settings.display_name,
            "ai_name": profile.profile_settings.ai_name,
            "ai_personality": profile.profile_settings.ai_personality,
            "ai_expectation": profile.profile_settings.ai_expectation,
            "response_length_style": profile.profile_settings.response_length_style,
            "profile_initialized_at": profile.profile_settings.profile_initialized_at,
        },
        "general_profile": {
            "hobbies": profile.general_profile.hobbies if profile.general_profile.hobbies else [],
            "occupation": profile.general_profile.occupation,
            "location": profile.general_profile.location,
            "age": profile.general_profile.age,
            "family": profile.general_profile.family,
        },
        "mental_profile": {
            "recent_medication_change": profile.mental_profile.recent_medication_change,
            "current_mental_state": profile.mental_profile.current_mental_state,
            "symptoms": profile.mental_profile.symptoms if profile.mental_profile.symptoms else [],
            "triggers": profile.mental_profile.triggers if profile.mental_profile.triggers else [],
            "coping_methods": profile.mental_profile.coping_methods
            if profile.mental_profile.coping_methods
            else [],
            "support_system": profile.mental_profile.support_system
            if profile.mental_profile.support_system
            else [],
        },
        "favorites": {
            "favorite_food": profile.favorites.favorite_food,
            "favorite_animal": profile.favorites.favorite_animal,
            "beverage": profile.favorites.drink,
            "extra": profile.favorites.extra if profile.favorites.extra else {},
        },
        "important_memories": [mem.text for mem in profile.important_memories]
        if profile.important_memories
        else [],
        "recent_concerns": recent_concerns_dict,
        "goals": [goal.goal for goal in profile.goals if goal.status == "active"]
        if profile.goals
        else [],
        "relationships": profile.relationships if profile.relationships else {},
        "environments": profile.environments if profile.environments else {},
        "mood_trend": [
            {"date": mood.date, "mood": mood.mood, "intensity": mood.intensity}
            for mood in profile.mood_trend[-20:]
        ]
        if profile.mood_trend
        else [],
        "user_tendency": {
            "dominant_mood": profile.user_tendency.dominant_mood,
            "counts": profile.user_tendency.counts if profile.user_tendency.counts else {},
            "recent_intensity": profile.user_tendency.recent_intensity,
            "last_observed": profile.user_tendency.last_observed,
            "insight": profile.user_tendency.insight,
            "time_patterns": profile.user_tendency.time_patterns
            if profile.user_tendency.time_patterns
            else [],
        },
    }

    # JSON形式でエクスポート
    json_content = json.dumps(export_data, ensure_ascii=False, indent=2)

    return {
        "csv_data": json_content,
        "filename": f"profile_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    }


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
        "recent_patterns": [conv.get("response_pattern", 2) for conv in convs[-10:]],
    }


@app.get("/api/memories/{user_id}")
async def get_user_memories(user_id: str):
    """Get LangChain-based user memories with importance scores"""
    if user_id not in memory_system.memory_items:
        return {
            "user_id": user_id,
            "memories": [],
            "stats": memory_system.get_memory_stats(user_id),
        }

    memories = memory_system.memory_items[user_id]

    # 時間減衰を考慮した現在の重要度でソートして返す
    sorted_memories = sorted(memories, key=lambda m: m.get_current_importance(), reverse=True)

    # MemoryItemをJSON形式に変換
    memory_list = []
    for memory in sorted_memories:
        days_ago = (datetime.now() - memory.timestamp).days
        current_importance = memory.get_current_importance()

        memory_list.append(
            {
                "id": memory.id,
                "content": memory.content,
                "memory_type": memory.memory_type,
                "importance_score_original": memory.importance_score,  # 保存時の重要度
                "importance_score_current": current_importance,  # 時間減衰後の現在の重要度
                "days_ago": days_ago,
                "timestamp": memory.timestamp.isoformat(),
                "metadata": memory.metadata,
            }
        )

    return {
        "user_id": user_id,
        "memories": memory_list,
        "stats": memory_system.get_memory_stats(user_id),
    }


@app.get("/api/knowledge")
async def get_all_knowledge(category: str | None = None):
    """全知識ベースを取得"""
    items = knowledge_base.get_all_knowledge(category=category)

    knowledge_list = []
    for item in items:
        knowledge_list.append(
            {
                "id": item.id,
                "category": item.category,
                "title": item.title,
                "content": item.content,
                "tags": item.tags,
                "relevance_keywords": item.relevance_keywords,
                "created_at": item.created_at,
            }
        )

    return {"knowledge": knowledge_list, "stats": knowledge_base.get_stats()}


@app.get("/api/knowledge/search")
async def search_knowledge(query: str, category: str | None = None, limit: int = 5):
    """知識を検索"""
    items = knowledge_base.search_knowledge(query, category=category, limit=limit)

    knowledge_list = []
    for item in items:
        knowledge_list.append(
            {
                "id": item.id,
                "category": item.category,
                "title": item.title,
                "content": item.content,
                "tags": item.tags,
                "relevance_keywords": item.relevance_keywords,
                "created_at": item.created_at,
            }
        )

    return {"query": query, "knowledge": knowledge_list}


@app.get("/api/profile/{user_id}")
async def get_user_profile(user_id: str):
    """ユーザープロファイルを取得"""
    profile = user_profile_system.get_profile(user_id)

    if not profile:
        # プロファイルが存在しない場合は新規作成
        profile = UserProfile(user_id=user_id)
        user_profile_system.create_or_update_profile(profile)

    return {"user_id": user_id, "profile": profile.to_dict()}


@app.get("/api/profile/{user_id}/summary")
async def get_user_profile_summary(user_id: str):
    """ユーザープロファイルの要約を取得"""
    summary = user_profile_system.get_profile_summary(user_id)

    return {"user_id": user_id, "summary": summary}


@app.delete("/api/profile/{user_id}")
async def delete_user_profile(user_id: str):
    """ユーザープロファイルを削除"""
    deleted = user_profile_system.delete_profile(user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="User profile not found")

    return {"message": "User profile deleted successfully"}


@app.get("/api/state/{user_id}")
async def get_user_state(user_id: str):
    """ユーザーの現在の状態を取得"""
    if user_id not in user_states:
        raise HTTPException(status_code=404, detail="User state not found")

    return {"user_id": user_id, "state": user_states[user_id]}


# ============================================
# 拡張プロファイルAPI (JSON形式)
# ============================================


@app.get("/api/extended-profile/{user_id}")
async def get_extended_profile(user_id: str):
    """拡張プロファイルをJSON形式で取得"""
    profile = extended_profile_system.get_profile(user_id)

    if not profile:
        # プロファイルが存在しない場合は新規作成
        profile = ExtendedUserProfile(user_id=user_id)
        extended_profile_system.create_or_update_profile(profile)

    return {"user_id": user_id, "profile": profile.to_dict()}


@app.post("/api/extended-profile/{user_id}")
async def update_extended_profile(user_id: str, profile_data: dict[str, Any]):
    """拡張プロファイルをJSON形式で更新"""
    try:
        profile = ExtendedUserProfile.from_dict(user_id, profile_data)
        extended_profile_system.create_or_update_profile(profile)

        return {"user_id": user_id, "updated": True, "profile": profile.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid profile data: {str(e)}")


@app.delete("/api/extended-profile/{user_id}")
async def delete_extended_profile(user_id: str):
    """拡張プロファイルを削除"""
    deleted = extended_profile_system.delete_profile(user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Extended profile not found")

    return {"message": "Extended profile deleted successfully"}


@app.get("/api/extended-profile/{user_id}/summary")
async def get_extended_profile_summary(user_id: str):
    """拡張プロファイルの要約を取得（プロンプト用）"""
    summary = extended_profile_system.generate_profile_summary(user_id)

    return {"user_id": user_id, "summary": summary}


@app.get("/api/system-prompt/default")
async def get_default_system_prompt():
    """デフォルトのシステムプロンプトテンプレートを取得"""
    # デフォルトのシステムプロンプトを生成（変数プレースホルダー付き）
    default_prompt = """あなたは{ai_name}という名前のAIメンタルカウンセラーです。
あなたの性格・役割は「{ai_personality}」です。

## あなたのビジョンと基本スタンス
「メンタルバリアフリー」というビジョンを持っています。
- 不安や悩みを抱える人の感情も、それが個性であると捉えてください
- 無理に更生させようとせず、あなた自身がユーザーに合わせて変わってください
- ユーザーにとって「ここでは自分らしくいられる」「居心地が良い」場所を提供してください

## 会話モード
user_context内には「このターンで優先したいモード」が含まれます。
modesに含まれるものを優先して使ってください：

- empathy: 共感・受容を前面に出し、「わかってもらえた感」を最優先にする
- emotion_labeling: ユーザーの感情に名前をつけてあげる（不安、悲しみ、怒り、戸惑い など）
- problem_sorting: 状況を一緒に整理し、「何が起きているか」を一緒に言語化する
- small_action: 今日〜数日のあいだにできそうな、負担の小さい行動を一緒に考える
- psychoeducation: 必要に応じて、メンタルヘルスに関する情報や考え方のヒントを優しく共有する

必ずしも全部を使う必要はありません。modesに含まれる2つを中心にしてください。

## 制約条件
- うつ病で休職中のユーザや復職を目指している方、その他メンタルヘルスに関する方を主な対象とします
- 医療行為や診断は行わず、緊急事態では専門家への相談を促します
- 対面での会話のように自然で人間らしいバリエーションに富んだ会話を目指します
- 記憶しているユーザの情報を会話の中で自然に活用してください
- 適度に改行を入れて読みやすくしてください

{user_context}

## 回答方針
response_pattern={response_pattern}に応じて以下のように応答してください：
- pattern=1: 「はい」「なるほど」など短い相槌のみ（15文字以内）
- pattern=2: 傾聴型で共感を示す応答（100文字程度）
- pattern=3: 解決策提案・客観的視点を含む応答（200文字程度）"""

    return {
        "default_prompt": default_prompt,
        "variables": [
            "{ai_name}",
            "{ai_personality}",
            "{user_context}",
            "{conversation_context}",
            "{response_pattern}",
        ],
        "description": "システムプロンプトテンプレート。変数は実行時に自動置換されます。",
    }


# モデル設定保存用のディクショナリ（ユーザーごと）
model_settings_storage: dict[str, dict[str, Any]] = {}


@app.get("/api/model-settings/{user_id}")
async def get_model_settings(user_id: str):
    """ユーザーのGPTモデル設定を取得"""
    if user_id in model_settings_storage:
        return model_settings_storage[user_id]

    # デフォルト設定
    return {"model": "gpt-4.1-mini-2025-04-14", "temperature": 0.7, "max_tokens": 500}


@app.post("/api/model-settings/{user_id}")
async def update_model_settings(user_id: str, settings: dict[str, Any]):
    """ユーザーのGPTモデル設定を更新"""
    model_settings_storage[user_id] = {
        "model": settings.get("model", "gpt-4.1-mini-2025-04-14"),
        "temperature": settings.get("temperature", 0.7),
        "max_tokens": settings.get("max_tokens", 500),
    }

    return {"status": "success", "settings": model_settings_storage[user_id]}
