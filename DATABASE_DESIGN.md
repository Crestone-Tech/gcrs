# PostgreSQL Database Design for GCRS

## Overview

This document describes the PostgreSQL database schema for the Green Cloud Repository Scanner (GCRS) persistence layer. The design supports tracking repository scans, file metadata, commit history, and aggregated summaries.

## Design Principles

1. **Incremental History**: File versions are created only when files are scanned, building history organically
2. **Idempotency**: Scanning the same file at the same commit reuses existing records
3. **Audit Trail**: Scan configurations and parameters are stored for reproducibility
4. **Flexibility**: JSONB columns used for flexible, extensible data storage
5. **Performance**: Strategic indexes on frequently queried fields

## Entity Relationship Diagram

```
repo (1) ────< (many) repo_commit
  │
  │ (1)
  │
  └───< (many) file
         │
         │ (1)
         │
         └───< (many) file_version
                │
                │ (1)
                │
                └───< (many) bom_file

repo (1) ────< (many) bom
  │
  │ (1:many)
  │
  └───< (many) repo_commit (via bom_commits junction)

bom (1) ────< (many) bom_file
  │
  └───> (1) file_version
         └───> (1) file
                └───> (1) repo
```

## Tables

### 1. `repo`

Stores repository information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing repository ID |
| `git_owner_account` | `VARCHAR(255)` | NOT NULL | Git owner/account name (e.g., "github.com/user") |
| `name` | `VARCHAR(255)` | NOT NULL | Repository name |
| `uri` | `VARCHAR(512)` | NOT NULL, UNIQUE | Repository URI (e.g., "https://github.com/user/repo.git") |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was created |
| `updated_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was last updated |

**Indexes:**
- `idx_repo_uri` on `uri` (UNIQUE)
- `idx_repo_owner_name` on `(git_owner_account, name)`

**Notes:**
- `uri` is unique to prevent duplicate repository entries
- Composite index on owner and name for efficient lookups

---

### 2. `repo_commit`

Stores Git commit information for repositories.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing commit ID |
| `repo_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `repo.id` | Reference to repository |
| `hash` | `VARCHAR(40)` | NOT NULL | SHA-1 commit hash (40 characters) |
| `timestamp` | `TIMESTAMP` | NOT NULL | Commit timestamp |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was created |

**Indexes:**
- `idx_repo_commit_repo_id` on `repo_id`
- `idx_repo_commit_hash` on `hash`
- `idx_repo_commit_repo_hash` on `(repo_id, hash)` (UNIQUE)

**Notes:**
- Unique constraint on `(repo_id, hash)` ensures one record per commit per repo
- Index on `hash` for efficient lookups across repositories

---

### 3. `file`

Stores file information within repositories.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing file ID |
| `repo_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `repo.id` | Reference to repository |
| `name` | `VARCHAR(255)` | NOT NULL | Filename (e.g., "scanner.py") |
| `path` | `TEXT` | NOT NULL | Relative path from repository root (e.g., "src/utils/scanner.py") |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was created |
| `updated_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was last updated |

**Indexes:**
- `idx_file_repo_id` on `repo_id`
- `idx_file_repo_path` on `(repo_id, path)` (UNIQUE)

**Notes:**
- Unique constraint on `(repo_id, path)` ensures one record per file path per repo
- Path is stored as relative to repo root for portability

---

### 4. `file_version`

Stores file versions at specific commits. Created only when a file is scanned.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing file version ID |
| `file_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `file.id` | Reference to file |
| `commit_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `repo_commit.id` | Reference to commit |
| `path` | `TEXT` | NOT NULL | File path at this commit (may differ from file.path if renamed) |
| `size_bytes` | `BIGINT` | NOT NULL | File size in bytes at this commit |
| `content_hash` | `VARCHAR(64)` | NULL | SHA-256 hash of file content (optional, for change detection) |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was created |

**Indexes:**
- `idx_file_version_file_id` on `file_id`
- `idx_file_version_commit_id` on `commit_id`
- `idx_file_version_file_commit` on `(file_id, commit_id)` (UNIQUE)

**Notes:**
- Unique constraint on `(file_id, commit_id)` ensures idempotency
- `path` stored here to track renames/moves across commits
- `content_hash` optional but useful for detecting content changes

