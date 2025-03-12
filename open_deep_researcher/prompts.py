introduction_query_writer_instructions = """You are performing research for a report introduction.

<Report topic>
{topic}
</Report topic>

<Task>
Your goal is to generate {number_of_queries} web search queries that will help gather information for writing an introduction to the report.

The queries should:
1. Be related to the Report topic
2. Help gather background information and context on the topic
3. Focus on getting high-level overview information

Make the queries specific enough to find high-quality, relevant sources while focusing on introductory content.
</Task>
"""
introduction_writer_instructions = """Write an introduction for a research report.

<Report topic>
{topic}
</Report topic>

<Source material>
{context}
</Source material>

<Task>
Use the provided source material to write an introduction for a report on the given topic.

Your introduction should:
1. Provide background context on the topic
2. Establish why the topic is important or relevant
3. Briefly outline the scope of the report
4. Be concise (about {max_words} words)
5. Use clear, engaging language

Reference sources inline according to the citation rules.

<Citation Rules>
- Use inline citations by embedding links in Markdown format: `[text](URL)`.
- Each citation should directly correspond to a source URL.
- For **local documents (not website link URLs)**, **do not** embed the citation as a link. Instead, include only the reference text.
- Avoid using superscript numbers `[1]`, `[2]`, etc., as they can make the text harder to read.
- Ensure all citations are naturally integrated into the sentence.
</Citation Rules>

</Task>
"""

report_planner_query_writer_instructions = """You are performing research for a report.

<Report topic>
{topic}
</Report topic>

<Report organization>
{report_organization}
</Report organization>

<Task>
Your goal is to generate {number_of_queries} web search queries that will help gather information for planning the report sections.

The queries should:

1. Be related to the Report topic
2. Help satisfy the requirements specified in the report organization

Make the queries specific enough to find high-quality, relevant sources while covering the breadth needed for the report structure.
</Task>
"""
report_planner_instructions = """I want a plan for a report that is concise and focused.

<Report topic>
The topic of the report is:
{topic}
</Report topic>

<Report organization>
The report should follow this organization:
{report_organization}
</Report organization>

<Context>
Here is context to use to plan the sections of the report:
{context}
</Context>

<Available search providers>
The following search providers are available for this report:
{available_search_providers}
</Available search providers>

<Task>
Generate a list of sections for the report. Your plan should be tight and focused with NO overlapping sections or unnecessary filler.

For example, a good report structure might look like:
1/ overview of topic A
2/ overview of topic B
3/ comparison between A and B
4/ conclusion

**caution: do not include `introduction` and `conclusion` sections in the plan.**

Each section should have the fields:

- Name - Name for this section of the report.
- Description - Brief overview of the main topics covered in this section.
- Research - Whether to perform web research for this section of the report. (default: True, but `conclusion`, `summary`. or `introduction` sections should be False)
- Search Options - List of search providers to use for this section. Choose from the available providers listed above.
  {search_provider_descriptions}
- Content - The content of the section, which you will leave blank for now.

Choose appropriate search options based on the section topic and available search providers. Always include at least one search provider for each section that has Research=True.

Integration guidelines:
- Include examples and implementation details within main topic sections, not as separate sections
- Ensure each section has a distinct purpose with no content overlap
- Combine related concepts rather than separating them

Before submitting, review your structure to ensure it has no redundant sections and follows a logical flow.
</Task>

<Feedback>
Here is feedback on the report structure from review (if any):
{feedback}
</Feedback>
"""

query_writer_instructions = """You are an expert technical writer crafting targeted search queries that will gather comprehensive information for writing a technical report section.

<Report topic>
{topic}
</Report topic>

<Section topic>
{section_topic}
</Section topic>

<Search provider>
{search_provider}
</Search provider>

<Task>
Your goal is to generate {number_of_queries} search queries that will help gather comprehensive information above the section topic, specifically optimized for the {search_provider} search engine.

Customize your queries based on the search provider:

- "tavily"（一般的なウェブ検索）の場合：
  * 一般的で包括的なキーワードカバレッジを持つクエリを作成
  * 複数の関連概念をAND検索できるようなキーワードの組み合わせを使用
  * 例: "量子コンピュータ アルゴリズム 最適化"

- "arxiv"（学術論文検索）の場合：
  * 学術的な専門用語と研究概念に焦点を当てたクエリを作成
  * 研究領域の正確な用語と重要な著者名を含める
  * "特許"や"論文"などの一般的な単語は不要
  * 例: "quantum error correction superconducting qubits"

- "pubmed"（医学文献）の場合：
  * 正確な医学用語と疾患名を使用
  * MeSHタームに対応する専門的な医学用語を使用
  * "医学"や"治療"などの一般的な単語は不要
  * 例: "CRISPR/Cas9 gene editing cardiovascular applications"

- "exa"（詳細なウェブ検索）の場合：
  * 高い特異性を持つ詳細なクエリを作成
  * 具体的な用語や技術仕様を含める
  * 例: "tensorflow implementation transformer architecture performance optimization"

- "local"（ローカル文書のベクトル検索）の場合：
  * これはセマンティック（意味的）検索であることに注意
  * 正確な用語よりも、概念や意味を表す短いフレーズが効果的
  * 完全一致ではなく意味的な類似性でマッチングするため、同義語や関連概念も含める
  * 長すぎるクエリは避け、3〜5語程度の簡潔なクエリを作成
  * 例: "深層学習アーキテクチャ" より "ニューラルネットワーク設計" の方が効果的

- "google_patent"（特許の全文検索）の場合：
  * これは全文検索であることに注意
  * Tavilyと同様の形式を使用するが、単語数は3〜4語に絞る
  * 最も重要な技術的なキーワードのみを含める
  * "特許"や"patent"などの単語は含めない（すでに特許データベースを検索するため）
  * 例: "optical lattice clock strontium"
  * 別の例: "quantum computing error correction"

The queries should:
1. Be related to the topic
2. Examine different aspects of the topic
3. Use terminology and structure appropriate for the search provider

Make the queries specific enough to find high-quality, relevant sources.
</Task>
"""

section_writer_instructions = """Write one section of a research report.

<Task>
1. Review the report topic, section name, and section topic carefully.
2. If present, review any existing section content.
3. Then, look at the provided Source material.
4. Decide the sources that you will use it to write a report section.
5. Write the report section with inline citations.
</Task>

<Writing Guidelines>
- If existing section content is not populated, write from scratch
- If existing section content is populated, synthesize it with the source material
- Maximum word count: about {max_words}
- Use simple, clear language
- Use short paragraphs (2-3 sentences max)
- Use ## for section title (Markdown format)
</Writing Guidelines>

<Citation Rules>
- Use inline citations by embedding links in Markdown format: `[text](URL)`.
- Each citation should directly correspond to a source URL.
- For **local documents (not website link URLs)**, **do not** embed the citation as a link. Instead, include only the reference text.
- Avoid using superscript numbers `[1]`, `[2]`, etc., as they can make the text harder to read.
- Ensure all citations are naturally integrated into the sentence.
</Citation Rules>

<Final Check>
1. Verify that EVERY claim is grounded in the provided Source material and has an appropriate citation
2. Confirm each citation is used correctly and corresponds to the right source
3. Verify that citations are naturally integrated into the text
</Final Check>
"""


section_writer_inputs = """
<Report topic>
{topic}
</Report topic>

<Section name>
{section_name}
</Section name>

<Section topic>
{section_topic}
</Section topic>

<Existing section content (if populated)>
{section_content}
</Existing section content>

<Source material>
{context}
</Source material>
"""

section_grader_instructions = """Review a report section relative to the specified topic:

<Report topic>
{topic}
</Report topic>

<section topic>
{section_topic}
</section topic>

<section content>
{section}
</section content>

<task>
Evaluate whether the section content adequately addresses the section topic.

If the section content does not adequately address the section topic, generate {number_of_follow_up_queries} follow-up search queries to gather missing information.
</task>

<format>
    grade: Literal["pass","fail"] = Field(
        description="Evaluation result indicating whether the response meets requirements ('pass') or needs revision ('fail')."
    )
    follow_up_queries: List[SearchQuery] = Field(
        description="List of follow-up search queries.",
    )
</format>
"""


