"""Design Snapshot model — tracks design iterations and changes over time."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class DesignSnapshot(Base):
    """
    Immutable snapshot of a design at a point in time.
    Enables tracking what changed between iterations.
    """
    __tablename__ = "design_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    design_id: Mapped[int] = mapped_column(
        ForeignKey("generated_designs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    iteration: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    label: Mapped[str] = mapped_column(String(200), nullable=False, default="snapshot")
    design_json: Mapped[str] = mapped_column(Text, nullable=False)
    analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    rules_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
