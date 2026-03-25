# 모든 모델을 여기서 import하여 Alembic이 감지할 수 있도록 함
from app.NewsBase.models.user import User
from app.NewsBase.models.news import News
from app.NewsBase.models.news_comment import NewsComment

__all__ = ["User", "News", "NewsComment"]
