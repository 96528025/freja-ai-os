from app.core.config import Settings
from app.services.collectors.github import GitHubTrendingCollector
from app.services.collectors.reddit import RedditCollector
from app.services.collectors.rss import RSSCollector
from app.services.collectors.xiaohongshu import XiaohongshuCollector


def enabled_collectors(sources: list[str], settings: Settings):
    factories = {
        "reddit": lambda: RedditCollector(settings),
        "xiaohongshu": lambda: XiaohongshuCollector(settings),
        "github_trending": GitHubTrendingCollector,
        "openai_blog": lambda: RSSCollector("openai_blog", "OpenAI", "https://openai.com/news/rss.xml"),
        "anthropic_blog": lambda: RSSCollector("anthropic_blog", "Anthropic", "https://www.anthropic.com/rss.xml"),
        "google_deepmind_blog": lambda: RSSCollector("google_deepmind_blog", "Google DeepMind", "https://deepmind.google/blog/rss.xml"),
        "cursor_blog": lambda: RSSCollector("cursor_blog", "Cursor", "https://www.cursor.com/changelog/rss.xml"),
        "claude_code_blog": lambda: RSSCollector("claude_code_blog", "Claude Code", "https://github.com/anthropics/claude-code/releases.atom"),
        "codex_blog": lambda: RSSCollector("codex_blog", "Codex", "https://github.com/openai/codex/releases.atom"),
    }
    return [factories[source]() for source in sources if source in factories]
