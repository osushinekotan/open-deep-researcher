import asyncio
from datetime import datetime
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.config import DOCUMENTS_DIR, VECTOR_STORE_DIR
from app.models.research import DEFAULT_REPORT_STRUCTURE, PlanResponse, ResearchConfig, ResearchStatus, SectionModel
from open_deep_researcher.graph import builder


class ResearchManager:
    def __init__(self):
        self.research_tasks = {}  # research_id -> task_info
        self.memory = MemorySaver()
        self.graph = builder.compile(checkpointer=self.memory)

    async def execute_research(self, research_id: str, topic: str, config: ResearchConfig | None = None):
        """リサーチを実行する"""
        try:
            # 初期状態を設定
            self.research_tasks[research_id] = {
                "id": research_id,
                "topic": topic,
                "status": "initializing",
                "config": config.dict() if config else {},
                "created_at": datetime.now().isoformat(),
                "sections": [],
                "completed_sections": [],
                "final_report": None,
                "error": None,
                "waiting_for_feedback": False,
                "thread": None,
                "progress": 0.0,
            }

            # 設定からConfigurableを作成
            configurable = self._create_configurable(config, research_id)

            # スレッド情報
            thread = {"configurable": configurable}

            self.research_tasks[research_id]["thread"] = thread
            self.research_tasks[research_id]["status"] = "planning"

            # リサーチの実行
            async for event in self.graph.astream({"topic": topic}, thread, stream_mode="updates"):
                print(f"Event for {research_id}: {event.keys()}")
                await self._process_event(research_id, event)

                # ヒューマンフィードバックが必要な場合は一時停止
                skip_human_feedback = configurable.get("skip_human_feedback", False)
                if not skip_human_feedback and self.research_tasks[research_id].get("waiting_for_feedback", False):
                    self.research_tasks[research_id]["status"] = "waiting_for_feedback"
                    break

        except Exception as e:
            # エラー情報を保存
            self.research_tasks[research_id]["status"] = "error"
            self.research_tasks[research_id]["error"] = str(e)
            import traceback

            print(f"Error executing research: {traceback.format_exc()}")

    async def submit_feedback(self, research_id: str, feedback: str | None) -> bool:
        """リサーチプランに対するフィードバックを送信"""
        if research_id not in self.research_tasks:
            return False

        task = self.research_tasks[research_id]
        if task["status"] != "waiting_for_feedback" or not task.get("waiting_for_feedback"):
            return False

        # フィードバック待ち状態を解除
        task["waiting_for_feedback"] = False
        task["status"] = "processing_feedback"

        # 非同期でリサーチを続行
        asyncio.create_task(self._continue_research(research_id, feedback))

        return True

    async def _continue_research(self, research_id: str, feedback: str | None):
        """フィードバック後にリサーチを続行"""
        task = self.research_tasks[research_id]
        thread = task["thread"]

        try:
            task["status"] = "executing"

            # フィードバックに基づいてリサーチを続行
            if feedback is None or feedback.strip() == "":
                command = Command(resume=True)  # フィードバックが提供されない場合は再開
                print("No feedback provided - resuming research")
            else:
                # フィードバックが提供された場合はそれを送信してプランを更新
                command = Command(resume=feedback)

            # リサーチを継続
            async for event in self.graph.astream(command, thread, stream_mode="updates"):
                print(f"Continue event for {research_id}: {event.keys()}")
                await self._process_event(research_id, event)

        except Exception as e:
            # エラー情報を保存
            task["status"] = "error"
            task["error"] = str(e)
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
                    {"name": s.name, "description": s.description, "content": s.content or ""} for s in sections
                ]

                # skip_human_feedback が False の場合のみフィードバック待ち状態に設定
                if not skip_human_feedback:
                    task["waiting_for_feedback"] = True
                    task["status"] = "waiting_for_feedback"
                else:
                    task["status"] = "executing"

        elif "setup_local_documents" in event:
            task["status"] = "initializing_documents"

        elif "determine_if_question" in event:
            task["status"] = "analyzing_question"

        elif "generate_introduction" in event:
            task["status"] = "writing_introduction"

        elif "human_feedback" in event:
            task["status"] = "processing_sections"

        elif "build_section_with_research" in event:
            task["status"] = "researching_sections"

            if "completed_sections" in event["build_section_with_research"]:
                # 完了したセクションを追加
                for section in event["build_section_with_research"]["completed_sections"]:
                    section_name = section.name
                    if section_name not in task["completed_sections"]:
                        task["completed_sections"].append(section_name)

                # 進捗率を更新
                total_sections = len(task["sections"]) if task["sections"] else 1
                completed = len(task["completed_sections"])
                task["progress"] = min(0.9, completed / total_sections) if total_sections > 0 else 0

        elif "gather_completed_sections" in event:
            task["status"] = "collecting_sections"

        elif "generate_conclusion" in event:
            task["status"] = "generating_conclusion"

        elif "compile_final_report" in event:
            if "final_report" in event["compile_final_report"]:
                # 最終レポートを保存
                task["final_report"] = event["compile_final_report"]["final_report"]
                task["status"] = "completed"
                task["progress"] = 1.0
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

    def _create_configurable(self, config: ResearchConfig | None, research_id: str) -> dict[str, Any]:
        """設定からConfigurableオブジェクトを作成"""
        # デフォルト設定
        configurable = {
            "thread_id": research_id,
            # 基本設定
            "report_structure": DEFAULT_REPORT_STRUCTURE,
            "number_of_queries": 2,
            "max_reflection": 2,
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
                "load_all_available_meta": True,
                "add_aditional_metadata": True,
            },
            "local_search_config": {
                "vector_store_path": str(VECTOR_STORE_DIR),
                "local_document_path": str(DOCUMENTS_DIR),
                "embedding_provider": "openai",
                "embedding_model": "text-embedding-3-small",
            },
            "google_patent_search_config": {
                "db_path": "data/patent_database.sqlite",
                "limit": 10,
                "query_expansion": True,
            },
            "language": "japanese",
            "max_tokens_per_source": 8192,
        }

        # ユーザー設定で上書き
        if config:
            user_config = config.dict(exclude_unset=True)

            # 列挙型を string 値に変換
            if "search_source" in user_config and user_config["search_source"]:
                user_config["search_source"] = user_config["search_source"].value

            for key in ["planner_provider", "writer_provider", "conclusion_writer_provider"]:
                if key in user_config and user_config[key]:
                    user_config[key] = user_config[key].value

            # 設定を更新
            configurable.update(user_config)

        return configurable

    async def get_research_status(self, research_id: str) -> ResearchStatus | None:
        """リサーチの現在のステータスを取得"""
        if research_id not in self.research_tasks:
            return None

        task = self.research_tasks[research_id]

        # セクションを変換
        sections = []
        if task.get("sections"):
            sections = [
                SectionModel(name=s["name"], description=s["description"], content=s.get("content", ""))
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
        )

    async def get_research_plan(self, research_id: str) -> PlanResponse | None:
        """リサーチプランを取得（フィードバック用）"""
        if research_id not in self.research_tasks:
            return None

        task = self.research_tasks[research_id]

        # セクションを変換
        sections = []
        if task.get("sections"):
            sections = [
                SectionModel(name=s["name"], description=s["description"], content=s.get("content", ""))
                for s in task["sections"]
            ]

        return PlanResponse(
            research_id=task["id"], sections=sections, waiting_for_feedback=task.get("waiting_for_feedback", False)
        )

    async def get_research_result(self, research_id: str) -> dict[str, Any] | None:
        """完了したリサーチの結果を取得"""
        if research_id not in self.research_tasks:
            return None

        task = self.research_tasks[research_id]
        if task["status"] != "completed" or not task.get("final_report"):
            return {"research_id": research_id, "status": task["status"], "message": "Research is not completed yet"}

        return {
            "research_id": research_id,
            "status": "completed",
            "final_report": task["final_report"],
            "completed_at": datetime.now().isoformat(),
        }

    async def list_researches(self) -> list[ResearchStatus]:
        """すべてのリサーチのリストを取得"""
        result = []
        for research_id, task in self.research_tasks.items():  # noqa
            status = await self.get_research_status(research_id)
            if status:
                result.append(status)
        return result


_research_manager = None


def get_research_manager():
    global _research_manager
    if _research_manager is None:
        _research_manager = ResearchManager()
    return _research_manager
