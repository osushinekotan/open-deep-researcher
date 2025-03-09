import asyncio
from typing import Any

from open_deep_researcher.retriever.local import local_search
from open_deep_researcher.retriever.web import web_search


async def hybrid_search(
    search_queries: list[str],
    web_search_api: str,
    web_search_params: dict[str, Any],
    local_search_params: dict[str, Any],
    **kwargs,
) -> str:
    # ローカル検索とWeb検索を並行して実行
    local_task = asyncio.create_task(
        local_search(
            search_queries,
            **web_search_params,
            **local_search_params,
        )
    )
    web_task = asyncio.create_task(web_search(web_search_api, search_queries, web_search_params))
    local_results_raw, web_results_raw = await asyncio.gather(local_task, web_task)
    combined_results = local_results_raw + "\n\n" + web_results_raw

    return combined_results
