import os

import gradio as gr
import requests
import boto3
from dotenv import load_dotenv


assert load_dotenv(), "環境変数の読み込みに失敗しました"

# === 設定(デプロイ後の値を入力)===
API_URL = os.environ["API_URL"]
USER_POOL_CLIENT_ID = os.environ["USER_POOL_CLIENT_ID"]
REGION = os.environ["REGION"]

# グローバル状態
class AppState:
    id_token = None
    conversation_id = None
    username = None

state = AppState()


def login(username, password):
    """Cognitoでログイン"""
    client = boto3.client('cognito-idp', region_name=REGION)

    try:
        response = client.initiate_auth(
            ClientId=USER_POOL_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        state.id_token = response['AuthenticationResult']['IdToken']
        state.username = username

        # ログイン成功時に会話一覧を取得
        dropdown_update, conversations_text = get_conversations()

        return (
            f"✅ ログイン成功: {username}",
            gr.update(visible=False),
            gr.update(visible=True),
            dropdown_update,
            conversations_text
        )
    except Exception as e:
        return (
            f"❌ ログイン失敗: {str(e)}",
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(),
            ""
        )


def chat(message, history):
    """チャット処理"""
    if not state.id_token:
        return "⚠️ 先にログインしてください"
    
    try:
        body = {"message": message}
        if state.conversation_id:
            body["conversationId"] = state.conversation_id
        
        response = requests.post(
            f"{API_URL}/chat",
            headers={
                "Authorization": f"Bearer {state.id_token}",
                "Content-Type": "application/json"
            },
            json=body
        )

        if response.status_code != 200:
            return f"❌ エラー: {response.text}"

        data = response.json()
        state.conversation_id = data.get("conversationId")
        return data["response"]
        
    except Exception as e:
        return f"❌ エラー: {str(e)}"


def new_conversation():
    """新規会話を開始"""
    state.conversation_id = None
    return [], "✅ 新しい会話を開始しました"


def get_conversations():
    """会話一覧を取得してドロップダウン用のリストを返す"""
    if not state.id_token:
        return gr.update(choices=[], value=None), "⚠️ 先にログインしてください"

    try:
        response = requests.get(
            f"{API_URL}/conversations",
            headers={"Authorization": f"Bearer {state.id_token}"}
        )

        data = response.json()
        conversations = data.get("conversations", [])

        if not conversations:
            return gr.update(choices=[], value=None), "会話履歴がありません"

        # ドロップダウン用の選択肢を作成 (表示名, ID)
        choices = []
        for conv in conversations:
            label = f"{conv['title']} ({conv['messageCount']}件)"
            choices.append((label, conv['conversationId']))

        result = "## 📝 会話一覧\n\n"
        for conv in conversations:
            result += f"- **{conv['title']}** (メッセージ数: {conv['messageCount']})\n"

        return gr.update(choices=choices, value=None), result

    except Exception as e:
        return gr.update(choices=[], value=None), f"❌ エラー: {str(e)}"


def load_conversation(conversation_id):
    """選択した会話のメッセージ履歴を読み込む"""
    if not conversation_id:
        return [], "会話を選択してください"

    if not state.id_token:
        return [], "⚠️ 先にログインしてください"

    try:
        response = requests.get(
            f"{API_URL}/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {state.id_token}"}
        )

        if response.status_code == 404:
            return [], "❌ 会話が見つかりません"

        if response.status_code != 200:
            return [], f"❌ エラー: {response.text}"

        data = response.json()
        messages = data.get("messages", [])

        # タイムスタンプでソート（古い順）
        messages.sort(key=lambda x: x['timestamp'])

        # Gradio 6.0の辞書形式に変換
        chat_history = []
        for msg in messages:
            chat_history.append({
                "role": msg['role'],
                "content": msg['content']
            })

        state.conversation_id = conversation_id
        return chat_history, f"✅ 会話を読み込みました (ID: {conversation_id[:8]}...)"

    except Exception as e:
        return [], f"❌ エラー: {str(e)}"


