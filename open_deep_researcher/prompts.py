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
4. **Max number of queries is {number_of_queries}**

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
3. **Max number of queries is {number_of_queries}**

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

**caution: do not include `introduction` and `conclusion` sections in the plan.**

**caution: maximum number of sections is {max_sections}.**

Each section should have the fields:

- Name - Name for this section of the report.
- Description - Brief overview of the main topics covered in this section. 細かい指定は不要であり、「特に xxx について」などは不要です。
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

<Section name>
{section_name}
</Section name>

<Section topic>
{section_topic}
</Section topic>

<Search provider>
{search_provider}
</Search provider>

<Task>
- Your goal is to generate {number_of_queries} search queries that will help gather comprehensive information above the section topic, specifically optimized for the **{search_provider}** search engine.
- 異なる概念や具体を一つのクエリに含めるのではなく、それぞれのクエリに分けることで情報の質を高めることができます。
- Section name に関連する情報を収集するために必要な検索クエリを生成してください。

Customize your queries based on the search provider:

{query_generation_description}

The queries should:
1. Be related to the topic
2. Examine different aspects of the topic
3. Use terminology and structure appropriate for the search provider

Make the queries specific enough to find high-quality, relevant sources.
</Task>
"""


section_writer_instructions = """
あなたは技術文書作成の専門家です。以下の情報を使用して、レポートのセクションを作成してください。

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

<Task>
提供された検索結果を使用して、このトピックに関する詳細なセクションを作成してください。
セクションは以下の特性を持つべきです：
- マークダウン形式で、## レベルのヘッダー（セクションタイトル）から始める
- 明確で簡潔な表現を使用する
- 検索結果に基づいた事実を提示する
- 情報源は必ず引用し、以下のルールに従ったインライン引用を使用する
- 約 {max_words} 語以内に収める
- Do not write a summary. Write a detailed report section.
- Do not write conclusion.
- 必要な情報に加え、より深い洞察を提供することを目指してください。数値情報や具体的な例を使用して、情報を裏付けてください。
- より詳しく、より具体的に書くことを心がけてください。できるだけ重厚感のあるレポートが望ましいです。
- If an image and its description are provided, include them at the appropriate location in the report section.
- Insert the image using markdown tags. For example: \n`![description](URL)`\n
- Only include the image if necessary.
</Task>

<Citation Rules>
- Use inline citations by embedding links in Markdown format: `[text](URL)`.
- Each citation should directly correspond to a source URL.
- For **local documents (not website link URLs)**, **do not** embed the citation as a link. Instead, include only the reference text.
- Avoid using superscript numbers `[1]`, `[2]`, etc., as they can make the text harder to read.
- Ensure all citations are naturally integrated into the sentence.
</Citation Rules>

サブセクションは元のセクションの一部として読めるようになっていることが重要です。
引用リストや「出典」セクションは含めないでください。引用はすべて本文中に埋め込んでください。

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

{query_generation_description}

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
- マークダウン形式で、### レベルのヘッダー（サブセクションタイトル）から始める
- 明確で簡潔な表現を使用する
- 検索結果に基づいた事実を提示する
- 情報源は必ず引用し、以下のルールに従ったインライン引用を使用する
- 約 {max_words} 語以内に収める
- Do not write a summary. Write a detailed report section.
- Do not write conclusion.
- 必要な情報に加え、より深い洞察を提供することを目指してください。数値情報や具体的な例を使用して、情報を裏付けてください。
- より詳しく、より具体的に書くことを心がけてください。できるだけ重厚感のあるレポートが望ましいです。
- If an image and its description are provided, include them at the appropriate location in the report section.
- Insert the image using markdown tags. For example: \n`![description](URL)`\n
- Only include the image if necessary.
</Task>

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
- Do not write `Conclusion` as a section title. Instead, start with the content directly.

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

**caution: maximum number of sections is {max_sections}.**

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
