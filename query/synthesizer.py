from groq import Groq

from models.types import QueryResult


MAX_CONTEXT_RESULTS = 20
MAX_CONTEXT_CHARS = 900
MAX_PROMPT_CHARS = 6000


class Synthesizer:
    def __init__(
        self,
        api_key: str,
        model: str,
    ):
        self.client = Groq(api_key=api_key)
        self.model = model

    def synthesize(
        self,
        query: str,
        results: list[QueryResult],
    ) -> str:
        context = self._build_context(results)

        if len(context) > MAX_PROMPT_CHARS:
            context = context[:MAX_PROMPT_CHARS]
            last_newline = context.rfind("\n")
            if last_newline != -1:
                context = context[:last_newline]
            context += "\n... [truncated repository context]"

        prompt = f"""
You are an AI software engineer.

Answer the user's question using only the repository context provided below.

Use clean Markdown formatting in your response.
Structure the answer with:
- A short summary
- A clear list of relevant files and line ranges
- A concise conclusion

User question:
{query}

Repository context:
{context}

Requirements:
- Ground the answer in repository evidence.
- Mention file paths and line ranges when available.
- Do not invent repository facts.
- If the context is insufficient, say so clearly.
- Use markdown headings, bullet lists, and short paragraphs.
- Keep the response readable and professional.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You answer questions about software "
                        "repositories using retrieved evidence."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
        )

        return response.choices[0].message.content or ""

    @staticmethod
    def _build_context(
        results: list[QueryResult],
    ) -> str:
        if not results:
            return "No repository context was retrieved."

        if len(results) > MAX_CONTEXT_RESULTS:
            results = results[:MAX_CONTEXT_RESULTS]

        sections = []

        for result in results:
            section = [
                f"Source: {result.source}",
                f"Symbol: {result.symbol_id}",
            ]

            if result.file_path:
                section.append(f"File: {result.file_path}")

            if result.metadata:
                section.append(f"Metadata: {result.metadata}")

            if result.start_line is not None:
                section.append(
                    f"Lines: {result.start_line}-{result.end_line}"
                )

            if result.content:
                section.append(
                    f"Code:\n{Synthesizer._truncate_content(result.content)}"
                )

            if result.relationships:
                section.append(
                    f"Relationships:\n"
                    f"{result.relationships}"
                )

            sections.append("\n".join(section))

        return "\n\n---\n\n".join(sections)

    @staticmethod
    def _truncate_content(content: str) -> str:
        if len(content) <= MAX_CONTEXT_CHARS:
            return content

        truncated = content[:MAX_CONTEXT_CHARS]
        last_newline = truncated.rfind("\n")
        if last_newline != -1:
            truncated = truncated[:last_newline]

        return f"{truncated}\n... [truncated]"
