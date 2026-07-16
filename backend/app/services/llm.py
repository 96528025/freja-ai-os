import json
import re

from openai import OpenAI

from app.core.config import Settings
from app.services.embeddings import deterministic_embedding


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def classify_idea(self, content: str) -> dict[str, object]:
        if not self.client:
            return self._heuristic_classification(content)
        response = self.client.responses.create(
            model=self.settings.openai_model,
            input=(
                "Classify this personal idea. Return JSON with title (Chinese or source language), "
                "category, and 2-5 lowercase tags. No markdown.\n\n" + content
            ),
        )
        try:
            return json.loads(response.output_text)
        except json.JSONDecodeError:
            return self._heuristic_classification(content)

    def create_chinese_brief(
        self,
        items: list[dict[str, object]],
        *,
        preferences: dict[str, object] | None = None,
    ) -> str:
        if not items:
            return "# 今日 AI 简报\n\n今天暂未收集到新条目。"
        if not self.client:
            lines = ["# 今日 AI 简报", "", "> 自动采集完成。配置 OpenAI API Key 后将启用中文摘要、去重与智能排序。", ""]
            for index, item in enumerate(items[:20], 1):
                lines.extend(
                    [
                        f"## {index}. {item['title']}",
                        f"来源：{item.get('source', 'unknown')}",
                        f"[{item.get('url', '查看原文')}]({item.get('url', '')})",
                        "",
                    ]
                )
            return "\n".join(lines)
        response = self.client.responses.create(
            model=self.settings.openai_model,
            input=(
                "你是 Freja 的研究编辑。将以下 AI 新闻去重，按影响力排序，输出简洁中文 Markdown。"
                "这是一份私人简报，不要试图覆盖所有行业新闻。优先保留符合用户兴趣、会影响其产品决策、"
                "开发工作或认知判断的信号；弱相关的公司宣传、重复报道和泛泛入门内容应省略。"
                "最多输出 5 条，也可以少于 5 条，绝不为了凑数保留弱相关内容；保留原文链接；"
                "分成核心动态、开发工具、值得关注三个小节。"
                "每条固定包含：发生了什么、为什么值得用户关注；确有实际行动时再增加“可以做什么”。"
                "严格区分来源平台指标与原文站内指标：points/comments/score 只属于 source 指定的平台，"
                "必须明确写出平台名和原字段含义，禁止改写为原文章的点赞或评论。"
                "每条若提供 occurred_at，必须以 YYYY-MM-DD 明确标注发布日期；不要把采集时间当发布日期。"
                "候选已按时效分层：优先使用过去72小时内容，仅在数量不足时使用最近7天内容；"
                "不得把较旧的补充内容描述成刚刚发生，也不要为了凑满条数重复或扩写。"
                "不要推断输入中没有提供的热度、作者、日期、评价或事实；不确定的信息直接省略。"
                "直接输出 Markdown 正文，不要使用 ```markdown 代码围栏。\n\n"
                "用户偏好画像（来自其历史显式反馈；负向偏好必须尊重）：\n"
                + json.dumps(preferences or {}, ensure_ascii=False)
                + "\n\n候选新闻：\n"
                + json.dumps(items, ensure_ascii=False)
            ),
        )
        return self.strip_markdown_fence(response.output_text)

    @staticmethod
    def strip_markdown_fence(content: str) -> str:
        clean = content.strip()
        match = re.fullmatch(r"```(?:markdown|md)?\s*\n([\s\S]*?)\n```", clean, flags=re.I)
        return match.group(1).strip() if match else clean

    def embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.client:
            return [deterministic_embedding(text) for text in texts]
        result = self.client.embeddings.create(
            model=self.settings.openai_embedding_model,
            input=[text[:20_000] for text in texts],
        )
        return [item.embedding for item in sorted(result.data, key=lambda item: item.index)]

    def embedding(self, text: str) -> list[float]:
        return self.embeddings([text])[0]

    @staticmethod
    def _heuristic_classification(content: str) -> dict[str, object]:
        clean = re.sub(r"^(i have an idea|我有一个想法)[：:\s-]*", "", content, flags=re.I).strip()
        title = clean.split("。", 1)[0].split("\n", 1)[0][:80] or "Untitled idea"
        lowered = content.lower()
        tag_map = {
            "ai": ["ai", "llm", "agent", "模型", "智能"],
            "product": ["app", "product", "工具", "产品", "网站"],
            "learning": ["learn", "study", "学习", "课程"],
            "career": ["job", "career", "工作", "实习"],
        }
        tags = [tag for tag, words in tag_map.items() if any(word in lowered for word in words)]
        return {"title": title, "category": tags[0] if tags else "general", "tags": tags or ["idea"]}
