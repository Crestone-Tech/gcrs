"""Database service layer for GCRS persistence operations.

This module provides high-level functions for persisting scan results to the database,
following the scan execution flow defined in DATABASE_DESIGN.md.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from collections import Counter
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from gcrs.db.models import (
    BOM,
    BOMCommit,
    BOMFile,
    File,
    FileVersion,
    Repo,
    RepoCommit,
)
from gcrs.logger import setup_logging
from gcrs.models import FileRecord, RepositorySummary, ScanParams

logger = setup_logging()


def get_or_create_repo(
    session: Session,
    uri: str,
    git_owner_account: str | None = None,
    repo_name: str | None = None,
) -> Repo:
    """Get or create a repository record.
    
    Args:
        session: Database session
        uri: Repository URI (e.g., "https://github.com/user/repo.git")
        git_owner_account: Git owner/account name (e.g., "github.com/user"). 
                          If None, will be derived from URI or set to "unknown"
        name: Repository name. If None, will be derived from URI or set to "unknown"
    
    Returns:
        Repo instance (existing or newly created)
    """
    # Try to find existing repo by URI
    stmt = select(Repo).where(Repo.uri == uri)
    repo = session.scalar(stmt)
    
    if repo:
        logger.debug("Found existing repo: %s (id=%s)", uri, repo.id)
        return repo
    
    # Derive owner and name from URI if not provided
    if not git_owner_account or not repo_name:
        if git_owner_account is None:
            git_owner_account = "unknown"
        if repo_name is None:
            # Try to extract name from URI
            if uri.endswith(".git"):
                repo_name = Path(uri).stem
            elif "/" in uri:
                repo_name = uri.rstrip("/").split("/")[-1]
            else:
                repo_name = "unknown"
    
    # Create new repo
    repo = Repo(
        uri=uri,
        git_owner_account=git_owner_account,
        name=repo_name,
    )
    session.add(repo)
    session.flush()  # Flush to get the ID
    logger.info("Created new repo: %s (id=%s)", uri, repo.id)
    return repo


def get_or_create_repo_commit(
    session: Session,
    repo_id: int,
    commit_hash: str,
    commit_timestamp: datetime | None = None,
) -> RepoCommit:
    """Get or create a repository commit record.
    
    Args:
        session: Database session
        repo_id: Repository ID
        commit_hash: SHA-1 commit hash (40 characters)
        commit_timestamp: Commit timestamp. If None, uses current time
    
    Returns:
        RepoCommit instance (existing or newly created)
    """
    # Try to find existing commit
    stmt = select(RepoCommit).where(
        RepoCommit.repo_id == repo_id,
        RepoCommit.hash == commit_hash,
    )
    commit = session.scalar(stmt)
    
    if commit:
        logger.debug("Found existing commit: %s (id=%s)", commit_hash[:8], commit.id)
        return commit
    
    # Create new commit
    if commit_timestamp is None:
        commit_timestamp = datetime.utcnow()
    
    commit = RepoCommit(
        repo_id=repo_id,
        hash=commit_hash,
        timestamp=commit_timestamp,
    )
    session.add(commit)
    session.flush()
    logger.debug("Created new commit: %s (id=%s)", commit_hash[:8], commit.id)
    return commit


def get_or_create_file(
    session: Session,
    repo_id: int,
    file_path: str,
    file_name: str | None = None,
) -> File:
    """Get or create a file record.
    
    Args:
        session: Database session
        repo_id: Repository ID
        file_path: Relative path from repository root
        file_name: Filename. If None, derived from file_path
    
    Returns:
        File instance (existing or newly created)
    """
    # Try to find existing file
    stmt = select(File).where(
        File.repo_id == repo_id,
        File.path == file_path,
    )
    file = session.scalar(stmt)
    
    if file:
        logger.debug("Found existing file: %s (id=%s)", file_path, file.id)
        return file
    
    # Derive name from path if not provided
    if file_name is None:
        file_name = Path(file_path).name
    
    # Create new file
    file = File(
        repo_id=repo_id,
        name=file_name,
        path=file_path,
    )
    session.add(file)
    session.flush()
    logger.debug("Created new file: %s (id=%s)", file_path, file.id)
    return file


def get_or_create_file_version(
    session: Session,
    file_id: int,
    commit_id: int | None,
    file_path: str,
    size_bytes: int,
    content_hash: str | None = None,
) -> FileVersion:
    """Get or create a file version record (idempotent).
    
    Args:
        session: Database session
        file_id: File ID
        commit_id: Commit ID. If None, creates a version without commit association
        file_path: File path at this commit (may differ if renamed)
        size_bytes: File size in bytes
        content_hash: Optional SHA-256 hash of file content
    
    Returns:
        FileVersion instance (existing or newly created)
    """
    # Try to find existing file version
    if commit_id is not None:
        stmt = select(FileVersion).where(
            FileVersion.file_id == file_id,
            FileVersion.commit_id == commit_id,
        )
    else:
        # If no commit_id, we can't use idempotency - create new version
        # In practice, we should always have a commit_id for proper versioning
        stmt = None
    
    if stmt:
        file_version = session.scalar(stmt)
        if file_version:
            logger.debug(
                "Found existing file version: file_id=%s, commit_id=%s (id=%s)",
                file_id,
                commit_id,
                file_version.id,
            )
            return file_version
    
    # Create new file version
    file_version = FileVersion(
        file_id=file_id,
        commit_id=commit_id,
        path=file_path,
        size_bytes=size_bytes,
        content_hash=content_hash,
    )
    session.add(file_version)
    session.flush()
    logger.debug(
        "Created new file version: file_id=%s, commit_id=%s (id=%s)",
        file_id,
        commit_id,
        file_version.id,
    )
    return file_version


def create_bom(
    session: Session,
    repo_id: int,
    repo_root: str,
    scan_config: dict[str, Any],
    start_timestamp: datetime | None = None,
) -> BOM:
    """Create a new BOM (scan execution) record with status='in_progress'.
    
    Args:
        session: Database session
        repo_id: Repository ID
        repo_root: Repository root path used for scan
        scan_config: Scan configuration dictionary (will be stored as JSONB)
        start_timestamp: Scan start timestamp. If None, uses current time
    
    Returns:
        BOM instance
    """
    if start_timestamp is None:
        start_timestamp = datetime.utcnow()
    
    bom = BOM(
        repo_id=repo_id,
        repo_root=repo_root,
        start_timestamp=start_timestamp,
        status="in_progress",
        scan_config=scan_config,
    )
    session.add(bom)
    session.flush()
    logger.info("Created new BOM: repo_id=%s, bom_id=%s", repo_id, bom.id)
    return bom


def add_bom_file(
    session: Session,
    bom_id: int,
    file_version_id: int,
    absolute_filename: str,
    extension: str | None = None,
    is_binary: bool = False,
    category: str | None = None,
    language: str | None = None,
    data_type: str | None = None,
    dependency_kind: str | None = None,
    technologies: list[str] | None = None,
) -> BOMFile:
    """Add a file record to a BOM.
    
    Args:
        session: Database session
        bom_id: BOM ID
        file_version_id: File version ID
        absolute_filename: Absolute filename path at scan time
        extension: File extension (e.g., '.py')
        is_binary: Whether file is binary
        category: File category (e.g., 'code', 'config', 'docs')
        language: Programming language (e.g., 'python', 'javascript')
        data_type: Data file type (e.g., 'csv', 'jsonl')
        dependency_kind: Dependency management system (e.g., 'python-requirements')
        technologies: List of technologies detected (e.g., ['docker', 'kubernetes'])
    
    Returns:
        BOMFile instance
    """
    bom_file = BOMFile(
        bom_id=bom_id,
        file_version_id=file_version_id,
        absolute_filename=absolute_filename,
        extension=extension,
        is_binary=is_binary,
        category=category,
        language=language,
        data_type=data_type,
        dependency_kind=dependency_kind,
        technologies=technologies,
    )
    session.add(bom_file)
    session.flush()
    logger.debug(
        "Added BOM file: bom_id=%s, file_version_id=%s (id=%s)",
        bom_id,
        file_version_id,
        bom_file.id,
    )
    return bom_file


def link_bom_commits(
    session: Session,
    bom_id: int,
    commit_ids: list[int],
) -> list[BOMCommit]:
    """Link commits to a BOM.
    
    Args:
        session: Database session
        bom_id: BOM ID
        commit_ids: List of commit IDs to link
    
    Returns:
        List of BOMCommit instances created
    """
    bom_commits = []
    for commit_id in commit_ids:
        # Check if link already exists
        stmt = select(BOMCommit).where(
            BOMCommit.bom_id == bom_id,
            BOMCommit.commit_id == commit_id,
        )
        existing = session.scalar(stmt)
        
        if existing:
            logger.debug(
                "BOM-commit link already exists: bom_id=%s, commit_id=%s",
                bom_id,
                commit_id,
            )
            bom_commits.append(existing)
            continue
        
        # Create new link
        bom_commit = BOMCommit(
            bom_id=bom_id,
            commit_id=commit_id,
        )
        session.add(bom_commit)
        bom_commits.append(bom_commit)
    
    session.flush()
    logger.debug("Linked %d commits to BOM: bom_id=%s", len(bom_commits), bom_id)
    return bom_commits


def complete_bom(
    session: Session,
    bom_id: int,
    status: str = "success",
    error: str | None = None,
    end_timestamp: datetime | None = None,
) -> BOM:
    """Complete a BOM by updating end_timestamp, execution_time, and status.
    
    Args:
        session: Database session
        bom_id: BOM ID
        status: Final status ('success' or 'fail')
        error: Error message if status is 'fail'
        end_timestamp: Scan end timestamp. If None, uses current time
    
    Returns:
        Updated BOM instance
    """
    bom = session.get(BOM, bom_id)
    if not bom:
        raise ValueError(f"BOM with id={bom_id} not found")
    
    if end_timestamp is None:
        end_timestamp = datetime.utcnow()
    
    bom.end_timestamp = end_timestamp
    bom.status = status
    bom.error = error
    
    # Calculate execution time
    if bom.start_timestamp and end_timestamp:
        delta = end_timestamp - bom.start_timestamp
        bom.execution_time_seconds = delta.total_seconds()
    
    session.flush()
    logger.info(
        "Completed BOM: bom_id=%s, status=%s, execution_time=%.3fs",
        bom_id,
        status,
        bom.execution_time_seconds or 0.0,
    )
    return bom


def get_latest_bom(session: Session, repo_id: int) -> BOM | None:
    """Get the latest BOM (scan) for a repository.
    
    Args:
        session: Database session
        repo_id: Repository ID
    
    Returns:
        BOM instance or None if no scans exist
    """
    stmt = (
        select(BOM)
        .where(BOM.repo_id == repo_id)
        .order_by(BOM.start_timestamp.desc())
        .limit(1)
    )
    bom = session.scalar(stmt)
    return bom


def persist_scan_results(
    session: Session,
    repo_root: Path,
    file_records: list[FileRecord],
    scan_params: ScanParams,
    repo_uri: str | None = None,
    git_owner_account: str | None = None,
) -> BOM:
    """Persist scan results to the database following the scan execution flow.
    
    This is a high-level function that orchestrates the entire persistence process:
    1. Create/Get Repo
    2. Create BOM with status='in_progress'
    3. For each file: create/get File, RepoCommit, FileVersion, and BOMFile
    4. Link commits to BOM
    5. Complete BOM with status='success'
    
    Args:
        session: Database session
        repo_root: Repository root path
        file_records: List of FileRecord instances from scan
        scan_params: ScanParams used for the scan
        repo_uri: Repository URI. If None, will be derived or set to "unknown"
        git_owner_account: Git owner/account. If None, will be derived or set to "unknown"
    
    Returns:
        Completed BOM instance
    """
    # Derive repo URI if not provided
    if repo_uri is None:
        repo_uri = str(repo_root.resolve())
    
    # Derive repo name from path if not provided
    repo_name = repo_root.name if repo_root.name else "unknown"
    
    # 1. Create/Get Repo
    repo = get_or_create_repo(
        session=session,
        uri=repo_uri,
        git_owner_account=git_owner_account,
        repo_name=repo_name,
    )
    
    # 2. Create BOM with status='in_progress'
    scan_config = {
        "output_file_format": scan_params.output_file_format,
        "skip_dirs": scan_params.skip_dirs,
        "respect_gitignore": scan_params.respect_gitignore,
    }
    bom = create_bom(
        session=session,
        repo_id=repo.id,
        repo_root=str(repo_root.resolve()),
        scan_config=scan_config,
    )
    
    # Track unique commits for linking
    unique_commits: dict[str, RepoCommit] = {}
    
    # 3. Process each file record
    for file_record in file_records:
        # Build relative path
        relative_path = str(Path(file_record.relative_dir) / file_record.name)
        
        # Get or create File
        file = get_or_create_file(
            session=session,
            repo_id=repo.id,
            file_path=relative_path,
            file_name=file_record.name,
        )
        
        # Get or create RepoCommit if commit info is available
        commit_id = None
        if file_record.most_recent_commit_hash:
            commit = get_or_create_repo_commit(
                session=session,
                repo_id=repo.id,
                commit_hash=file_record.most_recent_commit_hash,
                commit_timestamp=file_record.most_recent_commit_date,
            )
            commit_id = commit.id
            unique_commits[file_record.most_recent_commit_hash] = commit
        
        # Get or create FileVersion
        file_version = get_or_create_file_version(
            session=session,
            file_id=file.id,
            commit_id=commit_id,
            file_path=relative_path,
            size_bytes=file_record.size_bytes,
            content_hash=None,  # Could compute SHA-256 if needed
        )
        
        # Create BOMFile
        add_bom_file(
            session=session,
            bom_id=bom.id,
            file_version_id=file_version.id,
            absolute_filename=file_record.absolute_filename,
            extension=file_record.extension,
            is_binary=file_record.is_binary,
            category=file_record.category,
            language=file_record.language,
            data_type=file_record.data_type,
            dependency_kind=file_record.dependency_kind,
            technologies=file_record.technologies if file_record.technologies else None,
        )
    
    # 4. Link commits to BOM
    if unique_commits:
        commit_ids = [commit.id for commit in unique_commits.values()]
        link_bom_commits(session=session, bom_id=bom.id, commit_ids=commit_ids)
    
    # 5. Complete BOM
    bom = complete_bom(session=session, bom_id=bom.id, status="success")
    
    logger.info(
        "Persisted scan results: bom_id=%s, repo_id=%s, files=%d",
        bom.id,
        repo.id,
        len(file_records),
    )
    return bom


def get_repo_summary_from_db(
    session: Session,
    repo_id: int,
    bom_id: int | None = None,
) -> RepositorySummary | None:
    """Get repository summary from database for a specific BOM.
    
    Aggregates data from BOMFile records to create a RepositorySummary.
    If bom_id is None, uses the latest BOM for the repository.
    
    Args:
        session: Database session
        repo_id: Repository ID
        bom_id: Optional BOM ID. If None, uses latest BOM for the repo
    
    Returns:
        RepositorySummary instance or None if no BOM found
    """
    # Get BOM (latest if not specified)
    if bom_id is None:
        bom = get_latest_bom(session=session, repo_id=repo_id)
        if not bom:
            logger.debug("No BOM found for repo_id=%s", repo_id)
            return None
        bom_id = bom.id
    else:
        bom = session.get(BOM, bom_id)
        if not bom or bom.repo_id != repo_id:
            logger.warning("BOM %s not found or doesn't belong to repo %s", bom_id, repo_id)
            return None
    
    # Query all BOMFile records for this BOM
    stmt = select(BOMFile).where(BOMFile.bom_id == bom_id)
    bom_files = session.scalars(stmt).all()
    
    if not bom_files:
        logger.debug("No files found in BOM %s", bom_id)
        # Return empty summary
        return RepositorySummary(
            total_files=0,
            scanned_files=0,
            skipped_files=0,
        )
    
    # Initialize counters for aggregation
    files_by_language_counter = Counter()
    files_by_category_counter = Counter()
    files_by_extension_counter = Counter()
    binary_files_by_extension_counter = Counter()
    files_by_dependency_counter = Counter()
    data_files_by_extension_counter = Counter()
    files_by_technology_counter = Counter()
    files_without_extension = 0
    files_with_extension = 0
    
    # Aggregate data from BOMFile records
    for bom_file in bom_files:
        # Language
        if bom_file.language:
            files_by_language_counter[bom_file.language] += 1
        
        # Category
        if bom_file.category:
            files_by_category_counter[bom_file.category] += 1
        
        # Extension
        if bom_file.extension:
            files_by_extension_counter[bom_file.extension] += 1
            files_with_extension += 1
            
            # Binary files by extension
            if bom_file.is_binary:
                binary_files_by_extension_counter[bom_file.extension] += 1
        else:
            files_without_extension += 1
        
        # Data type
        if bom_file.data_type:
            data_files_by_extension_counter[bom_file.data_type] += 1
        
        # Dependency kind
        if bom_file.dependency_kind:
            files_by_dependency_counter[bom_file.dependency_kind] += 1
        
        # Technologies (array field)
        if bom_file.technologies:
            for tech in bom_file.technologies:
                files_by_technology_counter[tech] += 1
    
    # Build RepositorySummary
    summary = RepositorySummary(
        files_by_language=dict(files_by_language_counter),
        files_by_category=dict(files_by_category_counter),
        files_by_technology=dict(files_by_technology_counter),
        files_by_dependency=dict(files_by_dependency_counter),
        files_by_extension=dict(files_by_extension_counter),
        binary_files_by_extension=dict(binary_files_by_extension_counter),
        data_files_by_extension=dict(data_files_by_extension_counter),
        files_without_extension=files_without_extension,
        files_with_extension=files_with_extension,
        total_files=len(bom_files),  # Total files in this BOM
        scanned_files=len(bom_files),  # All files in BOM were scanned
        skipped_files=0,  # We don't track skipped files in the database
    )
    
    logger.debug(
        "Generated summary from DB: repo_id=%s, bom_id=%s, files=%d",
        repo_id,
        bom_id,
        len(bom_files),
    )
    return summary

