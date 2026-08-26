
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class DesignVersion(Base):
    """
    Persisted canonical design version.

    This stores an immutable snapshot of the canonical design produced after
    generation/conversion. Structural validation and engineering approval are
    intentionally separate concerns.
    """

    __tablename__ = "design_versions"

    __table_args__ = (
        UniqueConstraint(
            "site_id",
            "version",
            name="uq_design_versions_site_version",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    design_specification_id: Mapped[int] = mapped_column(
        ForeignKey("design_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("design_candidates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    schema_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0.0",
    )

    design_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="created",
        index=True,
    )

    # Complete canonical DesignVersion snapshot.
    design_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )