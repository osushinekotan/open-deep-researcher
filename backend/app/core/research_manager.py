import asyncio
import json
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command

from app.config import DATA_DIR, get_document_metadata_file, get_research_fts_database, get_user_documents_dir
from app.db.models import init_db
from app.models.research import DEFAULT_REPORT_STRUCTURE, PlanResponse, ResearchConfig, ResearchStatus, SectionModel
from app.services.research_service import get_research_service
from open_deep_researcher.graph import builder

CHECKPOINTS_DATABASE_URL = f"{DATA_DIR}/checkpoints.db"


async def _run_research_async(
    research_id: str,
    topic: str,
    config_dict: dict,
    user_id: str = None,
) -> None:
    """別スレッドで実行される研究処理（非同期）"""
    try:
        # データベース接続を初期化
        init_db()

        # 研究サービスのインスタンスを取得
        research_service = get_research_service()
        configurable = _create_configurable(config_dict, research_id, user_id)

        # 永続化されたチェックポインターを使用
        conn = await aiosqlite.connect(CHECKPOINTS_DATABASE_URL)
        checkpointer = AsyncSqliteSaver(conn)
        graph = builder.compile(checkpointer=checkpointer)

        research_data = research_service.get_research(research_id)
        async for event in graph.astream({"topic": topic}, {"configurable": configurable}, stream_mode="updates"):
            _process_event(research_id, event, research_service)

            # research data 更新
            research_data = research_service.get_research(research_id)
            if not research_data:
                print(f"{research_id} のデータが見つかりません")
                break

            # human feedback が必要な場合は一時停止
            skip_human_feedback = configurable.get("skip_human_feedback", False)
            if not skip_human_feedback and research_data.get("waiting_for_feedback", False):
                research_data["status"] = "waiting_for_feedback"
                research_service.save_research(research_data)
                break

    except Exception as e:
        research_service = get_research_service()
        research_data = research_service.get_research(research_id)
        if research_data:
            research_data["status"] = "error"
            research_data["error"] = str(e)
            research_service.save_research(research_data)


def _run_research_thread(
    research_id: str,
    topic: str,
    config_dict: dict,
    user_id: str = None,
) -> None:
    """スレッド内で asyncio イベントループを実行"""
    try:
        asyncio.run(_run_research_async(research_id, topic, config_dict, user_id))
    except Exception as e:
        research_service = get_research_service()
        research_data = research_service.get_research(research_id)
        if research_data:
            research_data["status"] = "error"
            research_data["error"] = f"スレッド実行エラー: {str(e)}"
            research_service.save_research(research_data)


async def _continue_research_async(
    research_id: str,
    feedback: str = None,
) -> None:
    """フィードバック後に研究を継続するための非同期関数"""
    try:
        init_db()

        research_service = get_research_service()
        research_data = research_service.get_research(research_id)
        if not research_data:
            print(f"{research_id} のデータが見つかりません")
            return

        # 状態を更新
        research_data["status"] = "processing_feedback"
        research_service.save_research(research_data)

        # 設定を再作成
        config_dict = research_data.get("config", {})
        user_id = research_data.get("user_id")
        configurable = _create_configurable(config_dict, research_id, user_id)

        conn = await aiosqlite.connect(CHECKPOINTS_DATABASE_URL)
        checkpointer = AsyncSqliteSaver(conn)
        graph = builder.compile(checkpointer=checkpointer)

        # フィードバックに基づいてリサーチを続行
        if feedback is None or feedback.strip() == "":
            command = Command(resume=True)  # フィードバックが提供されない場合は再開
            configurable["skip_human_feedback"] = True  # 強制的にフィードバックをスキップ
            print("フィードバックなし - 研究を再開します")
        else:
            command = Command(resume=feedback)
            print(f"フィードバックを処理中: {feedback[:100]}...")

        async for event in graph.astream(command, {"configurable": configurable}, stream_mode="updates"):
            _process_event(research_id, event, research_service)

            research_data = research_service.get_research(research_id)
            if not research_data:
                print(f"{research_id} のデータが見つかりません")
                break

    except Exception as e:
        research_service = get_research_service()
        research_data = research_service.get_research(research_id)
        if research_data:
            research_data["status"] = "error"
            research_data["error"] = str(e)
            research_service.save_research(research_data)


# スレッドでasyncio実行ループを管理する関数
def _continue_research_thread(
    research_id: str,
    feedback: str = None,
) -> None:
    """スレッド内でasyncioイベントループを実行"""
    try:
        asyncio.run(_continue_research_async(research_id, feedback))
    except Exception as e:
        print(f"continue_research_thread error（{research_id}）: {e}")

        research_service = get_research_service()
        research_data = research_service.get_research(research_id)
        if research_data:
            research_data["status"] = "error"
            research_data["error"] = f"フィードバック処理エラー: {str(e)}"
            research_service.save_research(research_data)