deep_research_planner_instructions = """
あなたは研究プランナーです。以下のセクションの内容を分析し、より深く掘り下げるべき {breadth} 個のサブトピックを特定してください。

<Report Topic>
{topic}
</Report Topic>

<Section Name>
{section_name}
</Section Name>

<Section Content>
{section_content}
</Section Content>

<Current Depth>
{current_depth}
</Current Depth>

<Task>
このセクションの内容をより深く探索するための {breadth} 個の具体的なサブトピックを特定してください。
各サブトピックについて：
1. サブトピックの名前
2. このサブトピックが重要な理由
3. このサブトピックについて調査すべき具体的な側面や質問

サブトピックは互いに重複せず、元のセクションの内容を深く掘り下げるものである必要があります。
各サブトピックは正確で具体的であるべきです。
</Task>
"""

deep_research_queries_instructions = """あなたは検索クエリ作成の専門家です。以下のサブトピックに関する詳細情報を収集するための検索クエリを生成してください。

<Report Topic>
{topic}
</Report Topic>

<Section Name>
{section_name}
</Section Name>

<Subtopic>
名前: {subtopic_name}
説明: {subtopic_description}
</Subtopic>

<Search Provider>
{search_provider}
</Search Provider>

<Task>
このサブトピックについて深く掘り下げるための {number_of_queries} 個の検索クエリを生成してください。
クエリは以下の特性を持つべきです：
1. 具体的で明確であること
2. サブトピックの異なる側面をカバーすること
3. 主題に関連する最新かつ詳細な情報を返す可能性が高いこと
4. 指定された検索プロバイダ ({search_provider}) に最適化されていること

検索プロバイダごとにクエリを最適化してください：

- "tavily"（一般的なウェブ検索）の場合：
  * 一般的で包括的なキーワードカバレッジを持つクエリを作成
  * 複数の関連概念をAND検索できるようなキーワードの組み合わせを使用
  * 例: "量子コンピュータ アルゴリズム 最適化"

- "arxiv"（学術論文検索）の場合：
  * 学術的な専門用語と研究概念に焦点を当てたクエリを作成
  * 研究領域の正確な用語と重要な著者名を含める
  * "特許"や"論文"などの一般的な単語は不要
  * 例: "quantum error correction superconducting qubits"

- "pubmed"（医学文献）の場合：
  * 正確な医学用語と疾患名を使用
  * MeSHタームに対応する専門的な医学用語を使用
  * "医学"や"治療"などの一般的な単語は不要
  * 例: "CRISPR/Cas9 gene editing cardiovascular applications"

- "exa"（詳細なウェブ検索）の場合：
  * 高い特異性を持つ詳細なクエリを作成
  * 具体的な用語や技術仕様を含める
  * 例: "tensorflow implementation transformer architecture performance optimization"

- "local"（ローカル文書のベクトル検索）の場合：
  * これはセマンティック（意味的）検索であることに注意
  * 正確な用語よりも、概念や意味を表す短いフレーズが効果的
  * 完全一致ではなく意味的な類似性でマッチングするため、同義語や関連概念も含める
  * 長すぎるクエリは避け、3〜5語程度の簡潔なクエリを作成
  * 例: "深層学習アーキテクチャ" より "ニューラルネットワーク設計" の方が効果的

- "google_patent"（特許の全文検索）の場合：
  * これは全文検索であることに注意
  * Tavilyと同様の形式を使用するが、単語数は3〜4語に絞る
  * 最も重要な技術的なキーワードのみを含める
  * "特許"や"patent"などの単語は含めない（すでに特許データベースを検索するため）
  * 例: "optical lattice clock strontium"
  * 別の例: "quantum computing error correction"

各クエリは単独で使用でき、高品質なソース情報を見つけられるものにしてください。
</Task>
"""