def delete_conversation(conversation_id):
    """会話を削除する"""
    if not conversation_id:
        return gr.update(), [], "⚠️ 削除する会話を選択してください", ""

    if not state.id_token:
        return gr.update(), [], "⚠️ 先にログインしてください", ""

    try:
        response = requests.delete(
            f"{API_URL}/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {state.id_token}"}
        )

        if response.status_code == 404:
            return gr.update(), [], "❌ 会話が見つかりません", ""

        if response.status_code != 200:
            return gr.update(), [], f"❌ エラー: {response.text}", ""

        # 現在の会話が削除された場合はリセット
        if state.conversation_id == conversation_id:
            state.conversation_id = None

        # 会話一覧を更新
        dropdown_update, conversations_text = get_conversations()
        return dropdown_update, [], "✅ 会話を削除しました", conversations_text

    except Exception as e:
        return gr.update(), [], f"❌ エラー: {str(e)}", ""


def logout():
    """ログアウト"""
    state.id_token = None
    state.conversation_id = None
    state.username = None
    return "ログアウトしました", gr.update(visible=True), gr.update(visible=False)


# === カスタムCSS ===
custom_css = """
/* ========== ライトモードのみ ========== */
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f7f7f8;
    --bg-sidebar: #202123;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --text-sidebar: #ececf1;
    --text-sidebar-muted: #8e8ea0;
    --border-color: #e5e5e5;
    --border-sidebar: #565869;
    --btn-sidebar-bg: #343541;
    --btn-sidebar-hover: #40414f;
    --input-bg: #ffffff;
    --accent: #10a37f;
    --accent-hover: #1a7f64;
}

/* 全体のスタイル */
.gradio-container {
    max-width: 1200px !important;
    margin: auto !important;
    width: 100% !important;
}

/* チャットセクションの幅を固定 */
.chat-section-container {
    max-width: 1200px !important;
    margin: auto !important;
}

/* ヘッダー */
.header-container {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    color: white;
    text-align: center;
}

.header-container h1 {
    color: white !important;
    margin-bottom: 0.25rem;
    font-size: 1.5rem;
}

.header-container p {
    color: rgba(255,255,255,0.85) !important;
    margin: 0;
    font-size: 0.875rem;
}

/* ログインカード */
.login-card {
    background: var(--bg-primary) !important;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    max-width: 400px;
    margin: 2rem auto;
    border: 1px solid var(--border-color) !important;
}

.login-card h2 {
    color: var(--text-primary) !important;
}

.login-card label, .login-card span, .login-card p {
    color: var(--text-primary) !important;
}

.login-card input {
    background: var(--input-bg) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-color) !important;
}

/* ログインカード内の全テキスト */
.login-card * {
    color: var(--text-primary) !important;
}

.login-card input::placeholder {
    color: var(--text-secondary) !important;
}

/* サイドバー */
.sidebar {
    background: var(--bg-sidebar) !important;
    border-radius: 12px;
    padding: 1rem;
    border: none !important;
    min-height: 500px;
}

.sidebar * {
    color: var(--text-sidebar) !important;
}

.sidebar-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-sidebar-muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.75rem;
    padding: 0 0.5rem;
}

/* ChatGPTライクなチャットエリア */
.chat-container {
    border-radius: 8px !important;
    border: 1px solid var(--border-color) !important;
    background: var(--bg-primary) !important;
}

/* メッセージのスタイル */
.chat-container .message {
    padding: 1.5rem !important;
    max-width: 100% !important;
    color: var(--text-primary) !important;
}

/* メッセージ行のスタイル */
.chat-container [data-testid="bot"], .chat-container [data-testid="user"] {
    padding: 1.5rem !important;
    max-width: 100% !important;
}

.chat-container [data-testid="bot"] {
    background: var(--bg-secondary) !important;
}

.chat-container [data-testid="user"] {
    background: var(--bg-primary) !important;
}

/* メッセージテキストの色を明示的に指定 */
.chat-container [data-testid="bot"] *,
.chat-container [data-testid="user"] * {
    color: var(--text-primary) !important;
}

/* ボタンスタイル */
.primary-btn {
    background: var(--accent) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: background 0.2s !important;
    color: white !important;
}

.primary-btn:hover {
    background: var(--accent-hover) !important;
}

/* サイドバー内のボタン */
.secondary-btn {
    background: var(--btn-sidebar-bg) !important;
    border: 1px solid var(--border-sidebar) !important;
    border-radius: 8px !important;
    color: var(--text-sidebar) !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}

.secondary-btn:hover {
    background: var(--btn-sidebar-hover) !important;
}

.danger-btn {
    background: transparent !important;
    border: 1px solid #ef4444 !important;
    color: #ef4444 !important;
    border-radius: 8px !important;
}

.danger-btn:hover {
    background: rgba(239, 68, 68, 0.1) !important;
}

/* ドロップダウン */
.conversation-select {
    border-radius: 8px !important;
    background: var(--btn-sidebar-bg) !important;
    border: 1px solid var(--border-sidebar) !important;
}

.conversation-select input {
    background: var(--btn-sidebar-bg) !important;
    color: var(--text-sidebar) !important;
}

/* ドロップダウンのリスト部分 */
.conversation-select ul,
.conversation-select li,
.conversation-select [role="listbox"],
.conversation-select [role="option"] {
    background: #343541 !important;
    color: #ececf1 !important;
}

.conversation-select li:hover,
.conversation-select [role="option"]:hover {
    background: #40414f !important;
}

/* サイドバー内の全てのドロップダウン */
.sidebar select,
.sidebar input[type="text"],
.sidebar .wrap {
    background: #343541 !important;
    color: #ececf1 !important;
    border-color: #565869 !important;
}

.sidebar ul[role="listbox"],
.sidebar [data-testid="dropdown"] ul {
    background: #343541 !important;
}

.sidebar ul[role="listbox"] li,
.sidebar [data-testid="dropdown"] li {
    background: #343541 !important;
    color: #ececf1 !important;
}

.sidebar ul[role="listbox"] li:hover,
.sidebar [data-testid="dropdown"] li:hover {
    background: #40414f !important;
}

/* 入力フィールド */
.message-input textarea {
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    background: var(--input-bg) !important;
    color: var(--text-primary) !important;
    box-shadow: 0 0 15px rgba(0,0,0,0.1) !important;
    transition: box-shadow 0.2s !important;
    padding: 12px 16px !important;
}

.message-input textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 15px rgba(16,163,127,0.15) !important;
}

.message-input textarea::placeholder {
    color: var(--text-secondary) !important;
}

/* 情報テキスト（サイドバー内） */
.info-text, .info-text * {
    font-size: 0.8rem !important;
    color: #8e8ea0 !important;
}

.info-text li, .info-text p, .info-text span {
    color: #8e8ea0 !important;
}

/* サイドバー内のMarkdown・テキスト全般 */
.sidebar .prose, .sidebar .prose *,
.sidebar .markdown-text, .sidebar .markdown-text *,
.sidebar p, .sidebar span, .sidebar li {
    color: #ececf1 !important;
}

.sidebar .info-text, .sidebar .info-text *,
.sidebar .info-text li, .sidebar .info-text p {
    color: #8e8ea0 !important;
}

/* メインエリアのアクションボタン */
.action-btn {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}

.action-btn:hover {
    background: var(--bg-primary) !important;
    border-color: var(--accent) !important;
}

/* ステータスメッセージ */
.status-message, #new_conv_status, [id*="status"] {
    color: var(--text-primary) !important;
}

/* Markdownテキスト */
.prose, .prose * {
    color: var(--text-primary) !important;
}

/* 汎用テキスト色の上書き */
p, span, div {
    color: inherit;
}

/* ========== コードブロック対応 ========== */
/* 全てのコードブロックをライトモードに強制 */
pre, code,
.chat-container pre,
.chat-container code,
.prose pre, .prose code,
[data-testid="bot"] pre,
[data-testid="bot"] code,
.message pre, .message code,
.markdown pre, .markdown code {
    background: #f6f8fa !important;
    color: #24292e !important;
    border: 1px solid #e1e4e8 !important;
    border-radius: 6px !important;
}

pre, .chat-container pre, .prose pre,
[data-testid="bot"] pre, .message pre, .markdown pre {
    padding: 12px !important;
    overflow-x: auto !important;
}

code, .chat-container code, .prose code,
[data-testid="bot"] code, .message code, .markdown code {
    padding: 2px 6px !important;
    font-size: 0.9em !important;
}

pre code,
.chat-container pre code,
.prose pre code,
[data-testid="bot"] pre code,
.message pre code,
.markdown pre code {
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
}

/* ダークモードを無効化 */
.dark pre, .dark code,
.dark .chat-container pre,
.dark .chat-container code,
.dark .prose pre, .dark .prose code,
.dark [data-testid="bot"] pre,
.dark [data-testid="bot"] code {
    background: #f6f8fa !important;
    color: #24292e !important;
    border: 1px solid #e1e4e8 !important;
}
"""

