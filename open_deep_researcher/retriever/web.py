import asyncio

from langchain_community.retrievers import ArxivRetriever
from langchain_community.utilities.pubmed import PubMedAPIWrapper
from langsmith import traceable
from tavily import AsyncTavilyClient

from open_deep_researcher.utils import deduplicate_and_format_sources


@traceable
async def tavily_search_async(
    search_queries: list[str],
    max_results: int = 5,
    include_raw_content: bool = True,
) -> list[dict]:
    """
    Performs concurrent web searches using the Tavily API.

    Args:
        search_queries (List[SearchQuery]): List of search queries to process

    Returns:
            List[dict]: List of search responses from Tavily API, one per query. Each response has format:
                {
                    'query': str, # The original search query
                    'follow_up_questions': None,
                    'answer': None,
                    'images': list,
                    'results': [                     # List of search results
                        {
                            'title': str,            # Title of the webpage
                            'url': str,              # URL of the result
                            'content': str,          # Summary/snippet of content
                            'score': float,          # Relevance score
                            'raw_content': str|None  # Full page content if available
                        },
                        ...
                    ]
                }
    """
    tavily_async_client = AsyncTavilyClient()
    search_tasks = []
    for query in search_queries:
        search_tasks.append(
            tavily_async_client.search(
                query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                topic="general",
                include_images=True,
                include_image_descriptions=True,
            )
        )

    # Execute all searches concurrently
    search_docs = await asyncio.gather(*search_tasks)

    return search_docs


@traceable
async def arxiv_search_async(  # noqa
    search_queries: list[str],
    load_max_docs: int = 5,
    get_full_documents: bool = True,
    load_all_available_meta: bool = True,
    add_aditional_metadata: bool = False,
) -> list[dict]:
    """
    Performs concurrent searches on arXiv using the ArxivRetriever.

    Args:
        search_queries (List[str]): List of search queries or article IDs
        load_max_docs (int, optional): Maximum number of documents to return per query. Default is 5.
        get_full_documents (bool, optional): Whether to fetch full text of documents. Default is True.
        load_all_available_meta (bool, optional): Whether to load all available metadata. Default is True.

    Returns:
        List[dict]: List of search responses from arXiv, one per query. Each response has format:
            {
                'query': str,                    # The original search query
                'follow_up_questions': None,
                'answer': None,
                'images': [],
                'results': [                     # List of search results
                    {
                        'title': str,            # Title of the paper
                        'url': str,              # URL (Entry ID) of the paper
                        'content': str,          # Formatted summary with metadata
                        'score': float,          # Relevance score (approximated)
                        'raw_content': str|None  # Full paper content if available
                    },
                    ...
                ]
            }
    """

    async def process_single_query(query):  # noqa
        try:
            # Create retriever for each query
            retriever = ArxivRetriever(
                load_max_docs=load_max_docs,
                get_full_documents=get_full_documents,
                load_all_available_meta=load_all_available_meta,
            )

            # Run the synchronous retriever in a thread pool
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, lambda: retriever.invoke(query))

            results = []
            # Assign decreasing scores based on the order
            base_score = 1.0
            score_decrement = 1.0 / (len(docs) + 1) if docs else 0

            for i, doc in enumerate(docs):
                # Extract metadata
                metadata = doc.metadata

                # Use entry_id as the URL (this is the actual arxiv link)
                url = metadata.get("entry_id", "")

                # Format content with all useful metadata
                content_parts = []

                # Primary information
                if "Summary" in metadata:
                    content_parts.append(f"Summary: {metadata['Summary']}")

                if "Authors" in metadata:
                    content_parts.append(f"Authors: {metadata['Authors']}")

                # Add publication information
                published = metadata.get("Published")
                published_str = (
                    published.isoformat() if hasattr(published, "isoformat") else str(published) if published else ""
                )
                if published_str:
                    content_parts.append(f"Published: {published_str}")

                # Add additional metadata if available
                if add_aditional_metadata:
                    if "primary_category" in metadata:
                        content_parts.append(f"Primary Category: {metadata['primary_category']}")

                    if "categories" in metadata and metadata["categories"]:
                        content_parts.append(f"Categories: {', '.join(metadata['categories'])}")

                    if "comment" in metadata and metadata["comment"]:
                        content_parts.append(f"Comment: {metadata['comment']}")

                    if "journal_ref" in metadata and metadata["journal_ref"]:
                        content_parts.append(f"Journal Reference: {metadata['journal_ref']}")

                    if "doi" in metadata and metadata["doi"]:
                        content_parts.append(f"DOI: {metadata['doi']}")

                    # Get PDF link if available in the links
                    pdf_link = ""
                    if "links" in metadata and metadata["links"]:
                        for link in metadata["links"]:
                            if "pdf" in link:
                                pdf_link = link
                                content_parts.append(f"PDF: {pdf_link}")
                                break

                # Join all content parts with newlines
                content = "\n".join(content_parts)

                result = {
                    "title": metadata.get("Title", ""),
                    "url": url,  # Using entry_id as the URL
                    "content": content,
                    "score": base_score - (i * score_decrement),
                    "raw_content": doc.page_content if get_full_documents else None,
                }
                results.append(result)

            return {
                "query": query,
                "follow_up_questions": None,
                "answer": None,
                "images": [],
                "results": results,
            }
        except Exception as e:
            # Handle exceptions gracefully
            print(f"Error processing arXiv query '{query}': {str(e)}")
            return {
                "query": query,
                "follow_up_questions": None,
                "answer": None,
                "images": [],
                "results": [],
                "error": str(e),
            }

    # Process queries sequentially with delay to respect arXiv rate limit (1 request per 3 seconds)
    search_docs = []
    for i, query in enumerate(search_queries):
        try:
            # Add delay between requests (3 seconds per ArXiv's rate limit)
            if i > 0:  # Don't delay the first request
                await asyncio.sleep(3.0)

            result = await process_single_query(query)
            search_docs.append(result)
        except Exception as e:
            # Handle exceptions gracefully
            print(f"Error processing arXiv query '{query}': {str(e)}")
            search_docs.append(
                {
                    "query": query,
                    "follow_up_questions": None,
                    "answer": None,
                    "images": [],
                    "results": [],
                    "error": str(e),
                }
            )

            # Add additional delay if we hit a rate limit error
            if "429" in str(e) or "Too Many Requests" in str(e):
                print("ArXiv rate limit exceeded. Adding additional delay...")
                await asyncio.sleep(5.0)  # Add a longer delay if we hit a rate limit

    return search_docs