---

### 5. `bom`

Stores Bill of Materials (scan execution) information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing BOM ID |
| `repo_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `repo.id` | Reference to repository |
| `repo_root` | `TEXT` | NOT NULL | Repository root path used for scan |
| `start_timestamp` | `TIMESTAMP` | NOT NULL | Scan start time |
| `end_timestamp` | `TIMESTAMP` | NULL | Scan end time (NULL if scan in progress) |
| `execution_time_seconds` | `NUMERIC(10, 3)` | NULL | Execution time in seconds (calculated) |
| `status` | `VARCHAR(20)` | NOT NULL, CHECK (`status` IN ('success', 'fail', 'in_progress')) | Scan status |
| `error` | `TEXT` | NULL | Error message if status is 'fail' |
| `scan_config` | `JSONB` | NOT NULL | Scan configuration/parameters (see below) |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was created |

**Indexes:**
- `idx_bom_repo_id` on `repo_id`
- `idx_bom_status` on `status`
- `idx_bom_start_timestamp` on `start_timestamp`
- `idx_bom_repo_start` on `(repo_id, start_timestamp DESC)`

**Notes:**
- `scan_config` JSONB structure:
  ```json
  {
    "output_file_format": "json",
    "skip_dirs": [".git", "node_modules"],
    "respect_gitignore": true
  }
  ```
- `execution_time_seconds` can be calculated from `start_timestamp` and `end_timestamp`
- Index on `(repo_id, start_timestamp DESC)` for efficient "latest scan" queries

---

### 6. `bom_commits`

Junction table linking BOMs to commits (many-to-many relationship).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `bom_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `bom.id` | Reference to BOM |
| `commit_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `repo_commit.id` | Reference to commit |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was created |

**Indexes:**
- `idx_bom_commits_bom_id` on `bom_id`
- `idx_bom_commits_commit_id` on `commit_id`
- `idx_bom_commits_unique` on `(bom_id, commit_id)` (UNIQUE)

**Notes:**
- Tracks which commits were present/included in a scan
- Unique constraint prevents duplicate associations

---

### 7. `bom_file`

Stores scan findings for files within a BOM (analogous to FileRecord in scan output).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing BOM file ID |
| `bom_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `bom.id` | Reference to BOM |
| `file_version_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `file_version.id` | Reference to file version |
| `absolute_filename` | `TEXT` | NOT NULL | Absolute filename path at scan time |
| `extension` | `VARCHAR(50)` | NULL | File extension in lowercase (e.g., '.py') |
| `is_binary` | `BOOLEAN` | NOT NULL | Whether file is binary |
| `category` | `VARCHAR(50)` | NULL | File category (e.g., 'code', 'config', 'docs') |
| `language` | `VARCHAR(50)` | NULL | Programming language (e.g., 'python', 'javascript') |
| `data_type` | `VARCHAR(50)` | NULL | Data file type (e.g., 'csv', 'jsonl', 'xml') |
| `dependency_kind` | `VARCHAR(50)` | NULL | Dependency management system (e.g., 'python-requirements') |
| `technologies` | `TEXT[]` | NULL | Array of technologies detected (e.g., ['docker', 'kubernetes']) |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was created |

**Indexes:**
- `idx_bom_file_bom_id` on `bom_id`
- `idx_bom_file_file_version_id` on `file_version_id`
- `idx_bom_file_category` on `category`
- `idx_bom_file_language` on `language`
- `idx_bom_file_bom_category` on `(bom_id, category)`
- `idx_bom_file_bom_language` on `(bom_id, language)`

**Notes:**
- References `file_version` to link to specific commit state
- `absolute_filename` stored for historical reference (may differ from current path)
- Array type for `technologies` allows multiple values per file
- Composite indexes support common aggregation queries

---

### 8. `repo_summary` (View)

Materialized view or regular view aggregating repository summary statistics from BOM data.

**View Definition:**
```sql
CREATE OR REPLACE VIEW repo_summary AS
SELECT 
    r.id AS repo_id,
    r.git_owner_account,
    r.name AS repo_name,
    r.uri AS repo_uri,
    b.id AS latest_bom_id,
    b.start_timestamp AS latest_scan_timestamp,
    b.status AS latest_scan_status,
    COUNT(DISTINCT b.id) AS total_scans,
    COUNT(DISTINCT bf.id) AS total_files_scanned,
    COUNT(DISTINCT CASE WHEN bf.category IS NOT NULL THEN bf.id END) AS files_with_category,
    COUNT(DISTINCT CASE WHEN bf.language IS NOT NULL THEN bf.id END) AS files_with_language,
    -- Aggregated counts by category
    COUNT(DISTINCT CASE WHEN bf.category = 'code' THEN bf.id END) AS code_files,
    COUNT(DISTINCT CASE WHEN bf.category = 'config' THEN bf.id END) AS config_files,
    COUNT(DISTINCT CASE WHEN bf.category = 'docs' THEN bf.id END) AS docs_files,
    -- Aggregated counts by language
    COUNT(DISTINCT CASE WHEN bf.language = 'python' THEN bf.id END) AS python_files,
    COUNT(DISTINCT CASE WHEN bf.language = 'javascript' THEN bf.id END) AS javascript_files,
    -- Add more aggregations as needed
    MAX(b.end_timestamp) AS last_scan_completed_at
