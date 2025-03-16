import asyncio
import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.config import get_document_metadata_file, get_research_fts_database, get_user_documents_dir
from app.db.models import init_db
from app.models.research import DEFAULT_REPORT_STRUCTURE, PlanResponse, ResearchConfig, ResearchStatus, SectionModel
from app.services.research_service import get_research_service
from open_deep_researcher.graph import builder


class ResearchManager:
    def __init__(self):
        # データベースの初期化
        init_db()

        # インメモリストア（グラフ実行時に使用）
        self.research_tasks = {}
        # SQLAlchemyを使った永続サービス
        self.research_service = get_research_service()
        # langgraphのメモリセーバー
        self.memory = MemorySaver()
        self.graph = builder.compile(checkpointer=self.memory)

        # 起動時に永続ストアからデータをロード
        self._load_from_persistent_store()

    def _load_from_persistent_store(self):
        """データベースからリサーチデータをロード"""
        try:
            researches = self.research_service.list_researches()
            for research in researches:
                # 完了したものや、エラーのあるものはメモリに復元
                # 継続中のものについては必要になったときに個別にロード
                if research["status"] in ["completed", "error"]:
                    full_research = self.research_service.get_research(research["id"])
                    if full_research:
                        self.research_tasks[research["id"]] = full_research
        except Exception as e:
            print(f"永続ストアからのロード中にエラーが発生しました: {e}")

    async def execute_research(
        self,
        research_id: str,
        topic: str,
        config: ResearchConfig | None = None,
        user_id: str | None = None,
    ):
        """リサーチを実行する"""
        try:
            # 初期状態を設定
            self.research_tasks[research_id] = {
                "id": research_id,
                "topic": topic,
                "status": "initializing",
                "config": config.dict() if config else {},
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
                "sections": [],
                "completed_sections": [],
                "final_report": None,
                "error": None,
                "waiting_for_feedback": False,
                "thread": None,
                "progress": 0.0,
                "all_urls": [],
                "user_id": user_id,
            }

            # データベースに保存
            self.research_service.save_research(self.research_tasks[research_id])

            configurable = self._create_configurable(config, research_id, user_id=user_id)

            # スレッド情報
            thread = {"configurable": configurable}

            self.research_tasks[research_id]["thread"] = thread
            self.research_tasks[research_id]["status"] = "planning"

            # ステータス更新をデータベースに保存
            self.research_service.save_research(self.research_tasks[research_id])

            # リサーチの実行
            async for event in self.graph.astream({"topic": topic}, thread, stream_mode="updates"):
                print(f"Event for {research_id}: {event.keys()}")
                await self._process_event(research_id, event)

                # リサーチ情報の変更をデータベースに保存
                self.research_service.save_research(self.research_tasks[research_id])

                # ヒューマンフィードバックが必要な場合は一時停止
                skip_human_feedback = configurable.get("skip_human_feedback", False)
                if not skip_human_feedback and self.research_tasks[research_id].get("waiting_for_feedback", False):
                    self.research_tasks[research_id]["status"] = "waiting_for_feedback"
                    self.research_service.save_research(self.research_tasks[research_id])
                    break

        except Exception as e:
            # エラー情報を保存
            self.research_tasks[research_id]["status"] = "error"
            self.research_tasks[research_id]["error"] = str(e)
            # データベースに保存
            self.research_service.save_research(self.research_tasks[research_id])
            import traceback

            print(f"Error executing research: {traceback.format_exc()}")

    async def submit_feedback(self, research_id: str, feedback: str | None) -> bool:
        """リサーチプランに対するフィードバックを送信"""
        # データベースからリサーチ情報をロード（まだメモリにない場合）
        if research_id not in self.research_tasks:
            research_data = self.research_service.get_research(research_id)
            if research_data:
                self.research_tasks[research_id] = research_data
            else:
                return False

        task = self.research_tasks[research_id]
        if task["status"] != "waiting_for_feedback" or not task.get("waiting_for_feedback"):
            return False

        # フィードバック待ち状態を解除
        task["waiting_for_feedback"] = False
        # フィードバック処理中のステータスに変更
        task["status"] = "processing_feedback"

        # 状態変更をデータベースに保存
        self.research_service.save_research(task)

        # 非同期でリサーチを続行
        asyncio.create_task(self._continue_research(research_id, feedback))

        return True

    async def _continue_research(self, research_id: str, feedback: str | None):
        """フィードバック後にリサーチを続行"""
        task = self.research_tasks[research_id]
        thread = task["thread"]

        try:
            task["status"] = "processing_feedback"
            # 状態変更をデータベースに保存
            self.research_service.save_research(task)

            # フィードバックに基づいてリサーチを続行
            if feedback is None or feedback.strip() == "":
                command = Command(resume=True)  # フィードバックが提供されない場合は再開
                print("No feedback provided - resuming research")
            else:
                # フィードバックが提供された場合はそれを送信してプランを更新
                command = Command(resume=feedback)
                print(f"Processing feedback: {feedback[:100]}...")

            # リサーチを継続
            async for event in self.graph.astream(command, thread, stream_mode="updates"):
                print(f"Continue event for {research_id}: {event.keys()}")

                # イベントを処理する前に human_feedback イベントの内容をより詳細に出力
                if "human_feedback" in event:
                    print(f"Human feedback event details: {type(event['human_feedback'])}")
                    if isinstance(event["human_feedback"], dict):
                        print(f"  Keys: {event['human_feedback'].keys()}")

                await self._process_event(research_id, event)

                # 変更をデータベースに保存
                self.research_service.save_research(task)

                # フィードバック待ち状態になった場合はループを中断
                if task.get("waiting_for_feedback", False) and task["status"] == "waiting_for_feedback":
                    print(f"Pausing research {research_id} for feedback")
                    break

        except Exception as e:
            # エラー情報を保存
            task["status"] = "error"
            task["error"] = str(e)
            # データベースに保存
            self.research_service.save_research(task)
            import traceback

            print(f"Error continuing research: {traceback.format_exc()}")

    async def _process_event(self, research_id: str, event):  # noqa
        """イベントを処理してステータスを更新"""
        task = self.research_tasks[research_id]
        thread = task["thread"]
        skip_human_feedback = thread["configurable"].get("skip_human_feedback", False)

        # グラフのノード名に基づいて処理
        if "generate_report_plan" in event:
            if "sections" in event["generate_report_plan"]:
                # セクションリストを更新
                sections = event["generate_report_plan"]["sections"]
                task["sections"] = [
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
                    task["waiting_for_feedback"] = True
                    task["status"] = "waiting_for_feedback"
                else:
                    task["status"] = "executing"

        elif "human_feedback" in event:
            # human_feedback が辞書かどうかをチェック
            if isinstance(event["human_feedback"], dict):
                # フィードバック後に更新されたプランがある場合
                if "updated_plan" in event["human_feedback"]:
                    # 更新されたプランがあれば、再度フィードバック待ち状態に
                    updated_plan = event["human_feedback"]["updated_plan"]
                    if updated_plan and isinstance(updated_plan, dict) and "sections" in updated_plan:
                        # セクションリストを更新
                        sections = updated_plan["sections"]
                        task["sections"] = [
                            {
                                "name": s.get("name", ""),
                                "description": s.get("description", ""),
                                "content": s.get("content", ""),
                                "search_options": s.get("search_options", []),
                            }
                            for s in sections
                        ]
                        # 再度フィードバックを待つ
                        task["waiting_for_feedback"] = True
                        task["status"] = "waiting_for_feedback"
                    else:
                        # 更新されたプランがなければ実行に進む
                        task["status"] = "executing"
                else:
                    # フィードバックが処理されたが、プランの更新がない場合は実行に進む
                    task["status"] = "processing_sections"
                    task["progress"] = 0.3
            else:
                # human_feedback が辞書でない場合（None等）は実行に進む
                print("Human feedback event is not a dictionary, continuing execution")
                task["status"] = "processing_sections"
                task["progress"] = 0.3

        # 残りの既存コードはそのまま維持
        elif "setup_knowledge_base" in event:
            task["status"] = "setup_knowledge_base"
            task["progress"] = 0.1

        elif "determine_if_question" in event:
            task["status"] = "analyzing_question"
            task["progress"] = 0.15

        elif "generate_introduction" in event:
            task["status"] = "writing_introduction"
            if "introduction" in event["generate_introduction"]:
                task["introduction"] = event["generate_introduction"]["introduction"]
            if "all_urls" in event["generate_introduction"]:
                task["all_urls"] = event["generate_introduction"]["all_urls"]
            task["progress"] = 0.2

        elif "build_section_with_research" in event:
            task["status"] = "researching_sections"
            task["progress"] = 0.4

            if "completed_sections" in event["build_section_with_research"]:
                # 完了したセクションを追加
                for section in event["build_section_with_research"]["completed_sections"]:
                    section_name = section.name
                    if section_name not in task["completed_sections"]:
                        task["completed_sections"].append(section_name)

                    # セクションの内容を更新
                    for i, s in enumerate(task["sections"]):
                        if s["name"] == section_name:
                            task["sections"][i]["content"] = section.content

                # 進捗率を更新
                total_sections = len(task["sections"]) if task["sections"] else 1
                completed = len(task["completed_sections"])
                task["progress"] = min(0.8, completed / total_sections) if total_sections > 0 else 0

            if "all_urls" in event["build_section_with_research"]:
                # URLを追加（重複は追って対処する）
                task["all_urls"] = task.get("all_urls", []) + event["build_section_with_research"]["all_urls"]
                # 重複を削除
                task["all_urls"] = list(set(task["all_urls"]))

        elif "gather_completed_sections" in event:
            task["status"] = "collecting_sections"
            task["progress"] = 0.8

        elif "generate_conclusion" in event:
            task["status"] = "generating_conclusion"
            if "conclusion" in event["generate_conclusion"]:
                task["conclusion"] = event["generate_conclusion"]["conclusion"]
            task["progress"] = 0.9

        elif "compile_final_report" in event:
            if "final_report" in event["compile_final_report"]:
                # 最終レポートを保存
                task["final_report"] = event["compile_final_report"]["final_report"]
                task["status"] = "completed"
                task["progress"] = 1.0
                task["completed_at"] = datetime.now().isoformat()
                print(f"Research {research_id} completed!")
            else:
                task["status"] = "compiling_report"

        # デバッグ用：不明なイベントタイプがあれば内容を詳細に検査
        else:
            print(f"Unknown event type for {research_id}: {event.keys()}")
            # イベントの内容をデバッグ出力
            for key, value in event.items():
                if isinstance(value, dict):
                    print(f"  {key} keys: {value.keys()}")
                    if "final_report" in value:
                        task["final_report"] = value["final_report"]
                        task["status"] = "completed"
                        task["progress"] = 1.0
                        print(f"Found final report in unexpected event format - research {research_id} completed!")

    def _create_configurable(
        self,
        config: ResearchConfig | None,
        research_id: str,
        user_id: str | None = None,
    ) -> dict[str, Any]:
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
                "enabled_files": self._get_enable_local_document_files(user_id=user_id),
            },
            # 言語設定
            "language": "japanese",
        }

        def _deep_update(original, updates):
            """辞書を再帰的に更新し、None の値は無視する"""
            for key, value in updates.items():
                if isinstance(value, Mapping) and isinstance(original.get(key), Mapping):
                    # 両方が辞書の場合は再帰的に更新
                    original[key] = _deep_update(original.get(key, {}), value)
                elif value is not None:
                    original[key] = value
            return original

        # ユーザー設定で上書き
        if config:
            user_config = config.dict()
            configurable = _deep_update(configurable, user_config)

        return configurable

    def _get_enable_local_document_files(self, user_id: str | None = None) -> list[str]:
        """ローカルドキュメントの有効なファイルリストを取得"""
        metadata_file = get_document_metadata_file(user_id)
        if metadata_file.exists():
            with open(metadata_file) as f:
                data = json.load(f)
                enabled_files = data.get("enabled_files", [])
            return enabled_files
        return []

    async def get_research_status(self, research_id: str) -> ResearchStatus | None:
        """リサーチの現在のステータスを取得"""
        # データベースからリサーチ情報をロード（まだメモリにない場合）
        if research_id not in self.research_tasks:
            research_data = self.research_service.get_research(research_id)
            if research_data:
                self.research_tasks[research_id] = research_data
            else:
                return None

        task = self.research_tasks[research_id]

        # セクションを変換
        sections = []
        if task.get("sections"):
            sections = [
                SectionModel(
                    name=s["name"],
                    description=s["description"],
                    content=s.get("content", ""),
                    search_options=s.get("search_options"),
                )
                for s in task["sections"]
            ]

        return ResearchStatus(
            research_id=task["id"],
            status=task["status"],
            topic=task["topic"],
            sections=sections,
            progress=task.get("progress", 0.0),
            completed_sections=task.get("completed_sections", []),
            final_report=task.get("final_report"),
            error=task.get("error"),
            completed_at=task.get("completed_at"),
        )

    async def get_research_plan(self, research_id: str) -> PlanResponse | None:
        """リサーチプランを取得（フィードバック用）"""
        # データベースからリサーチ情報をロード（まだメモリにない場合）
        if research_id not in self.research_tasks:
            research_data = self.research_service.get_research(research_id)
            if research_data:
                self.research_tasks[research_id] = research_data
            else:
                return None

        task = self.research_tasks[research_id]

        # セクションを変換
        sections = []
        if task.get("sections"):
            sections = [
                SectionModel(
                    name=s["name"],
                    description=s["description"],
                    content=s.get("content", ""),
                    search_options=s.get("search_options"),
                )
                for s in task["sections"]
            ]

        return PlanResponse(
            research_id=task["id"], sections=sections, waiting_for_feedback=task.get("waiting_for_feedback", False)
        )

    async def get_research_result(self, research_id: str) -> dict[str, Any] | None:
        """完了したリサーチの結果を取得"""
        # データベースからリサーチ情報をロード（まだメモリにない場合）
        if research_id not in self.research_tasks:
            research_data = self.research_service.get_research(research_id)
            if research_data:
                self.research_tasks[research_id] = research_data
            else:
                return None

        task = self.research_tasks[research_id]
        if task["status"] != "completed" or not task.get("final_report"):
            return {"research_id": research_id, "status": task["status"], "message": "Research is not completed yet"}

        return {
            "research_id": research_id,
            "status": "completed",
            "final_report": task["final_report"],
            "completed_at": task.get(
                "completed_at", task.get("created_at")
            ),  # completed_at がなければ created_at を使用
        }

    async def list_researches(self, user_id: str | None = None) -> list[ResearchStatus]:
        """すべてのリサーチのリストを取得"""
        # データベースから全てのリサーチ情報を取得
        researches = self.research_service.list_researches(user_id=user_id)
        # ResearchStatusオブジェクトのリストに変換
        result = []
        for research in researches:
            sections = []
            status = ResearchStatus(
                research_id=research["id"],
                status=research["status"],
                topic=research["topic"],
                sections=sections,
                progress=research.get("progress", 0.0),
                completed_sections=[],  # 簡易リストでは空のリストを返す
                final_report=None,
                error=research.get("error"),
                completed_at=research.get("completed_at"),
                user_id=research.get("user_id"),
            )
            result.append(status)

        return result

    async def delete_research(self, research_id: str) -> bool:
        """リサーチを削除する"""
        # データベースからリサーチ情報を取得
        if research_id not in self.research_tasks:
            research_data = self.research_service.get_research(research_id)
            if not research_data:
                return False

        # メモリから削除
        if research_id in self.research_tasks:
            del self.research_tasks[research_id]

        # データベースから削除
        return self.research_service.delete_research(research_id)


_research_manager = None


def get_research_manager():
    global _research_manager
    if _research_manager is None:
        _research_manager = ResearchManager()
    return _research_manager
