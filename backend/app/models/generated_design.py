from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class GeneratedDesign(Base):
    """
    One generated design candidate produced from a ConstraintSet via the
    local generation pipeline (Steps 14-15), together with the structural
    analysis and Sphere rule evaluation computed for it.

    All three payloads (design, analysis, rules) are stored together
    because they are always produced and read as one unit.
    """

    __tablename__ = "generated_designs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    constraint_set_id: Mapped[int] = mapped_column(
        ForeignKey("constraint_sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    candidate_id: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="generated",
    )

    # CanonicalDesignVersion, StructuralAnalysisResult, StandardsEvaluation
    # serialized as JSON text (consistent with the rest of the codebase).
    design_json: Mapped[str] = mapped_column(Text, nullable=False)
    analysis_json: Mapped[str] = mapped_column(Text, nullable=False)
    rules_json: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
