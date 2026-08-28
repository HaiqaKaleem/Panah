from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ConstraintSetRecord(Base):
    """
    Persisted ConstraintSet (Step 13).

    This is the canonical requirements object shared by generation and
    structural validation. It is intentionally independent of the older
    SiteProfile/DesignSpecification pipeline so it can be evolved without
    risk to that existing flow.
    """

    __tablename__ = "constraint_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version: Mapped[str] = mapped_column(String(100), nullable=False)

    # Complete validated ConstraintSet snapshot.
    constraint_json: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
