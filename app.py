import streamlit as st
import datetime
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

# --- ページ設定 ---
st.set_page_config(page_title="AI News Investigator", layout="centered", page_icon="🕵️")

# --- UI: サイドバー設定 ---
st.sidebar.header("⚙️ 設定")
google_api_key = st.sidebar.text_input("Google Gemini API Key", type="password")
tavily_api_key = st.sidebar.text_input("Tavily API Key", type="password")

st.sidebar.markdown("---")
st.sidebar.caption("Powered by Gemini 2.0 Flash")

# --- ロジック: ニュース収集＆レポート作成 ---
def generate_news_report():
    if not google_api_key or not tavily_api_key:
        st.error("⚠️ サイドバーで2つのAPIキーを設定してください。")
        return

    status_area = st.empty()
    
    # 2. 検索フェーズ (Tavily)
    status_area.info("🔍 Web全体から最新のAIニュースを検索し、記事の中身を読んでいます...")
    
    # 以前のご指定に基づいた検索クエリ
    queries = [
        "Generative AI new models release last 24 hours", # 全般・最新
        "OpenAI Anthropic Google Microsoft AI news latest", # 各社動向
        "Video generation AI new tools latest", # 動画生成
        "Image generation AI latest trends", # 画像生成
        "Lesser known AI tools new release", # マイナーなAI
        "Innovative AI tools for creative workflow" # クリエイティブ向け
    ]
    
    # Tavilyツールの初期化 (include_raw_content=Trueで記事中身も取得可能だが、デフォルトで十分な要約が返る)
    tavily = TavilySearchResults(tavily_api_key=tavily_api_key, k=2) # 各クエリ3件
    
    search_context = ""
    found_links = set() # 重複除外用
    
for query in queries:
        try:
            results = tavily.invoke(query)
            for res in results:
                url = res['url']
                if url not in found_links:
                    search_context += f"Source: {url}\nContent: {res['content']}\n\n"
                    found_links.add(url)
        except Exception as e:
            print(f"Search error: {e}")
            
    if not search_context:
        status_area.error("ニュースが見つかりませんでした。")
        return

    # 3. 分析・執筆フェーズ (Gemini)
    status_area.info("🤖 AIコンサルタントが情報を分析し、レポートを執筆中...")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=google_api_key,
        temperature=0.5
    )
    
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # ★ここに「あなたの最強プロンプト」を組み込みました★
    system_prompt = f"""
    あなたは、鋭い洞察力を持つ「辛口AIコンサルタント」です。
    ユーザー（クリエイティブ・IT業界のプロ）に対し、単なるニュース要約ではない「付加価値のあるレポート」を作成してください。

    ### 1. 思考プロセスと選定
    - 提供された検索結果から、業界構造を変えるようなインパクトのあるニュースを選定してください。
    - 特に「新しいモデル」「競合他社の動き（OpenAI vs Google等）」には敏感に反応してください。
    - **情報の鮮度**を重視し、古い情報は除外してください。

    ### 2. 執筆ルール (ここが最重要)
    - **当たり前のことを言わない**: 「業務効率化に役立ちます」「注目が必要です」といった誰でも言えるコメントは**禁止**です。
    - **深く斬り込む**: 「なぜ今それが発表されたのか？」「裏にある意図は何か？」「既存のどのサービスを殺すのか？」という視点でコメントしてください。
    - **毒を少し混ぜる**: 批判的な視点や、リスクに対する警告も含めて構いません。

    ### 3. 出力フォーマット (厳守)
    必ず以下のMarkdown形式で出力してください。

    # 📰 {current_date} のAIニュース速報

    ## ⚡️ 最新ニュース (過去24時間以内目安)
    **1. [ニュースタイトル]**
    - **概要**: (事実を簡潔に。3行以内)
    - **コンサル視点**: (「〜と思われる」「〜だろう」等の曖昧な表現は避け、プロとして断定的に。「これは〇〇業界にとって脅威となる」「××の代替として即戦力」など具体的に)
    - **URL**: [記事URL]

    (これを繰り返す)

    ## 📚 その他チェックすべき動向
    **1. [ニュースタイトル]**
    - **概要**: (簡潔に)
    - **コンサル視点**: (鋭い一言コメント)
    - **URL**: [記事URL]

    (これを繰り返す)

    ---
    **💡 今日の辛口インサイト**
    (今日のニュース全体を俯瞰し、コンサルタントとしての「本音」を書いてください。表面的なまとめではなく、ユーザーがハッとするような視点、あるいは次に調査すべき具体的なキーワードを提示すること)
    """
    
    user_message = f"今日の日付: {current_date}\n\n以下の検索結果からレポートを作成してください:\n\n{search_context}"

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        
        status_area.empty()
        st.markdown(response.content)
        st.success("調査完了！")
        
    except Exception as e:
        status_area.error(f"AI生成エラー: {e}")

# --- UI: メイン画面 ---
st.title("📰 AIニュース朝刊")
st.markdown("""
あなたの専属AIコンシェルジュが、**Tavily**で深層Web検索を行い、
**Gemini**の頭脳でビジネス視点のレポートを作成します。
""")

if st.button("🚀 調査開始", type="primary"):
    generate_news_report()

st.markdown("---")
st.caption("Powered by Google Gemini 2.0 Flash & Tavily Search API")
