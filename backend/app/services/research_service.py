import json
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from app.db.models import URL, Research, Section, get_db_context


class ResearchService:
    """SQLAlchemyを使ってリサーチ情報を永続化するクラス"""

    def save_research(self, research_data: dict) -> bool:
        """リサーチ情報をデータベースに保存"""
        try:
            # 現在の時刻を取得
            now = datetime.now().isoformat()

            # configをJSON文字列に変換
            config_json = json.dumps(research_data.get("config", {})) if research_data.get("config") else None

            with get_db_context() as db:
                # 既存のリサーチがあるか確認
                existing_research = db.query(Research).filter(Research.id == research_data["id"]).first()

                if existing_research:
                    # 既存のリサーチを更新
                    existing_research.topic = research_data["topic"]
                    existing_research.status = research_data["status"]
                    existing_research.config = config_json
                    existing_research.updated_at = now
                    existing_research.progress = research_data.get("progress", 0.0)
                    existing_research.error = research_data.get("error")
                    existing_research.waiting_for_feedback = research_data.get("waiting_for_feedback", False)
                    existing_research.introduction = research_data.get("introduction")
                    existing_research.conclusion = research_data.get("conclusion")
                    existing_research.final_report = research_data.get("final_report")
                    existing_research.completed_at = research_data.get("completed_at")
                    existing_research.user_id = research_data.get("user_id")

                    # 既存のセクションをすべて削除（再作成する）
                    db.query(Section).filter(Section.research_id == research_data["id"]).delete()

                    # 既存のURLをすべて削除（再作成する）
                    db.query(URL).filter(URL.research_id == research_data["id"]).delete()
                else:
                    # 新規リサーチを作成
                    new_research = Research(
                        id=research_data["id"],
                        topic=research_data["topic"],
                        status=research_data["status"],
                        config=config_json,
                        created_at=research_data.get("created_at", now),
                        updated_at=now,
                        completed_at=research_data.get("completed_at"),
                        progress=research_data.get("progress", 0.0),
                        error=research_data.get("error"),
                        waiting_for_feedback=research_data.get("waiting_for_feedback", False),
                        introduction=research_data.get("introduction"),
                        conclusion=research_data.get("conclusion"),
                        final_report=research_data.get("final_report"),
                        user_id=research_data.get("user_id"),
                    )
                    db.add(new_research)

                # セクション情報を保存
                if research_data.get("sections"):
                    for section_data in research_data["sections"]:
                        # search_optionsをJSON文字列に変換
                        search_options_json = (
                            json.dumps(section_data.get("search_options", []))
                            if section_data.get("search_options")
                            else "[]"
                        )

                        # セクションが完了済みセクションに含まれているか確認
                        is_completed = section_data["name"] in research_data.get("completed_sections", [])

                        new_section = Section(
                            research_id=research_data["id"],
                            name=section_data["name"],
                            description=section_data.get("description", ""),
                            content=section_data.get("content", ""),
                            search_options=search_options_json,
                            is_completed=is_completed,
                        )
                        db.add(new_section)

                # URL情報を保存
                if research_data.get("all_urls"):
                    for url_str in research_data["all_urls"]:
                        new_url = URL(research_id=research_data["id"], url=url_str)
                        db.add(new_url)

                db.commit()
                return True

        except SQLAlchemyError as e:
            print(f"リサーチ情報の保存中にSQLAlchemyエラーが発生しました: {e}")
            import traceback

            print(traceback.format_exc())
            return False
        except Exception as e:
            print(f"リサーチ情報の保存中に予期しないエラーが発生しました: {e}")
            import traceback

            print(traceback.format_exc())
            return False

    def get_research(self, research_id: str) -> dict | None:
        """IDを指定してリサーチ情報を取得"""
        try:
            with get_db_context() as db:
                # リサーチ情報を取得
                research = db.query(Research).filter(Research.id == research_id).first()

                if not research:
                    return None

                # オブジェクトを辞書に変換
                research_data = {
                    "id": research.id,
                    "topic": research.topic,
                    "status": research.status,
                    "created_at": research.created_at,
                    "updated_at": research.updated_at,
                    "progress": research.progress,
                    "error": research.error,
                    "waiting_for_feedback": research.waiting_for_feedback,
                    "introduction": research.introduction,
                    "conclusion": research.conclusion,
                    "final_report": research.final_report,
                    "completed_at": research.completed_at,
                    "user_id": research.user_id,
                }

                # configをJSONから変換
                if research.config:
                    research_data["config"] = json.loads(research.config)

                # セクション情報を取得
                sections = []
                completed_sections = []

                for section in research.sections:
                    section_data = {
                        "name": section.name,
                        "description": section.description,
                        "content": section.content,
                    }

                    # search_optionsをJSONから変換
                    if section.search_options:
                        section_data["search_options"] = json.loads(section.search_options)

                    sections.append(section_data)

                    # 完了済みセクションの名前を収集
                    if section.is_completed:
                        completed_sections.append(section.name)

                research_data["sections"] = sections
                research_data["completed_sections"] = completed_sections

                # URL情報を取得
                all_urls = [url.url for url in research.urls]
                research_data["all_urls"] = all_urls

                return research_data

        except Exception as e:
            print(f"リサーチ情報の取得中にエラーが発生しました: {e}")
            import traceback

            print(traceback.format_exc())
            return None

    def list_researches(self, user_id: str | None = None) -> list[dict]:
        """すべてのリサーチの基本情報を取得"""
        try:
            with get_db_context() as db:
                # リサーチ情報を取得
                if user_id:
                    researches_query = (
                        db.query(Research).filter(Research.user_id == user_id).order_by(Research.created_at.desc())
                    )
                else:
                    researches_query = db.query(Research).order_by(Research.created_at.desc())

                researches = []

                for research in researches_query:
                    # 基本情報を辞書に変換
                    research_data = {
                        "id": research.id,
                        "topic": research.topic,
                        "status": research.status,
                        "created_at": research.created_at,
                        "updated_at": research.updated_at,
                        "completed_at": research.completed_at,
                        "progress": research.progress,
                        "error": research.error,
                        "waiting_for_feedback": research.waiting_for_feedback,
                        "user_id": research.user_id,
                    }

                    # 完了済みセクション数と全セクション数を取得
                    completed_count = (
                        db.query(Section)
                        .filter(Section.research_id == research.id, Section.is_completed.is_(True))
                        .count()
                    )

                    total_count = db.query(Section).filter(Section.research_id == research.id).count()

                    research_data["completed_section_count"] = completed_count
                    research_data["total_section_count"] = total_count

                    researches.append(research_data)

                return researches

        except Exception as e:
            print(f"リサーチリストの取得中にエラーが発生しました: {e}")
            import traceback

            print(traceback.format_exc())
            return []

    def delete_research(self, research_id: str) -> bool:
        """リサーチ情報を削除"""
        try:
            with get_db_context() as db:
                # リサーチを削除（関連するセクションとURLはカスケード削除される）
                research = db.query(Research).filter(Research.id == research_id).first()

                if not research:
                    return False

                db.delete(research)
                db.commit()
                return True

        except Exception as e:
            print(f"リサーチの削除中にエラーが発生しました: {e}")
            import traceback

            print(traceback.format_exc())
            return False


_research_service = None


def get_research_service() -> ResearchService:
    """ResearchServiceのシングルトンインスタンスを取得"""
    global _research_service
    if _research_service is None:
        _research_service = ResearchService()
    return _research_service