FROM repo r
LEFT JOIN bom b ON r.id = b.repo_id
LEFT JOIN bom_file bf ON b.id = bf.bom_id
GROUP BY r.id, r.git_owner_account, r.name, r.uri, b.id, b.start_timestamp, b.status
HAVING b.id = (
    SELECT id FROM bom 
    WHERE repo_id = r.id 
    ORDER BY start_timestamp DESC 
    LIMIT 1
);
```

**Alternative: Materialized View**
For better performance on large datasets, consider a materialized view that refreshes on BOM creation:

```sql
CREATE MATERIALIZED VIEW repo_summary_mv AS
-- Same query as above
;

CREATE UNIQUE INDEX ON repo_summary_mv (repo_id);
```

**Refresh Strategy:**
- Refresh on BOM completion
- Or refresh periodically via scheduled job

---

## Relationships Summary

| Relationship | Type | Description |
|--------------|------|-------------|
| `repo` → `repo_commit` | 1:many | One repo has many commits |
| `repo` → `file` | 1:many | One repo has many files |
| `repo` → `bom` | 1:many | One repo has many BOMs (scans) |
| `file` → `file_version` | 1:many | One file has many versions (at different commits) |
| `file_version` → `bom_file` | 1:many | One file version can appear in multiple BOMs |
| `bom` → `bom_file` | 1:many | One BOM contains many file records |
| `bom` → `repo_commit` | many:many | One BOM can reference many commits (via `bom_commits`) |

---

## Data Flow

### Scan Execution Flow

1. **Create/Get Repo**: Lookup or create `repo` record
2. **Create BOM**: Insert `bom` record with `status='in_progress'`
3. **For each file scanned**:
   - Create/Get `file` record
   - Get/Create `repo_commit` record (if commit info available)
   - Get/Create `file_version` record (idempotent: `file_id` + `commit_id`)
   - Create `bom_file` record linking to `file_version`
4. **Link Commits**: Insert into `bom_commits` for commits included in scan
5. **Update BOM**: Set `end_timestamp`, `execution_time_seconds`, `status='success'`

### Idempotency

- **File Versions**: Unique constraint on `(file_id, commit_id)` ensures re-scanning the same file at the same commit reuses the existing `file_version` record
- **BOM Files**: Each scan creates new `bom_file` records, but they may reference the same `file_version`

---

## Indexes Summary

### Primary Indexes (Primary Keys)
- All tables have `id` as PRIMARY KEY (auto-indexed)

### Foreign Key Indexes
- `idx_repo_commit_repo_id` on `repo_commit(repo_id)`
- `idx_file_repo_id` on `file(repo_id)`
- `idx_file_version_file_id` on `file_version(file_id)`
- `idx_file_version_commit_id` on `file_version(commit_id)`
- `idx_bom_repo_id` on `bom(repo_id)`
- `idx_bom_file_bom_id` on `bom_file(bom_id)`
- `idx_bom_file_file_version_id` on `bom_file(file_version_id)`

### Unique Constraint Indexes
- `idx_repo_uri` on `repo(uri)`
- `idx_repo_commit_repo_hash` on `repo_commit(repo_id, hash)`
- `idx_file_repo_path` on `file(repo_id, path)`
- `idx_file_version_file_commit` on `file_version(file_id, commit_id)`
- `idx_bom_commits_unique` on `bom_commits(bom_id, commit_id)`

### Query Optimization Indexes
- `idx_repo_owner_name` on `repo(git_owner_account, name)`
- `idx_repo_commit_hash` on `repo_commit(hash)`
- `idx_bom_status` on `bom(status)`
- `idx_bom_start_timestamp` on `bom(start_timestamp)`
- `idx_bom_repo_start` on `bom(repo_id, start_timestamp DESC)`
- `idx_bom_file_category` on `bom_file(category)`
- `idx_bom_file_language` on `bom_file(language)`
- `idx_bom_file_bom_category` on `bom_file(bom_id, category)`
- `idx_bom_file_bom_language` on `bom_file(bom_id, language)`

---

## Design Decisions

### 1. File Versioning Strategy
**Decision**: Create `file_version` records only when files are scanned  
**Rationale**: Incremental history building, simpler implementation, avoids upfront git history extraction

### 2. BOM-to-Repo Relationship
**Decision**: 1:many (one repo can have many BOMs)  
**Rationale**: Supports tracking scans over time, enables historical analysis

### 3. Scan Configuration Storage
**Decision**: Store in JSONB column `scan_config`  
**Rationale**: Flexible, extensible, easy to add new parameters without schema changes

### 4. Repository Summary
**Decision**: Implement as database view (or materialized view)  
**Rationale**: Computed from BOM data, matches `/scan/summary` endpoint output, avoids data duplication

### 5. File-to-Commit Relationship
**Decision**: Track via `file_version` table  
**Rationale**: Separates git history from scan results, supports tracking file changes over time

### 6. Technologies Storage
**Decision**: Use PostgreSQL array type `TEXT[]`  
**Rationale**: Native array support, efficient storage, easy to query

### 7. Content Hash
**Decision**: Optional `content_hash` in `file_version`  
**Rationale**: Useful for change detection but not always necessary, keeps table flexible

---

## Migration Considerations

### Initial Schema Creation
1. Create tables in dependency order:
   - `repo`
   - `repo_commit` (depends on `repo`)
   - `file` (depends on `repo`)
   - `file_version` (depends on `file`, `repo_commit`)
   - `bom` (depends on `repo`)
   - `bom_commits` (depends on `bom`, `repo_commit`)
   - `bom_file` (depends on `bom`, `file_version`)
2. Create indexes after tables
3. Create views last

### Future Extensibility
- JSONB columns (`scan_config`) allow adding fields without migrations
- Array columns can be extended with additional values
- Views can be modified without affecting underlying data

---

## Query Patterns

### Common Queries

1. **Get latest scan for a repository**:
   ```sql
   SELECT * FROM bom 
   WHERE repo_id = ? 
   ORDER BY start_timestamp DESC 
   LIMIT 1;
   ```

2. **Get all files in a BOM**:
   ```sql
   SELECT bf.*, f.name, f.path, fv.size_bytes
   FROM bom_file bf
   JOIN file_version fv ON bf.file_version_id = fv.id
   JOIN file f ON fv.file_id = f.id
   WHERE bf.bom_id = ?;
   ```

3. **Get repository summary**:
   ```sql
   SELECT * FROM repo_summary WHERE repo_id = ?;
   ```

4. **Find files by language across all scans**:
   ```sql
   SELECT f.name, f.path, b.start_timestamp
   FROM bom_file bf
   JOIN file_version fv ON bf.file_version_id = fv.id
   JOIN file f ON fv.file_id = f.id
   JOIN bom b ON bf.bom_id = b.id
   WHERE bf.language = 'python' AND b.repo_id = ?;
   ```

---

## Notes

- All timestamps use `TIMESTAMP` type (timezone-aware recommended: `TIMESTAMPTZ`)
- Consider adding `updated_at` triggers for automatic timestamp updates
- Consider soft deletes if historical data retention is important
- Monitor index usage and adjust based on actual query patterns
- Consider partitioning `bom_file` table by `bom_id` or date if it grows very large