# === UI構築 ===
with gr.Blocks(title="Bedrock Chat") as demo:
    # ヘッダー
    gr.HTML(
        """
        <div class="header-container">
            <h1>Bedrock Chat</h1>
            <p>Powered by Amazon Bedrock</p>
        </div>
        """
    )

    # ログインセクション
    with gr.Group(visible=True, elem_classes="login-card") as login_section:
        gr.HTML("<h2 style='text-align:center; margin-bottom:1.5rem;'>ログイン</h2>")
        username_input = gr.Textbox(
            label="ユーザー名",
            placeholder="ユーザー名を入力",
            elem_classes="message-input"
        )
        password_input = gr.Textbox(
            label="パスワード",
            type="password",
            placeholder="パスワードを入力",
            elem_classes="message-input"
        )
        login_btn = gr.Button("ログイン", variant="primary", elem_classes="primary-btn")
        login_status = gr.Markdown("")

    # チャットセクション
    with gr.Group(visible=False, elem_classes="chat-section-container") as chat_section:
        with gr.Row():
            # メインチャットエリア
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="",
                    height=520,
                    elem_classes="chat-container"
                )

                with gr.Row():
                    msg = gr.Textbox(
                        label="",
                        placeholder="メッセージを入力してEnterで送信...",
                        scale=5,
                        elem_classes="message-input",
                        show_label=False,
                        container=False
                    )
                    submit_btn = gr.Button("送信", variant="primary", scale=1, elem_classes="primary-btn")

                with gr.Row():
                    new_conv_btn = gr.Button("新規会話", size="sm", elem_classes="action-btn")
                    logout_btn = gr.Button("ログアウト", size="sm", elem_classes="action-btn")

                new_conv_status = gr.Markdown("")

            # サイドバー
            with gr.Column(scale=1, elem_classes="sidebar"):
                gr.HTML("<div class='sidebar-title'>会話履歴</div>")
                refresh_btn = gr.Button("更新", size="sm", elem_classes="secondary-btn")
                conversation_dropdown = gr.Dropdown(
                    label="",
                    choices=[],
                    value=None,
                    interactive=True,
                    show_label=False,
                    elem_classes="conversation-select",
                    container=False,
                    allow_custom_value=False
                )
                with gr.Row():
                    load_conv_btn = gr.Button("開く", size="sm", elem_classes="secondary-btn")
                    delete_conv_btn = gr.Button("削除", size="sm", elem_classes="danger-btn")

                gr.HTML("<div class='sidebar-title' style='margin-top:1.5rem;'>情報</div>")
                gr.Markdown(
                    """
                    - 会話は自動保存されます
                    - トークン有効期限: 1時間
                    """,
                    elem_classes="info-text"
                )
                conversations_display = gr.Markdown("")

    # === イベントハンドラ ===

    # ログイン
    login_btn.click(
        login,
        inputs=[username_input, password_input],
        outputs=[login_status, login_section, chat_section, conversation_dropdown, conversations_display]
    )

    # チャット送信 - Gradio 6.0の辞書形式に対応
    def respond(message, chat_history):
        bot_message = chat(message, chat_history)
        # Gradio 6.0では辞書形式を使用
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": bot_message})
        return "", chat_history

    submit_btn.click(
        respond,
        inputs=[msg, chatbot],
        outputs=[msg, chatbot]
    )

    msg.submit(
        respond,
        inputs=[msg, chatbot],
        outputs=[msg, chatbot]
    )

    # 新規会話
    new_conv_btn.click(
        new_conversation,
        outputs=[chatbot, new_conv_status]
    )

    # 会話一覧更新
    refresh_btn.click(
        get_conversations,
        outputs=[conversation_dropdown, conversations_display]
    )

    # 会話を読み込む
    load_conv_btn.click(
        load_conversation,
        inputs=[conversation_dropdown],
        outputs=[chatbot, new_conv_status]
    )

    # 会話を削除
    delete_conv_btn.click(
        delete_conversation,
        inputs=[conversation_dropdown],
        outputs=[conversation_dropdown, chatbot, new_conv_status, conversations_display]
    )

    # ログアウト
    logout_btn.click(
        logout,
        outputs=[new_conv_status, login_section, chat_section]
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        css=custom_css,
        theme=gr.themes.Base(
            primary_hue="indigo",
            secondary_hue="purple",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("Inter")
        )
    )
