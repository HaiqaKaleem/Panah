from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class DesignCandidate(Base):
    __tablename__ = "design_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

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

    # Candidate lifecycle is separate from structural validation.
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="generated",
    )

    # Provider/model identity and generation settings.
    generator_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    generator_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Structured candidate definition. This is the contract consumed by
    # future renderers/3D exporters and validators.
    candidate_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Links the candidate to the exact inputs used for generation.
    input_snapshot_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