def _process_event(research_id: str, event: dict, research_service) -> None:  # noqa: C901
    """イベントを処理してステータスを更新"""
    # 研究データを取得
    research_data = research_service.get_research(research_id)
    if not research_data:
        print(f"{research_id} のデータが見つかりません")
        return

    # フィードバックスキップ設定を取得
    config = research_data.get("config", {})
    skip_human_feedback = config.get("skip_human_feedback", False)

    # TODO: refactoring
    if "generate_report_plan" in event:
        if "sections" in event["generate_report_plan"]:
            # セクションリストを更新
            sections = event["generate_report_plan"]["sections"]
            research_data["sections"] = [
                {
                    "name": s.name,
                    "description": s.description,
                    "content": s.content or "",
                    "search_options": s.search_options,
                }
                for s in sections
            ]

            # skip_human_feedback が False の場合のみフィードバック待ち状態に設定
            if not skip_human_feedback:
                research_data["waiting_for_feedback"] = True
                research_data["status"] = "waiting_for_feedback"
            else:
                research_data["status"] = "executing"

    elif "human_feedback" in event:
        if isinstance(event["human_feedback"], dict):
            if "updated_plan" in event["human_feedback"]:
                updated_plan = event["human_feedback"]["updated_plan"]
                if updated_plan and isinstance(updated_plan, dict) and "sections" in updated_plan:
                    sections = updated_plan["sections"]
                    research_data["sections"] = [
                        {
                            "name": s.get("name", ""),
                            "description": s.get("description", ""),
                            "content": s.get("content", ""),
                            "search_options": s.get("search_options", []),
                        }
                        for s in sections
                    ]
                    # 再度フィードバックを待つ
                    research_data["waiting_for_feedback"] = True
                    research_data["status"] = "waiting_for_feedback"
                else:
                    research_data["status"] = "executing"
            else:
                # フィードバックが処理されたが、プランの更新がない場合は実行に進む
                research_data["status"] = "processing_sections"
                research_data["progress"] = 0.3
        else:
            # human_feedback が辞書でない場合（None等）は実行に進む
            print("Human feedback event is not a dictionary, continuing execution")
            research_data["status"] = "processing_sections"
            research_data["progress"] = 0.3

    # 残りの既存コードはそのまま維持
    elif "setup_knowledge_base" in event:
        research_data["status"] = "setup_knowledge_base"
        research_data["progress"] = 0.1

    elif "determine_if_question" in event:
        research_data["status"] = "analyzing_question"
        research_data["progress"] = 0.15

    elif "generate_introduction" in event:
        research_data["status"] = "writing_introduction"
        if "introduction" in event["generate_introduction"]:
            research_data["introduction"] = event["generate_introduction"]["introduction"]
        if "all_urls" in event["generate_introduction"]:
            research_data["all_urls"] = event["generate_introduction"]["all_urls"]
        research_data["progress"] = 0.2

    elif "build_section_with_research" in event:
        research_data["status"] = "researching_sections"
        research_data["progress"] = 0.4

        if "completed_sections" in event["build_section_with_research"]:
            # 完了したセクションを追加
            completed_sections = research_data.get("completed_sections", [])
            for section in event["build_section_with_research"]["completed_sections"]:
                section_name = section.name
                if section_name not in completed_sections:
                    completed_sections.append(section_name)

                # セクションの内容を更新
                sections = research_data.get("sections", [])
                for i, s in enumerate(sections):
                    if s["name"] == section_name:
                        sections[i]["content"] = section.content
                research_data["sections"] = sections

            research_data["completed_sections"] = completed_sections

            # 進捗率を更新
            total_sections = len(research_data.get("sections", [])) if research_data.get("sections") else 1
            completed = len(completed_sections)
            research_data["progress"] = min(0.8, completed / total_sections) if total_sections > 0 else 0

        if "all_urls" in event["build_section_with_research"]:
            # URLを追加（重複は追って対処する）
            all_urls = research_data.get("all_urls", []) + event["build_section_with_research"]["all_urls"]
            # 重複を削除
            research_data["all_urls"] = list(set(all_urls))

    elif "gather_completed_sections" in event:
        research_data["status"] = "collecting_sections"
        research_data["progress"] = 0.8

    elif "generate_conclusion" in event:
        research_data["status"] = "generating_conclusion"
        if "conclusion" in event["generate_conclusion"]:
            research_data["conclusion"] = event["generate_conclusion"]["conclusion"]
        research_data["progress"] = 0.9

    elif "compile_final_report" in event:
        if "final_report" in event["compile_final_report"]:
            # 最終レポートを保存
            research_data["final_report"] = event["compile_final_report"]["final_report"]
            research_data["status"] = "completed"
            research_data["progress"] = 1.0
            research_data["completed_at"] = datetime.now().isoformat()
            print(f"research {research_id} が完了しました！")
        else:
            research_data["status"] = "compiling_report"

    # デバッグ用：不明なイベントタイプがあれば内容を詳細に検査
    else:
        print(f"不明なイベントタイプ（{research_id}）: {event.keys()}")
        # イベントの内容をデバッグ出力
        for key, value in event.items():
            if isinstance(value, dict):
                print(f"  {key} のキー: {value.keys()}")
                if "final_report" in value:
                    research_data["final_report"] = value["final_report"]
                    research_data["status"] = "completed"
                    research_data["progress"] = 1.0
                    print(f"予期しないイベント形式で最終レポートを発見 -  {research_id} が完了")

    research_service.save_research(research_data)


def _create_configurable(
    config: dict,
    research_id: str,
    user_id: str = None,
) -> dict:
    """設定からConfigurableオブジェクトを作成"""
    # デフォルト設定
    configurable = {
        "thread_id": research_id,
        # 基本設定
        "report_structure": DEFAULT_REPORT_STRUCTURE,
        "number_of_queries": 2,
        "max_reflection": 2,
        "max_sections": 3,
        "request_delay": 0.0,
        # 単語数制限
        "max_section_words": 1000,
        "max_subsection_words": 500,
        "max_introduction_words": 500,
        "max_conclusion_words": 500,
        # 深掘り設定
        "skip_human_feedback": False,
        "enable_deep_research": True,
        "deep_research_depth": 1,
        "deep_research_breadth": 2,
        # 検索プロバイダー設定
        "introduction_search_provider": "tavily",
        "planning_search_provider": "tavily",
        "available_search_providers": ["tavily"],
        "deep_research_providers": ["tavily"],
        "default_search_provider": "tavily",
        # プロバイダー別設定
        "tavily_search_config": {
            "max_results": 5,
            "include_raw_content": False,
        },
        "arxiv_search_config": {
            "load_max_docs": 5,
            "get_full_documents": True,
        },
        "local_search_config": {
            "local_document_path": str(get_user_documents_dir(user_id)),
            "db_path": str(get_research_fts_database(research_id)),
            "chunk_size": 10000,
            "chunk_overlap": 2000,
            "top_k": 5,
            "enabled_files": _get_enable_local_document_files(user_id=user_id),
        },
        # 言語設定
        "language": "japanese",
    }

    # ユーザー設定があれば上書き
    if config:

        def _deep_update(original, updates):
            for key, value in updates.items():
                if isinstance(value, dict) and isinstance(original.get(key), dict):
                    original[key] = _deep_update(original.get(key, {}), value)
                elif value is not None:
                    original[key] = value
            return original

        configurable = _deep_update(configurable, config)

    return configurable


def _get_enable_local_document_files(user_id: str = None) -> list:
    """ローカルドキュメントの有効なファイルリストを取得"""
    metadata_file = get_document_metadata_file(user_id)
    if metadata_file.exists():
        with open(metadata_file) as f:
            data = json.load(f)
            enabled_files = data.get("enabled_files", [])
        return enabled_files
    return []


