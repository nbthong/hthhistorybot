# Prompt template for extracting structured data from history textbook pages
HISTORY_PAGE_EXTRACTION_PROMPT: str = """
You are an expert in digitizing historical textbook materials. This is page {page_num} from file '{filename}'.

CONTEXT FROM PREVIOUS PAGE (if available):
- Current chapter: {last_chapter}
- Current topic: {last_topic}

YOUR TASK:
1. Analyze the image of page {page_num}.
2. If this page does NOT contain a new Chapter or Topic title, reuse the context from the previous page.
3. If there is a new title, update it accordingly.
4. REQUIRED FORMAT: 
   - Chapter must have prefix 'Chương X: ...' (Vietnamese format)
   - Topic must have prefix 'Bài Y. ...' (Vietnamese format)

Return JSON with the following structure:
{{
    "page_info": {{
        "page_id": {page_num},
        "type": "CONTENT | TOC | GLOSSARY | APPENDIX",
        "chapter": "Chương X: [Tên chương]",
        "topic": "Bài Y. [Tên bài học]"
    }},
    "content_segments": [
        {{
            "heading": "Tiêu đề mục nhỏ",
            "text": "Văn bản thô",
            "table_markdown": "Markdown Table nếu có"
        }}
    ],
    "visual_analysis": [...],
    "rich_metadata": {{
        "summary": "Tóm tắt trang",
        "keywords": ["từ khóa"],
        "suggested_questions": ["Câu hỏi"]
    }}
}}
IMPORTANT: All extracted text content must be in accurate Vietnamese.
"""


# Prompt orchestrate intent (LEARN/QUIZ)
ORCHESTRATOR_INTENT_PROMPT: str = """
You are the orchestrator brain of an AI History Tutor system.
Classify the user's request: '{user_input}'
- If it's asking for knowledge, explanation, or summary: Return 'LEARN'
- If it's requesting exercises, quizzes, or tests: Return 'QUIZ'
Return only one word.
"""


# Prompt answer in RAG format
RAG_ANSWER_PROMPT: str = """
Based on the following textbook materials:
{context}

Answer the student's question: '{user_input}'
Requirements: 
- Respond in a friendly and accurate manner
- Cite page numbers from the textbook when possible
- Answer in Vietnamese language
"""


# Prompt generate quiz questions
QUIZ_GENERATION_PROMPT: str = """
Based on this historical knowledge:
{context}

Generate a set of 3 multiple-choice questions for students about the topic: '{user_input}'.
Format: Question -> 4 options -> Correct answer & Explanation.
All content must be in Vietnamese language.
"""