@traceable
async def pubmed_search_async(  # noqa
    search_queries: list[str],
    top_k_results: int = 5,
    email: str | None = None,
    api_key: str | None = None,
    doc_content_chars_max: int = 4000,
) -> list[dict]:
    """
    Performs concurrent searches on PubMed using the PubMedAPIWrapper.

    Args:
        search_queries (List[str]): List of search queries
        top_k_results (int, optional): Maximum number of documents to return per query. Default is 5.
        email (str, optional): Email address for PubMed API. Required by NCBI.
        api_key (str, optional): API key for PubMed API for higher rate limits.
        doc_content_chars_max (int, optional): Maximum characters for document content. Default is 4000.

    Returns:
        List[dict]: List of search responses from PubMed, one per query. Each response has format:
            {
                'query': str,                    # The original search query
                'follow_up_questions': None,
                'answer': None,
                'images': [],
                'results': [                     # List of search results
                    {
                        'title': str,            # Title of the paper
                        'url': str,              # URL to the paper on PubMed
                        'content': str,          # Formatted summary with metadata
                        'score': float,          # Relevance score (approximated)
                        'raw_content': str       # Full abstract content
                    },
                    ...
                ]
            }
    """

    async def process_single_query(query):
        try:
            # print(f"Processing PubMed query: '{query}'")

            # Create PubMed wrapper for the query
            wrapper = PubMedAPIWrapper(
                top_k_results=top_k_results,
                doc_content_chars_max=doc_content_chars_max,
                email=email if email else "your_email@example.com",
                api_key=api_key if api_key else "",
            )

            # Run the synchronous wrapper in a thread pool
            loop = asyncio.get_event_loop()

            # Use wrapper.lazy_load instead of load to get better visibility
            docs = await loop.run_in_executor(None, lambda: list(wrapper.lazy_load(query)))

            print(f"Query '{query}' returned {len(docs)} results")

            results = []
            # Assign decreasing scores based on the order
            base_score = 1.0
            score_decrement = 1.0 / (len(docs) + 1) if docs else 0

            for i, doc in enumerate(docs):
                # Format content with metadata
                content_parts = []

                if doc.get("Published"):
                    content_parts.append(f"Published: {doc['Published']}")

                if doc.get("Copyright Information"):
                    content_parts.append(f"Copyright Information: {doc['Copyright Information']}")

                if doc.get("Summary"):
                    content_parts.append(f"Summary: {doc['Summary']}")

                # Generate PubMed URL from the article UID
                uid = doc.get("uid", "")
                url = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/" if uid else ""

                # Join all content parts with newlines
                content = "\n".join(content_parts)

                result = {
                    "title": doc.get("Title", ""),
                    "url": url,
                    "content": content,
                    "score": base_score - (i * score_decrement),
                    "raw_content": doc.get("Summary", ""),
                }
                results.append(result)

            return {
                "query": query,
                "follow_up_questions": None,
                "answer": None,
                "images": [],
                "results": results,
            }
        except Exception as e:
            # Handle exceptions with more detailed information
            error_msg = f"Error processing PubMed query '{query}': {str(e)}"
            print(error_msg)
            import traceback

            print(traceback.format_exc())  # Print full traceback for debugging

            return {
                "query": query,
                "follow_up_questions": None,
                "answer": None,
                "images": [],
                "results": [],
                "error": str(e),
            }

    # Process all queries with a reasonable delay between them
    search_docs = []

    # Start with a small delay that increases if we encounter rate limiting
    delay = 1.0  # Start with a more conservative delay

    for i, query in enumerate(search_queries):
        try:
            # Add delay between requests
            if i > 0:  # Don't delay the first request
                # print(f"Waiting {delay} seconds before next query...")
                await asyncio.sleep(delay)

            result = await process_single_query(query)
            search_docs.append(result)

            # If query was successful with results, we can slightly reduce delay (but not below minimum)
            if result.get("results") and len(result["results"]) > 0:
                delay = max(0.5, delay * 0.9)  # Don't go below 0.5 seconds

        except Exception as e:
            # Handle exceptions gracefully
            error_msg = f"Error in main loop processing PubMed query '{query}': {str(e)}"
            print(error_msg)

            search_docs.append(
                {
                    "query": query,
                    "follow_up_questions": None,
                    "answer": None,
                    "images": [],
                    "results": [],
                    "error": str(e),
                }
            )

            # If we hit an exception, increase delay for next query
            delay = min(5.0, delay * 1.5)  # Don't exceed 5 seconds

    return search_docs


async def web_search(
    search_api: str,
    query_list: list[str],
    params_to_pass: dict,
    max_tokens_per_source: int = 8192,
    max_images: int | None = 10,
) -> str:
    """Select and execute the appropriate search API.

    Args:
        search_api: Name of the search API to use
        query_list: List of search queries to execute
        params_to_pass: Parameters to pass to the search API

    Returns:
        Formatted string containing search results

    Raises:
        ValueError: If an unsupported search API is specified
    """
    if search_api == "tavily":
        search_results = await tavily_search_async(query_list, **params_to_pass)
        return deduplicate_and_format_sources(
            search_results, max_tokens_per_source=max_tokens_per_source, max_images=max_images
        )
    elif search_api == "arxiv":
        search_results = await arxiv_search_async(query_list, **params_to_pass)
        return deduplicate_and_format_sources(
            search_results, max_tokens_per_source=max_tokens_per_source, max_images=max_images
        )
    elif search_api == "pubmed":
        search_results = await pubmed_search_async(query_list, **params_to_pass)
        return deduplicate_and_format_sources(
            search_results, max_tokens_per_source=max_tokens_per_source, max_images=max_images
        )
    else:
        raise ValueError(f"Unsupported search API: {search_api}")
