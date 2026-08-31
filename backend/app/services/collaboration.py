"""Collaboration service — comments, mentions, reviews, and real-time updates."""

import re
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/collaborate", tags=["Collaboration"])


# ── Models ────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    parent_id: Optional[str] = None  # For threaded replies
    mentions: Optional[list[str]] = None  # @user mentions

class CommentResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    author_id: str
    author_name: str
    content: str
    parent_id: Optional[str]
    mentions: list[str]
    replies_count: int
    created_at: str
    updated_at: str

class DiscussionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    entity_type: str
    entity_id: str

class DiscussionResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    entity_type: str
    entity_id: str
    author_id: str
    comments_count: int
    participants: list[str]
    status: str  # open, resolved, archived
    created_at: str


# ── In-Memory Store ───────────────────────────────────────────────────

@dataclass
class Comment:
    id: str
    entity_type: str
    entity_id: str
    author_id: str
    author_name: str
    content: str
    parent_id: Optional[str] = None
    mentions: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at


@dataclass
class Discussion:
    id: str
    title: str
    description: Optional[str]
    entity_type: str
    entity_id: str
    author_id: str
    status: str = "open"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class CollaborationStore:
    """In-memory collaboration store."""

    def __init__(self):
        self.comments: dict[str, Comment] = {}
        self.discussions: dict[str, Discussion] = {}

    def add_comment(self, entity_type: str, entity_id: str, author_id: str,
                    author_name: str, content: str, parent_id: Optional[str] = None) -> Comment:
        comment_id = f"cmt_{uuid.uuid4().hex[:12]}"
        mentions = self._extract_mentions(content)

        comment = Comment(
            id=comment_id,
            entity_type=entity_type,
            entity_id=entity_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
            parent_id=parent_id,
            mentions=mentions,
        )
        self.comments[comment_id] = comment
        return comment

    def get_comments(self, entity_type: str, entity_id: str,
                     parent_id: Optional[str] = None) -> list[Comment]:
        results = []
        for c in self.comments.values():
            if c.entity_type == entity_type and c.entity_id == entity_id:
                if parent_id is None:
                    if c.parent_id is None:  # Top-level comments
                        results.append(c)
                elif c.parent_id == parent_id:
                    results.append(c)
        return sorted(results, key=lambda x: x.created_at)

    def reply_to_comment(self, comment_id: str, author_id: str, author_name: str,
                         content: str) -> Optional[Comment]:
        parent = self.comments.get(comment_id)
        if not parent:
            return None

        return self.add_comment(
            entity_type=parent.entity_type,
            entity_id=parent.entity_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
            parent_id=comment_id,
        )

    def resolve_comment(self, comment_id: str) -> bool:
        comment = self.comments.get(comment_id)
        if comment:
            comment.content += "\n\n[RESOLVED]"
            comment.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def search_mentions(self, user_id: str) -> list[Comment]:
        """Find all comments mentioning a user."""
        return [
            c for c in self.comments.values()
            if user_id in c.mentions
        ]

    def get_activity_feed(self, entity_type: str, entity_id: str,
                          limit: int = 20) -> list[dict]:
        """Get combined activity feed for an entity."""
        comments = self.get_comments(entity_type, entity_id)
        feed = []
        for c in comments[-limit:]:
            feed.append({
                "type": "comment",
                "id": c.id,
                "author": c.author_name,
                "content": c.content[:200],
                "timestamp": c.created_at,
                "mentions": c.mentions,
            })
        return sorted(feed, key=lambda x: x["timestamp"], reverse=True)

    def create_discussion(self, title: str, entity_type: str, entity_id: str,
                          author_id: str, description: Optional[str] = None) -> Discussion:
        disc_id = f"disc_{uuid.uuid4().hex[:12]}"
        discussion = Discussion(
            id=disc_id,
            title=title,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            author_id=author_id,
        )
        self.discussions[disc_id] = discussion
        return discussion

    def get_discussions(self, entity_type: str, entity_id: str) -> list[Discussion]:
        return [
            d for d in self.discussions.values()
            if d.entity_type == entity_type and d.entity_id == entity_id
        ]

    def _extract_mentions(self, text: str) -> list[str]:
        """Extract @mentions from text."""
        return re.findall(r"@(\w+)", text)


collab_store = CollaborationStore()


# ── API Endpoints ─────────────────────────────────────────────────────

@router.post("/{entity_type}/{entity_id}/comments", response_model=CommentResponse,
             status_code=201, summary="Add a comment")
async def add_comment(entity_type: str, entity_id: str, comment: CommentCreate,
                      author_id: str = "usr_current", author_name: str = "Current User"):
    """
    Add a comment to any entity. Supports:
    - **Threaded replies** via `parent_id`
    - **@mentions** (e.g., @john) for notifications
    - **Markdown-style formatting**
    """
    c = collab_store.add_comment(
        entity_type=entity_type,
        entity_id=entity_id,
        author_id=author_id,
        author_name=author_name,
        content=comment.content,
        parent_id=comment.parent_id,
    )
    return CommentResponse(
        id=c.id, entity_type=c.entity_type, entity_id=c.entity_id,
        author_id=c.author_id, author_name=c.author_name, content=c.content,
        parent_id=c.parent_id, mentions=c.mentions, replies_count=0,
        created_at=c.created_at, updated_at=c.updated_at,
    )


@router.get("/{entity_type}/{entity_id}/comments",
             response_model=list[CommentResponse], summary="List comments")
async def list_comments(entity_type: str, entity_id: str,
                        parent_id: Optional[str] = Query(None)):
    """List comments for an entity. Filter by parent_id for replies."""
    comments = collab_store.get_comments(entity_type, entity_id, parent_id)
    return [
        CommentResponse(
            id=c.id, entity_type=c.entity_type, entity_id=c.entity_id,
            author_id=c.author_id, author_name=c.author_name, content=c.content,
            parent_id=c.parent_id, mentions=c.mentions, replies_count=0,
            created_at=c.created_at, updated_at=c.updated_at,
        )
        for c in comments
    ]


@router.post("/comments/{comment_id}/reply", response_model=CommentResponse,
             status_code=201, summary="Reply to a comment")
async def reply_comment(comment_id: str, comment: CommentCreate,
                        author_id: str = "usr_current", author_name: str = "Current User"):
    """Reply to an existing comment (creates a thread)."""
    c = collab_store.reply_to_comment(
        comment_id=comment_id,
        author_id=author_id,
        author_name=author_name,
        content=comment.content,
    )
    if not c:
        from fastapi import HTTPException
        raise HTTPException(404, "Comment not found")

    return CommentResponse(
        id=c.id, entity_type=c.entity_type, entity_id=c.entity_id,
        author_id=c.author_id, author_name=c.author_name, content=c.content,
        parent_id=c.parent_id, mentions=c.mentions, replies_count=0,
        created_at=c.created_at, updated_at=c.updated_at,
    )


@router.post("/comments/{comment_id}/resolve", summary="Resolve a comment")
async def resolve_comment(comment_id: str):
    """Mark a comment as resolved."""
    success = collab_store.resolve_comment(comment_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(404, "Comment not found")
    return {"status": "resolved", "comment_id": comment_id}


@router.get("/mentions/{user_id}", summary="Find mentions of a user")
async def find_mentions(user_id: str):
    """Find all comments mentioning a specific user."""
    comments = collab_store.search_mentions(user_id)
    return {
        "user_id": user_id,
        "total": len(comments),
        "mentions": [
            {"comment_id": c.id, "entity": f"{c.entity_type}/{c.entity_id}",
             "author": c.author_name, "content": c.content[:200], "date": c.created_at}
            for c in comments
        ],
    }


@router.get("/{entity_type}/{entity_id}/activity",
             summary="Activity feed for an entity")
async def activity_feed(entity_type: str, entity_id: str,
                        limit: int = Query(20, ge=1, le=100)):
    """Get combined activity feed (comments, decisions, changes)."""
    return collab_store.get_activity_feed(entity_type, entity_id, limit)


@router.post("/discussions", status_code=201, summary="Create a discussion")
async def create_discussion(discussion: DiscussionCreate,
                            author_id: str = "usr_current"):
    """Create a discussion thread for an entity."""
    d = collab_store.create_discussion(
        title=discussion.title,
        entity_type=discussion.entity_type,
        entity_id=discussion.entity_id,
        author_id=author_id,
        description=discussion.description,
    )
    return {
        "id": d.id, "title": d.title, "description": d.description,
        "entity_type": d.entity_type, "entity_id": d.entity_id,
        "status": d.status, "created_at": d.created_at,
    }


@router.get("/{entity_type}/{entity_id}/discussions",
             summary="List discussions for an entity")
async def list_discussions(entity_type: str, entity_id: str):
    """List all discussions for an entity."""
    discussions = collab_store.get_discussions(entity_type, entity_id)
    return [
        {"id": d.id, "title": d.title, "status": d.status, "created_at": d.created_at}
        for d in discussions
    ]
