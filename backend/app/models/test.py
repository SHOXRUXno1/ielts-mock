from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Test(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "tests"

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(default=False)
    type: Mapped[str] = mapped_column(String(20), default="academic", server_default="academic")
    book_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    book_slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True, server_default="")
    test_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    __table_args__ = (
        UniqueConstraint("book_slug", "test_number", name="uq_book_test"),
    )

    sections: Mapped[list["Section"]] = relationship(back_populates="test", order_by="Section.order", passive_deletes=True)
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="test", passive_deletes=True)
    section_settings: Mapped[list["TestSectionSettings"]] = relationship(
        back_populates="test",
        order_by="TestSectionSettings.section_type",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    practice_part_settings: Mapped[list["PracticePartSettings"]] = relationship(
        back_populates="test",
        order_by="(PracticePartSettings.section_type, PracticePartSettings.part_number)",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