class ResearchManager:
    """研究管理クラス（データベース中心・スレッド分離実装）"""

    def __init__(self):
        init_db()

        self.research_service = get_research_service()
        self.thread_pool = ThreadPoolExecutor(max_workers=3)  # 同時実行数を制限

        self.running_threads = {}

    async def execute_research(
        self,
        research_id: str,
        topic: str,
        config: ResearchConfig = None,
        user_id: str = None,
    ):
        """研究を実行する"""
        try:
            # 初期状態をデータベースに保存
            now = datetime.now().isoformat()
            research_data = {
                "id": research_id,
                "topic": topic,
                "status": "initializing",
                "config": config.dict() if config else {},
                "created_at": now,
                "updated_at": now,
                "completed_at": None,
                "sections": [],
                "completed_sections": [],
                "final_report": None,
                "error": None,
                "waiting_for_feedback": False,
                "progress": 0.0,
                "all_urls": [],
                "user_id": user_id,
            }

            # データベースに保存
            self.research_service.save_research(research_data)

            config_dict = config.dict() if config else {}
            future = self.thread_pool.submit(_run_research_thread, research_id, topic, config_dict, user_id)
            self.running_threads[research_id] = future

            asyncio.create_task(self._wait_for_completion(research_id, future))

            return True

        except Exception as e:
            error_data = {
                "id": research_id,
                "topic": topic,
                "status": "error",
                "error": str(e),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            self.research_service.save_research(error_data)

            print(f"execute_research error: {traceback.format_exc()}")
            return False

    async def _wait_for_completion(self, research_id: str, future):
        """スレッドの完了を待つ"""
        try:
            await asyncio.to_thread(future.result)
        except Exception as e:
            print(f"{research_id} の実行中にエラーが発生: {e}")
            research_data = self.research_service.get_research(research_id)
            if research_data:
                research_data["status"] = "error"
                research_data["error"] = str(e)
                self.research_service.save_research(research_data)

        finally:
            # 処理が完了したらスレッド追跡から削除
            if research_id in self.running_threads:
                del self.running_threads[research_id]

    async def submit_feedback(self, research_id: str, feedback: str = None) -> bool:
        """研究プランに対するフィードバックを送信"""
        # データベースから研究情報をロード
        research_data = self.research_service.get_research(research_id)
        if not research_data:
            return False

        if research_data["status"] != "waiting_for_feedback" or not research_data.get("waiting_for_feedback"):
            return False

        research_data["waiting_for_feedback"] = False
        research_data["status"] = "processing_feedback"

        self.research_service.save_research(research_data)

        future = self.thread_pool.submit(_continue_research_thread, research_id, feedback)
        self.running_threads[research_id] = future

        asyncio.create_task(self._wait_for_completion(research_id, future))

        return True

    async def get_research_status(self, research_id: str) -> ResearchStatus:
        """研究の現在のステータスを取得"""
        # データベースから研究情報をロード
        research_data = self.research_service.get_research(research_id)
        if not research_data:
            return None

        # セクションを変換
        sections = []
        if research_data.get("sections"):
            sections = [
                SectionModel(
                    name=s["name"],
                    description=s["description"],
                    content=s.get("content", ""),
                    search_options=s.get("search_options"),
                )
                for s in research_data["sections"]
            ]

        return ResearchStatus(
            research_id=research_data["id"],
            status=research_data["status"],
            topic=research_data["topic"],
            sections=sections,
            progress=research_data.get("progress", 0.0),
            completed_sections=research_data.get("completed_sections", []),
            final_report=research_data.get("final_report"),
            error=research_data.get("error"),
            completed_at=research_data.get("completed_at"),
            user_id=research_data.get("user_id"),
        )

    async def get_research_plan(self, research_id: str) -> PlanResponse:
        """研究プランを取得（フィードバック用）"""
        # データベースから研究情報をロード
        research_data = self.research_service.get_research(research_id)
        if not research_data:
            return None

        # セクションを変換
        sections = []
        if research_data.get("sections"):
            sections = [
                SectionModel(
                    name=s["name"],
                    description=s["description"],
                    content=s.get("content", ""),
                    search_options=s.get("search_options"),
                )
                for s in research_data["sections"]
            ]

        return PlanResponse(
            research_id=research_data["id"],
            sections=sections,
            waiting_for_feedback=research_data.get("waiting_for_feedback", False),
        )

    async def get_research_result(self, research_id: str) -> dict:
        """完了した研究の結果を取得"""
        # データベースから研究情報をロード
        research_data = self.research_service.get_research(research_id)
        if not research_data:
            return None

        if research_data["status"] != "completed" or not research_data.get("final_report"):
            return {
                "research_id": research_id,
                "status": research_data["status"],
                "message": "研究はまだ完了していません",
            }

        return {
            "research_id": research_id,
            "status": "completed",
            "final_report": research_data["final_report"],
            "completed_at": research_data.get("completed_at", research_data.get("created_at")),
        }

    async def list_researches(self, user_id: str = None) -> list[ResearchStatus]:
        """すべての研究のリストを取得"""
        # データベースから全ての研究情報を取得
        researches = self.research_service.list_researches(user_id=user_id)

        result = []
        for research in researches:
            sections = []
            status = ResearchStatus(
                research_id=research["id"],
                status=research["status"],
                topic=research["topic"],
                sections=sections,
                progress=research.get("progress", 0.0),
                completed_sections=[],
                final_report=None,
                error=research.get("error"),
                completed_at=research.get("completed_at"),
                user_id=research.get("user_id"),
            )
            result.append(status)

        return result

    async def delete_research(self, research_id: str) -> bool:
        """研究を削除する"""
        # 実行中のスレッドがあれば終了を試みる
        if research_id in self.running_threads:
            future = self.running_threads[research_id]
            future.cancel()
            del self.running_threads[research_id]

        return self.research_service.delete_research(research_id)

    def __del__(self):
        """デストラクタ - スレッドプールをクリーンアップ"""
        if hasattr(self, "thread_pool"):
            self.thread_pool.shutdown(wait=False)


_research_manager = None


def get_research_manager() -> ResearchManager:
    """ResearchManagerのシングルトンインスタンスを取得"""
    global _research_manager
    if _research_manager is None:
        _research_manager = ResearchManager()
    return _research_manager
