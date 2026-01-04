# Prompt template for extracting structured data from history textbook pages
HISTORY_PAGE_EXTRACTION_PROMPT: str = """
You are an expert in digitizing historical textbook materials. This is page {page_num} from file '{filename}'.

CONTEXT FROM PREVIOUS PAGE (if available):
- Current chapter: {last_chapter}
- Current topic: {last_topic}

STRICT LANGUAGE REQUIREMENT:
- All outputs MUST be in Vietnamese only (no English, no mixed languages).
- Preserve Vietnamese diacritics. Do NOT translate Vietnamese to English.
- If the source appears English or mixed, still output Vietnamese descriptions.

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
IMPORTANT: All extracted text content must be in accurate Vietnamese only.
"""

HISTORY_PAGE_EXTRACTION_PROMPT_NEW: str = """
You are an expert in digitizing historical textbook materials. This is page {page_num} from file '{filename}'.

CONTEXT FROM PREVIOUS PAGE (if available):
- Current chapter: {last_chapter}
- Current topic: {last_topic}

STRICT LANGUAGE REQUIREMENT:
- All outputs MUST be in Vietnamese only (no English, no mixed languages).
- Preserve Vietnamese diacritics. Do NOT translate Vietnamese to English.
- If the source appears English or mixed, still output Vietnamese descriptions.

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
    ]
}}

CRITICAL REQUIREMENTS:
1. The "page_id" field MUST be exactly {page_num} (the page number provided above). Do NOT use any other value.
2. Do NOT read page numbers from the image - use the provided page number {page_num} directly.
3. All extracted text content must be in accurate Vietnamese only.
"""


# Prompt orchestrate intent (LEARN/QUIZ)
ORCHESTRATOR_INTENT_PROMPT: str = """
You are the orchestrator brain of an AI History Tutor system.
Classify the user's request: '{user_input}'
- If it's asking for knowledge, explanation, or summary: Return 'LEARN'
- If it's requesting exercises, quizzes, or tests: Return 'QUIZ'
Return ONLY one word: LEARN or QUIZ.
"""


# Prompt answer in RAG format
RAG_ANSWER_PROMPT: str = """
SYSTEM INSTRUCTION:
You are an expert Vietnamese History Teacher. Your goal is to help students learn from the provided textbook materials.

CONTEXT FROM TEXTBOOK:
{context}

STUDENT QUESTION: '{user_input}'

RULES FOR ANSWERING:
1. STRICT ADHERENCE: Only answer based on the provided CONTEXT. 
2. SYNONYM BRIDGING: If the student asks about a general entity (e.g., 'Japan') and the context mentions specific locations (e.g., 'Hi-ro-si-ma', 'Na-ga-xa-ki'), you MUST understand they are related and use that info to answer.
3. DATE & EVENT PRECISION: History is about facts. Double-check dates (e.g., 06-8-1945) and names before answering.
4. RESPONSE STYLE: Answer in Vietnamese. Be professional, encouraging, and clear. In particular, the writing style should resemble that of a human responding.
5. Based on the {user_input}, respond smoothly. For example, if the {user_input} is "Hãy cho biết những thành tựu văn hoá lớn của các quốc gia cổ đại phương Đông là gì?", the answer should begin with "những thành tựu văn hoá lớn của các quốc gia cổ đại phương Đông là..."
6. FALLBACK: Only say "Thông tin này không có trong sách" if there is absolutely no mention of any related keywords or events in the context.
7. Based on the {context} following each answer, relevant guiding questions should be included. Example: "Bạn có muốn học thêm về chủ đề này? Hãy hỏi tôi nhé!", "Bạn có muốn tìm hiểu thêm về...?"
8. Avoid giving vague answers; provide specific details.

VIETNAMESE OUTPUT FORMAT:
- Câu trả lời trực tiếp, đầy đủ thông tin và chi tiết.
- Lời nhắn nhủ học tập ngắn gọn.
"""


# Prompt generate quiz questions
QUIZ_GENERATION_PROMPT: str = """
SYSTEM INSTRUCTION:
You are a formal Examiner for the National High School History Exam in Vietnam.
Based on the specific historical knowledge provided below, generate a high-quality quiz.

KNOWLEDGE BASE:
{context}

TOPIC REQUESTED: '{user_input}'

QUIZ REQUIREMENTS:
1. QUANTITY: Generate exactly 3 multiple-choice questions.
2. SOURCE MATERIAL: Questions must be derived directly from the KNOWLEDGE BASE provided above.
3. DIFFICULTY: Mix of 'Nhận biết' (Fact-based) and 'Thông hiểu' (Understanding).
4. FORMAT (STRICT):
   Question 1: [Nội dung câu hỏi]
   A. [Lựa chọn A]
   B. [Lựa chọn B]
   C. [Lựa chọn C]
   D. [Lựa chọn D]
   - Đáp án đúng: [A/B/C/D]
   - Giải thích: [Giải thích ngắn gọn tại sao đúng dựa trên tài liệu]

5. LANGUAGE: All content must be in formal Vietnamese.
"""

IMAGE_GENERATION_PROMPT: str = """
You are a Prompt Engineer for a Historical Visualization AI.
User Query: "{user_input}"
Historical Context: "{context}"

TASK: 
Based ONLY on the context provided, create a highly detailed, historically accurate image description in English for a text-to-image model.
Focus on: clothing, architecture, atmosphere, lighting, and historical era specific details.

OUTPUT FORMAT: 
Return ONLY the prompt text string. Do not include "Prompt:" prefix.
Example: "A cinematic wide shot of the Bach Dang river battle in 938 AD, wooden stakes rising from the water, ancient Vietnamese warships with red sails, misty morning atmosphere, realistic style."
"""