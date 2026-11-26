"""Slice 3: academic structure, offerings, teacher assignments, and enrollments

Revision ID: 0002_slice3_academic_structure
Revises: 0001_slice2_auth_schools
Create Date: 2026-11-26 11:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_slice3_academic_structure"
down_revision: str | Sequence[str] | None = "0001_slice2_auth_schools"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "schools",
        sa.Column(
            "terminology_config",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
    )

    op.create_table(
        "academic_years",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_academic_years_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_academic_years")),
        sa.UniqueConstraint("school_id", "name", name="uq_academic_years_school_name"),
    )
    op.create_index(
        op.f("ix_academic_years_school_id"),
        "academic_years",
        ["school_id"],
        unique=False,
    )

    op.create_table(
        "terms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["academic_year_id"],
            ["academic_years.id"],
            name=op.f("fk_terms_academic_year_id_academic_years"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_terms_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_terms")),
        sa.UniqueConstraint("academic_year_id", "name", name="uq_terms_year_name"),
    )
    op.create_index(op.f("ix_terms_school_id"), "terms", ["school_id"], unique=False)
    op.create_index(
        op.f("ix_terms_academic_year_id"), "terms", ["academic_year_id"], unique=False
    )

    op.create_table(
        "year_levels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_year_levels_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_year_levels")),
        sa.UniqueConstraint("school_id", "name", name="uq_year_levels_school_name"),
    )
    op.create_index(
        op.f("ix_year_levels_school_id"), "year_levels", ["school_id"], unique=False
    )

    op.create_table(
        "class_groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("year_level_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["academic_year_id"],
            ["academic_years.id"],
            name=op.f("fk_class_groups_academic_year_id_academic_years"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_class_groups_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["year_level_id"],
            ["year_levels.id"],
            name=op.f("fk_class_groups_year_level_id_year_levels"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_class_groups")),
        sa.UniqueConstraint(
            "school_id",
            "academic_year_id",
            "name",
            name="uq_class_groups_school_year_name",
        ),
    )
    op.create_index(
        op.f("ix_class_groups_school_id"), "class_groups", ["school_id"], unique=False
    )
    op.create_index(
        op.f("ix_class_groups_academic_year_id"),
        "class_groups",
        ["academic_year_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_class_groups_year_level_id"),
        "class_groups",
        ["year_level_id"],
        unique=False,
    )

    op.create_table(
        "subjects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_subjects_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subjects")),
        sa.UniqueConstraint("school_id", "code", name="uq_subjects_school_code"),
    )
    op.create_index(
        op.f("ix_subjects_school_id"), "subjects", ["school_id"], unique=False
    )

    op.create_table(
        "subject_offerings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("class_group_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("term_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["class_group_id"],
            ["class_groups.id"],
            name=op.f("fk_subject_offerings_class_group_id_class_groups"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_subject_offerings_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["subjects.id"],
            name=op.f("fk_subject_offerings_subject_id_subjects"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["term_id"],
            ["terms.id"],
            name=op.f("fk_subject_offerings_term_id_terms"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subject_offerings")),
        sa.UniqueConstraint(
            "school_id",
            "class_group_id",
            "subject_id",
            "term_id",
            name="uq_subject_offerings_scope",
        ),
    )
    op.create_index(
        op.f("ix_subject_offerings_school_id"),
        "subject_offerings",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_subject_offerings_class_group_id"),
        "subject_offerings",
        ["class_group_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_subject_offerings_subject_id"),
        "subject_offerings",
        ["subject_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_subject_offerings_term_id"),
        "subject_offerings",
        ["term_id"],
        unique=False,
    )

    op.create_table(
        "offering_teachers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("subject_offering_id", sa.Uuid(), nullable=False),
        sa.Column("teacher_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_offering_teachers_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subject_offering_id"],
            ["subject_offerings.id"],
            name=op.f("fk_offering_teachers_subject_offering_id_subject_offerings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["teacher_user_id"],
            ["users.id"],
            name=op.f("fk_offering_teachers_teacher_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_offering_teachers")),
        sa.UniqueConstraint(
            "subject_offering_id",
            "teacher_user_id",
            name="uq_offering_teachers_assignment",
        ),
    )
    op.create_index(
        op.f("ix_offering_teachers_school_id"),
        "offering_teachers",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_offering_teachers_subject_offering_id"),
        "offering_teachers",
        ["subject_offering_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_offering_teachers_teacher_user_id"),
        "offering_teachers",
        ["teacher_user_id"],
        unique=False,
    )

    op.create_table(
        "enrollments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("class_group_id", sa.Uuid(), nullable=False),
        sa.Column("subject_offering_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["academic_year_id"],
            ["academic_years.id"],
            name=op.f("fk_enrollments_academic_year_id_academic_years"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["class_group_id"],
            ["class_groups.id"],
            name=op.f("fk_enrollments_class_group_id_class_groups"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_enrollments_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_user_id"],
            ["users.id"],
            name=op.f("fk_enrollments_student_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subject_offering_id"],
            ["subject_offerings.id"],
            name=op.f("fk_enrollments_subject_offering_id_subject_offerings"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_enrollments")),
    )
    op.create_index(
        op.f("ix_enrollments_school_id"), "enrollments", ["school_id"], unique=False
    )
    op.create_index(
        op.f("ix_enrollments_student_user_id"),
        "enrollments",
        ["student_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_enrollments_academic_year_id"),
        "enrollments",
        ["academic_year_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_enrollments_class_group_id"),
        "enrollments",
        ["class_group_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_enrollments_subject_offering_id"),
        "enrollments",
        ["subject_offering_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_enrollments_subject_offering_id"), table_name="enrollments")
    op.drop_index(op.f("ix_enrollments_class_group_id"), table_name="enrollments")
    op.drop_index(op.f("ix_enrollments_academic_year_id"), table_name="enrollments")
    op.drop_index(op.f("ix_enrollments_student_user_id"), table_name="enrollments")
    op.drop_index(op.f("ix_enrollments_school_id"), table_name="enrollments")
    op.drop_table("enrollments")

    op.drop_index(
        op.f("ix_offering_teachers_teacher_user_id"), table_name="offering_teachers"
    )
    op.drop_index(
        op.f("ix_offering_teachers_subject_offering_id"), table_name="offering_teachers"
    )
    op.drop_index(
        op.f("ix_offering_teachers_school_id"), table_name="offering_teachers"
    )
    op.drop_table("offering_teachers")

    op.drop_index(op.f("ix_subject_offerings_term_id"), table_name="subject_offerings")
    op.drop_index(
        op.f("ix_subject_offerings_subject_id"), table_name="subject_offerings"
    )
    op.drop_index(
        op.f("ix_subject_offerings_class_group_id"), table_name="subject_offerings"
    )
    op.drop_index(
        op.f("ix_subject_offerings_school_id"), table_name="subject_offerings"
    )
    op.drop_table("subject_offerings")

    op.drop_index(op.f("ix_subjects_school_id"), table_name="subjects")
    op.drop_table("subjects")

    op.drop_index(op.f("ix_class_groups_year_level_id"), table_name="class_groups")
    op.drop_index(op.f("ix_class_groups_academic_year_id"), table_name="class_groups")
    op.drop_index(op.f("ix_class_groups_school_id"), table_name="class_groups")
    op.drop_table("class_groups")

    op.drop_index(op.f("ix_year_levels_school_id"), table_name="year_levels")
    op.drop_table("year_levels")

    op.drop_index(op.f("ix_terms_academic_year_id"), table_name="terms")
    op.drop_index(op.f("ix_terms_school_id"), table_name="terms")
    op.drop_table("terms")

    op.drop_index(op.f("ix_academic_years_school_id"), table_name="academic_years")
    op.drop_table("academic_years")

    op.drop_column("schools", "terminology_config")
