"""SQLAlchemy ORM models for GCRS database schema."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    func,
    Index,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Repo(Base):
    """Repository table."""

    __tablename__ = "repo"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    git_owner_account = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    uri = Column(String(512), nullable=False, unique=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default="now()")
    updated_at = Column(TIMESTAMP, nullable=False, server_default="now()", onupdate=func.now())

    # Relationships
    commits = relationship("RepoCommit", back_populates="repo", cascade="all, delete-orphan")
    files = relationship("File", back_populates="repo", cascade="all, delete-orphan")
    boms = relationship("BOM", back_populates="repo", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_repo_uri", "uri", unique=True),
        Index("idx_repo_owner_name", "git_owner_account", "name"),
    )

    def __repr__(self) -> str:
        return f"<Repo(id={self.id}, name='{self.name}', uri='{self.uri}')>"


class RepoCommit(Base):
    """Repository commit table."""

    __tablename__ = "repo_commit"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    repo_id = Column(BigInteger, ForeignKey("repo.id", ondelete="CASCADE"), nullable=False)
    hash = Column(String(40), nullable=False)  # SHA-1 hash (40 characters)
    timestamp = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default="now()")

    # Relationships
    repo = relationship("Repo", back_populates="commits")
    file_versions = relationship("FileVersion", back_populates="commit")
    bom_commits = relationship("BOMCommit", back_populates="commit")

    __table_args__ = (
        Index("idx_repo_commit_repo_id", "repo_id"),
        Index("idx_repo_commit_hash", "hash"),
        UniqueConstraint("repo_id", "hash", name="idx_repo_commit_repo_hash"),
    )

    def __repr__(self) -> str:
        return f"<RepoCommit(id={self.id}, repo_id={self.repo_id}, hash='{self.hash[:8]}...')>"


class File(Base):
    """File table."""

    __tablename__ = "file"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    repo_id = Column(BigInteger, ForeignKey("repo.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    path = Column(Text, nullable=False)  # Relative path from repository root
    created_at = Column(TIMESTAMP, nullable=False, server_default="now()")
    updated_at = Column(TIMESTAMP, nullable=False, server_default="now()", onupdate=func.now())

    # Relationships
    repo = relationship("Repo", back_populates="files")
    versions = relationship("FileVersion", back_populates="file", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_file_repo_id", "repo_id"),
        UniqueConstraint("repo_id", "path", name="idx_file_repo_path"),
    )

    def __repr__(self) -> str:
        return f"<File(id={self.id}, repo_id={self.repo_id}, path='{self.path}')>"


class FileVersion(Base):
    """File version table - tracks file state at specific commits."""

    __tablename__ = "file_version"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    file_id = Column(BigInteger, ForeignKey("file.id", ondelete="CASCADE"), nullable=False)
    commit_id = Column(BigInteger, ForeignKey("repo_commit.id", ondelete="CASCADE"), nullable=False)
    path = Column(Text, nullable=False)  # Path at this commit (may differ if renamed)
    size_bytes = Column(BigInteger, nullable=False)
    content_hash = Column(String(64), nullable=True)  # SHA-256 hash (optional)
    created_at = Column(TIMESTAMP, nullable=False, server_default="now()")

    # Relationships
    file = relationship("File", back_populates="versions")
    commit = relationship("RepoCommit", back_populates="file_versions")
    bom_files = relationship("BOMFile", back_populates="file_version")

    __table_args__ = (
        Index("idx_file_version_file_id", "file_id"),
        Index("idx_file_version_commit_id", "commit_id"),
        UniqueConstraint("file_id", "commit_id", name="idx_file_version_file_commit"),
    )

    def __repr__(self) -> str:
        return f"<FileVersion(id={self.id}, file_id={self.file_id}, commit_id={self.commit_id})>"


class BOM(Base):
    """Bill of Materials (scan execution) table."""

    __tablename__ = "bom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    repo_id = Column(BigInteger, ForeignKey("repo.id", ondelete="CASCADE"), nullable=False)
    repo_root = Column(Text, nullable=False)  # Repository root path used for scan
    start_timestamp = Column(TIMESTAMP, nullable=False)
    end_timestamp = Column(TIMESTAMP, nullable=True)
    execution_time_seconds = Column(Numeric(10, 3), nullable=True)
    status = Column(String(20), nullable=False)
    error = Column(Text, nullable=True)
    scan_config = Column(JSONB, nullable=False)  # Scan configuration/parameters
    created_at = Column(TIMESTAMP, nullable=False, server_default="now()")

    # Relationships
    repo = relationship("Repo", back_populates="boms")
    bom_commits = relationship("BOMCommit", back_populates="bom", cascade="all, delete-orphan")
    bom_files = relationship("BOMFile", back_populates="bom", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('success', 'fail', 'in_progress')", name="check_bom_status"),
        Index("idx_bom_repo_id", "repo_id"),
        Index("idx_bom_status", "status"),
        Index("idx_bom_start_timestamp", "start_timestamp"),
        Index("idx_bom_repo_start", "repo_id", "start_timestamp"),
    )

    def __repr__(self) -> str:
        return f"<BOM(id={self.id}, repo_id={self.repo_id}, status='{self.status}')>"


class BOMCommit(Base):
    """Junction table linking BOMs to commits."""

    __tablename__ = "bom_commits"

    bom_id = Column(BigInteger, ForeignKey("bom.id", ondelete="CASCADE"), primary_key=True)
    commit_id = Column(BigInteger, ForeignKey("repo_commit.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default="now()")

    # Relationships
    bom = relationship("BOM", back_populates="bom_commits")
    commit = relationship("RepoCommit", back_populates="bom_commits")

    __table_args__ = (
        Index("idx_bom_commits_bom_id", "bom_id"),
        Index("idx_bom_commits_commit_id", "commit_id"),
        UniqueConstraint("bom_id", "commit_id", name="idx_bom_commits_unique"),
    )

    def __repr__(self) -> str:
        return f"<BOMCommit(bom_id={self.bom_id}, commit_id={self.commit_id})>"


class BOMFile(Base):
    """BOM file table - stores scan findings for files."""

    __tablename__ = "bom_file"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bom_id = Column(BigInteger, ForeignKey("bom.id", ondelete="CASCADE"), nullable=False)
    file_version_id = Column(BigInteger, ForeignKey("file_version.id", ondelete="CASCADE"), nullable=False)
    absolute_filename = Column(Text, nullable=False)  # Absolute path at scan time
    extension = Column(String(50), nullable=True)
    is_binary = Column(Boolean, nullable=False)
    category = Column(String(50), nullable=True)
    language = Column(String(50), nullable=True)
    data_type = Column(String(50), nullable=True)
    dependency_kind = Column(String(50), nullable=True)
    technologies = Column(ARRAY(Text), nullable=True)  # Array of technologies
    created_at = Column(TIMESTAMP, nullable=False, server_default="now()")

    # Relationships
    bom = relationship("BOM", back_populates="bom_files")
    file_version = relationship("FileVersion", back_populates="bom_files")

    __table_args__ = (
        Index("idx_bom_file_bom_id", "bom_id"),
        Index("idx_bom_file_file_version_id", "file_version_id"),
        Index("idx_bom_file_category", "category"),
        Index("idx_bom_file_language", "language"),
        Index("idx_bom_file_bom_category", "bom_id", "category"),
        Index("idx_bom_file_bom_language", "bom_id", "language"),
    )

    def __repr__(self) -> str:
        return f"<BOMFile(id={self.id}, bom_id={self.bom_id}, file_version_id={self.file_version_id})>"