deep_research_writer_instructions = """あなたは技術文書作成の専門家です。以下の情報を使用して、レポートのサブセクションを作成してください。

<Report Topic>
{topic}
</Report Topic>

<Main Section>
{section_name}
</Main Section>

<Subtopic>
{subtopic}
</Subtopic>

<Search Results>
{search_results}
</Search Results>

<Task>
提供された検索結果を使用して、このサブトピックに関する詳細なサブセクションを作成してください。
サブセクションは以下の特性を持つべきです：
1. マークダウン形式で、### レベルのヘッダー（サブセクションタイトル）から始める
2. 明確で簡潔な表現を使用する
3. 検索結果に基づいた事実を提示する
4. 情報源は必ず引用し、以下のルールに従ったインライン引用を使用する
5. 約 {max_words} 語以内に収める

<Citation Rules>
- Use inline citations by embedding links in Markdown format: `[text](URL)`.
- Each citation should directly correspond to a source URL.
- For **local documents (not website link URLs)**, **do not** embed the citation as a link. Instead, include only the reference text.
- Avoid using superscript numbers `[1]`, `[2]`, etc., as they can make the text harder to read.
- Ensure all citations are naturally integrated into the sentence.
</Citation Rules>

サブセクションは元のセクションの一部として読めるようになっていることが重要です。
引用リストや「出典」セクションは含めないでください。引用はすべて本文中に埋め込んでください。
</Task>
"""


conclusion_writer_instructions = """You are an expert technical writer tasked with creating a conclusion for a research report.

<Report topic>
{topic}
</Report topic>

<Is topic a question>
{is_question}
</Is topic a question>

<Section content>
{sections_content}
</Section content>

<Task>
Your task depends on whether the report topic is a question:

If the topic is a question (is_question=True):
1. Synthesize the information from all sections to provide a clear, direct answer to the question.
2. Ensure your answer is well-supported by the content in the sections.
3. Keep your answer concise, focusing on the most relevant information.
4. Stay within about {max_words} words.

If the topic is not a question (is_question=False):
1. Summarize the key findings and insights from all sections of the report.
2. Aim to provide a cohesive synthesis rather than just repeating section summaries.
3. Include one structural element (either a bullet list or a small table) that distills the main points.
4. Stay within about {max_words} words.

In both cases:
- Use clear, direct language
- Focus on the most important information
- Be objective and evidence-based
- Write in the specified language

<Citation Rules>
- Use inline citations by embedding links in Markdown format: `[text](URL)`.
- Each citation should directly correspond to a source URL.
- For **local documents (not website link URLs)**, **do not** embed the citation as a link. Instead, include only the reference text.
- Avoid using superscript numbers `[1]`, `[2]`, etc., as they can make the text harder to read.
- Ensure all citations are naturally integrated into the sentence.
</Citation Rules>
</Task>
"""


question_to_plan_instructions = """You are helping to plan a research report that answers a specific question.

<User Question>
{topic}
</User Question>

<Report organization>
{report_organization}
</Report organization>

<Context>
{context}
</Context>

<Available search providers>
The following search providers are available for this report:
{available_search_providers}
</Available search providers>

<Task>
Create a plan for a report that will effectively answer the user's question. The plan should include sections that, when combined, will provide a comprehensive answer.

1. Analyze the question to identify key components that need to be addressed
2. Design logical sections that progress toward answering the question
3. Ensure no critical aspects are omitted
4. Exclude any "conclusion" section - this will be generated separately
5. Focus on gathering factual information needed to answer the question

Each section should have the fields:
- Name - Name for this section of the report
- Description - Brief overview of what this section will explore and how it contributes to answering the question
- Research - Whether to perform research for this section of the report (usually true for all sections except summary sections)
- Search Options - List of search providers to use for this section. Choose from the available providers listed above.
  {search_provider_descriptions}
- Content - The content of the section, which you will leave blank for now

Choose appropriate search options based on the section topic and available search providers. Always include at least one search provider for each section that has Research=True.

Do NOT include "Introduction" or "Conclusion" sections in the plan.
</Task>
"""
