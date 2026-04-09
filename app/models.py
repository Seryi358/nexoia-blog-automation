from pydantic import BaseModel


class ArticleGenerated(BaseModel):
    title: str
    slug: str
    meta_description: str
    focus_keyword: str
    category: str
    cluster: str
    content_html: str
    word_count: int
    internal_links: list[str] = []
    tags: list[str] = []


class ImageGenerated(BaseModel):
    task_id: str
    url: str | None = None
    state: str = "pending"


class PublishResult(BaseModel):
    wp_post_id: int
    url: str
    title: str
    success: bool = True
