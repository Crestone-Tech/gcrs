# Orchestrator Module Design

## Overview

The Orchestrator module is the central coordination system for the Green Cloud Repository Scanner (GCRS) ecosystem. It manages the complete workflow from repository scanning through code analysis, finding generation, cost estimation, and issue tracking.

## System Architecture

```
┌─────────────┐
│     UI      │ (Future)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Scheduler │  │  GCCO Runner │  │  GCGM Runner │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────┬──────────────────┬──────────────────┬───────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│    GCRS     │   │    GCCO     │   │    GCGM     │
│  (Scanner)  │   │  (Optimizer)│   │ (Goal Mgr)  │
└─────────────┘   └─────────────┘   └─────────────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ▼
                   ┌─────────────┐
                   │  PostgreSQL │
                   │   Database  │
                   └─────────────┘
```

## Core Components

### 1. Orchestrator

The main orchestration engine that coordinates all operations.

**Responsibilities:**
- Schedule and manage scan executions
- Coordinate GCRS scan runs with different scopes
- Orchestrate GCCO analysis runs
- Coordinate GCGM operations (cost estimation, Jira integration, performance measurement)
- Handle retries and error recovery
- Manage workflow state

**Key Methods:**
- `schedule_scan(repo_id, scan_scope, schedule_config)`
- `execute_scan_workflow(repo_id, scan_scope)`
- `execute_gcco_analysis(bom_id, filter_options)`
- `execute_gcgm_workflow(finding_ids)`
- `retry_failed_operation(operation_id)`

### 2. Scheduler

Manages scan scheduling and retry logic.

**Responsibilities:**
- Schedule scans (cron-like, event-driven, or manual)
- Manage retry queues
- Track operation status
- Handle timeouts

**Key Methods:**
- `schedule_scan(repo_id, schedule_config)`
- `retry_operation(operation_id, max_retries)`
- `cancel_scheduled_scan(schedule_id)`

### 3. GCCO Runner

Executes Green Cloud Code Optimizer analysis.

**Responsibilities:**
- Load and discover rules
- Execute pattern identification modules
- Coordinate AI confirmation layer
- Persist findings to database
- Handle rule execution errors

**Key Methods:**
- `load_rules(config_path)`
- `execute_rule(rule_id, file_path, language)`
- `run_ai_confirmation(finding_id)`
- `persist_findings(findings)`

### 4. GCGM Runner

Executes Green Cloud Goal Manager operations.

**Responsibilities:**
- Estimate cost savings for findings
- Integrate with Jira for issue creation
- Run performance tests (baseline and after fixes)
- Generate before/after comparisons
- Calculate aggregate metrics

**Key Methods:**
- `estimate_cost_savings(finding_id)`
- `create_jira_issues(finding_ids)`
- `run_performance_tests(repo_id, commit_hash)`
- `generate_comparison_report(finding_ids)`

## Data Flow

### Complete Workflow

```
1. User/System triggers scan
   │
   ▼
2. Orchestrator calls GCRS
   ├─ Whole repo (baseline)
   ├─ Incremental (since datetime)
   └─ Per commit
   │
   ▼
3. GCRS generates BOM in DB
   │
   ▼
4. Orchestrator fetches BOM results
   │
   ▼
5. For each file in BOM:
   │
   ├─ Filter by language/technology (optional)
   │
   ├─ Orchestrator calls GCCO
   │  │
   │  ├─ GCCO loads applicable rules
   │  │
   │  ├─ For each rule:
   │  │  │
   │  │  ├─ Load pattern module
   │  │  │
   │  │  ├─ Parse file to AST
   │  │  │
   │  │  ├─ Walk AST for patterns
   │  │  │
   │  │  └─ Generate findings (if matches)
   │  │
   │  └─ AI confirmation layer (Phase 2)
   │     │
   │     ├─ For each finding:
   │     │  │
   │     │  ├─ Call AI service
   │     │  │
   │     │  └─ Confirm or dismiss
   │     │
   │     └─ Update finding status
   │
   └─ Persist findings to DB
      │
      ▼
6. Orchestrator calls GCGM
   │
   ├─ Estimate cost savings
   │
   ├─ Create Jira issues
   │
   ├─ Run performance tests
   │  │
   │  ├─ Baseline (before fixes)
   │  │
   │  └─ After fixes
   │
   └─ Generate comparison reports
```

## Database Schema Extensions

### New Tables

#### 1. `rule`

Stores rule metadata for GCCO pattern identification.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing rule ID |
| `rule_id` | `VARCHAR(100)` | NOT NULL, UNIQUE | Human-readable rule identifier (e.g., "PY001") |
| `description` | `TEXT` | NOT NULL | Rule description |
| `category` | `VARCHAR(50)` | NOT NULL, CHECK (`category` IN ('code', 'technology')) | Rule category |
| `target_language` | `VARCHAR(50)` | NULL | Target programming language (e.g., 'python', 'javascript') |
| `target_technology` | `VARCHAR(50)` | NULL | Target technology (e.g., 'docker', 'kubernetes') |
| `module_path` | `TEXT` | NOT NULL | Path to pattern identification module |
| `enabled` | `BOOLEAN` | NOT NULL, DEFAULT TRUE | Whether rule is enabled |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was created |
| `updated_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was last updated |

**Indexes:**
- `idx_rule_rule_id` on `rule_id` (UNIQUE)
- `idx_rule_target_language` on `target_language`
- `idx_rule_target_technology` on `target_technology`
- `idx_rule_enabled` on `enabled`

**Notes:**
- Either `target_language` or `target_technology` must be set (enforced by application logic)
- `module_path` should be relative to project root or absolute path

---

#### 2. `finding`

Stores code inefficiency findings from GCCO analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing finding ID |
| `file_version_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `file_version.id` | Reference to file version |
| `rule_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `rule.id` | Reference to rule |
| `line_start` | `INTEGER` | NOT NULL | Starting line number of finding |
| `line_end` | `INTEGER` | NOT NULL | Ending line number of finding |
| `status` | `VARCHAR(20)` | NOT NULL, CHECK (`status` IN ('pending', 'confirmed', 'dismissed', 'fixed')) | Finding status |
| `ai_confirmed` | `BOOLEAN` | NULL | Whether AI confirmed the finding (NULL if not yet checked) |
| `ai_confidence` | `NUMERIC(5, 2)` | NULL | AI confidence score (0.00-1.00) |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when finding was created |
| `updated_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when finding was last updated |

**Indexes:**
- `idx_finding_file_version_id` on `file_version_id`
- `idx_finding_rule_id` on `rule_id`
- `idx_finding_status` on `status`
- `idx_finding_file_version_status` on `(file_version_id, status)`

**Notes:**
- `line_end` must be >= `line_start` (enforced by application logic)
- Status workflow: `pending` → `confirmed`/`dismissed` → `fixed` (optional)

---

#### 3. `cost_estimate`

Stores cost savings estimates from GCGM.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing cost estimate ID |
| `finding_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `finding.id` | Reference to finding |
| `processing_savings` | `NUMERIC(10, 2)` | NULL | Estimated processing/RAM savings (units TBD) |
| `performance_improvement` | `NUMERIC(10, 2)` | NULL | Estimated performance improvement (units TBD) |
| `power_cooling_savings` | `NUMERIC(10, 2)` | NULL | Estimated power/cooling cost savings (currency) |
| `developer_time_savings` | `NUMERIC(10, 2)` | NULL | Estimated developer time savings (hours) |
| `total_cost_savings` | `NUMERIC(10, 2)` | NULL | Total estimated cost savings (currency) |
| `story_points` | `INTEGER` | NULL | Estimated story points to fix (stretch goal) |
| `estimated_time_hours` | `NUMERIC(10, 2)` | NULL | Estimated time to fix in hours (stretch goal) |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when estimate was created |
| `updated_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when estimate was last updated |

**Indexes:**
- `idx_cost_estimate_finding_id` on `finding_id` (UNIQUE - one estimate per finding)
- `idx_cost_estimate_total_savings` on `total_cost_savings`

**Notes:**
- One cost estimate per finding (enforced by unique constraint)
- All savings fields are nullable (may not all be applicable)

---

#### 4. `jira_issue`

Stores Jira issue information linked to findings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing Jira issue record ID |
| `finding_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `finding.id` | Reference to finding |
| `jira_issue_key` | `VARCHAR(50)` | NOT NULL, UNIQUE | Jira issue key (e.g., "PROJ-123") |
| `jira_issue_url` | `TEXT` | NULL | Full URL to Jira issue |
| `status` | `VARCHAR(50)` | NULL | Jira issue status (synced from Jira) |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was created |
| `updated_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was last updated |

**Indexes:**
- `idx_jira_issue_finding_id` on `finding_id`
- `idx_jira_issue_key` on `jira_issue_key` (UNIQUE)

**Notes:**
- One Jira issue can be linked to multiple findings (via junction table if needed)
- `status` can be synced periodically from Jira API

---

#### 5. `performance_metric`

Stores performance test metrics from GCGM.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing metric ID |
| `repo_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `repo.id` | Reference to repository |
| `commit_id` | `BIGINT` | NULL, FOREIGN KEY → `repo_commit.id` | Reference to commit (NULL for baseline) |
| `test_suite_name` | `VARCHAR(255)` | NOT NULL | Name of test suite executed |
| `metric_name` | `VARCHAR(255)` | NOT NULL | Metric name (e.g., "execution_time_ms", "memory_usage_mb") |
| `metric_value` | `NUMERIC(15, 3)` | NOT NULL | Metric value |
| `metric_unit` | `VARCHAR(50)` | NULL | Unit of measurement (e.g., "ms", "MB", "requests/sec") |
| `is_baseline` | `BOOLEAN` | NOT NULL, DEFAULT FALSE | Whether this is a baseline measurement |
| `run_timestamp` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when test was run |

**Indexes:**
- `idx_performance_metric_repo_id` on `repo_id`
- `idx_performance_metric_commit_id` on `commit_id`
- `idx_performance_metric_test_suite` on `test_suite_name`
- `idx_performance_metric_repo_commit` on `(repo_id, commit_id)`

**Notes:**
- Multiple metrics can be recorded per test run
- Baseline metrics have `commit_id = NULL`
- Metrics can be aggregated for comparison reports

---

#### 6. `scan_schedule`

Stores scan scheduling information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing schedule ID |
| `repo_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `repo.id` | Reference to repository |
| `scan_scope` | `VARCHAR(50)` | NOT NULL, CHECK (`scan_scope` IN ('whole_repo', 'incremental', 'per_commit')) | Scan scope type |
| `schedule_type` | `VARCHAR(50)` | NOT NULL, CHECK (`schedule_type` IN ('cron', 'event', 'manual')) | Schedule type |
| `schedule_config` | `JSONB` | NOT NULL | Schedule configuration (cron expression, event triggers, etc.) |
| `enabled` | `BOOLEAN` | NOT NULL, DEFAULT TRUE | Whether schedule is enabled |
| `last_run_at` | `TIMESTAMP` | NULL | Timestamp of last execution |
| `next_run_at` | `TIMESTAMP` | NULL | Timestamp of next scheduled execution |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was created |
| `updated_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was last updated |

**Indexes:**
- `idx_scan_schedule_repo_id` on `repo_id`
- `idx_scan_schedule_enabled` on `enabled`
- `idx_scan_schedule_next_run` on `next_run_at`

**Notes:**
- `schedule_config` JSONB structure varies by `schedule_type`:
  - `cron`: `{"expression": "0 0 * * *", "timezone": "UTC"}`
  - `event`: `{"event_type": "push", "branch": "main"}`
  - `manual`: `{}`

---

#### 7. `orchestration_run`

Tracks orchestration execution runs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | PRIMARY KEY | Auto-incrementing run ID |
| `repo_id` | `BIGINT` | NOT NULL, FOREIGN KEY → `repo.id` | Reference to repository |
| `bom_id` | `BIGINT` | NULL, FOREIGN KEY → `bom.id` | Reference to BOM (if scan was executed) |
| `run_type` | `VARCHAR(50)` | NOT NULL, CHECK (`run_type` IN ('scan', 'gcco', 'gcgm', 'full')) | Type of orchestration run |
| `status` | `VARCHAR(20)` | NOT NULL, CHECK (`status` IN ('pending', 'in_progress', 'success', 'failed', 'cancelled')) | Run status |
| `start_timestamp` | `TIMESTAMP` | NULL | Run start time |
| `end_timestamp` | `TIMESTAMP` | NULL | Run end time |
| `execution_time_seconds` | `NUMERIC(10, 3)` | NULL | Execution time in seconds |
| `error_message` | `TEXT` | NULL | Error message if status is 'failed' |
| `config` | `JSONB` | NOT NULL | Run configuration |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was created |
| `updated_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Timestamp when record was last updated |

**Indexes:**
- `idx_orchestration_run_repo_id` on `repo_id`
- `idx_orchestration_run_bom_id` on `bom_id`
- `idx_orchestration_run_status` on `status`
- `idx_orchestration_run_repo_status` on `(repo_id, status)`

**Notes:**
- Tracks complete orchestration workflow execution
- `run_type='full'` indicates complete workflow (scan → GCCO → GCGM)

---

## GCRS Enhancements

### Scan Scope Features

GCRS needs to support three scan scopes:

#### 1. Whole Repo (Baseline)
- Scans entire repository
- Default behavior (already implemented)
- Use case: Initial scan, full repository analysis

**Implementation:**
- No changes needed (current behavior)

#### 2. Incremental (Since Datetime)
- Scans only files modified since a given datetime
- Use case: Regular scheduled scans, tracking changes over time

**Implementation:**
- Add `since_datetime` parameter to `do_the_repo_scan()`
- Filter files by `most_recent_commit_date >= since_datetime`
- Update `ScanParams` model to include `since_datetime: datetime | None`

#### 3. Per Commit
- Scans files changed in a specific commit
- Use case: Pre-commit hooks, commit-level analysis

**Implementation:**
- Add `commit_hash` parameter to `do_the_repo_scan()`
- Use `git diff` to get files changed in commit
- Scan only those files at that commit state

**TODO List for GCRS:**
- [ ] Add `since_datetime` parameter to scan functions
- [ ] Implement incremental scan filtering logic
- [ ] Add `commit_hash` parameter to scan functions
- [ ] Implement per-commit scan using git diff
- [ ] Update `ScanParams` model with new fields
- [ ] Update API endpoints to accept new parameters
- [ ] Add tests for incremental and per-commit scans
- [ ] Update documentation

## GCCO (Green Cloud Code Optimizer)

### Rule System

#### Rule Discovery (Phase 1)

**Configuration File: `rules.yaml`**

```yaml
rules:
  - id: "PY001"
    description: "Inefficient loop pattern - using range(len()) instead of enumerate()"
    category: "code"
    target_language: "python"
    module_path: "gcrs/rules/python/inefficient_loop.py"
    enabled: true
  
  - id: "PY002"
    description: "Unnecessary list comprehension in loop"
    category: "code"
    target_language: "python"
    module_path: "gcrs/rules/python/unnecessary_comprehension.py"
    enabled: true
  
  - id: "JS001"
    description: "Inefficient array operations"
    category: "code"
    target_language: "javascript"
    module_path: "gcrs/rules/javascript/inefficient_array.py"
    enabled: true
  
  - id: "DOCKER001"
    description: "Inefficient Docker layer caching"
    category: "technology"
    target_technology: "docker"
    module_path: "gcrs/rules/docker/inefficient_layers.py"
    enabled: true
```

**Rule Loading:**
- Load rules from `rules.yaml` on orchestrator startup
- Cache rules in memory
- Reload on configuration change (hot reload support)

#### Pattern Module Interface

All pattern identification modules must implement a standard interface:

```python
def analyze(file_path: Path, language: str | None, technology: str | None) -> list[Finding]:
    """
    Analyze a file for inefficient code patterns.
    
    Args:
        file_path: Path to the file to analyze
        language: Programming language of the file (if applicable)
        technology: Technology stack (if applicable)
    
    Returns:
        List of Finding objects (empty list if no matches)
    
    Raises:
        AnalysisError: If analysis fails (will be caught and logged)
    """
    # 1. Parse file to AST
    # 2. Walk AST looking for patterns
    # 3. Return list of findings
    pass
```

**Finding Object:**
```python
@dataclass
class Finding:
    line_start: int
    line_end: int
    rule_id: str
    message: str  # Optional human-readable message
```

#### Rule Execution

**Parallel Execution:**
- Execute rules in parallel per file (using `concurrent.futures.ThreadPoolExecutor` or `ProcessPoolExecutor`)
- Batch files for processing (configurable batch size)
- Error handling: Skip failed rules, continue with others

**Error Handling (MVP):**
- If pattern module fails: Skip that rule, log error, continue
- If file parsing fails: Skip file, log error, continue
- If all rules fail for a file: Log warning, continue

**Future Error Handling:**
- Configurable error handling strategy:
  - `skip_rule`: Skip failed rule (default)
  - `skip_file`: Skip entire file if any rule fails
  - `fail_run`: Fail entire run if any error occurs

#### AI Confirmation Layer (Phase 2)

**Purpose:** Reduce false positives from AST pattern matching

**Flow:**
1. After AST analysis generates findings
2. For each finding:
   - Extract code snippet (lines `line_start` to `line_end`)
   - Call AI service with:
     - Code snippet
     - Rule description
     - Context (surrounding code)
   - AI returns: `confirmed: bool`, `confidence: float`, `reason: str`
3. Update finding status:
   - `ai_confirmed = True` → status = `confirmed`
   - `ai_confirmed = False` → status = `dismissed`
   - Store `ai_confidence` score

**AI Service Interface:**
```python
def confirm_finding(
    code_snippet: str,
    rule_description: str,
    context: str,
    language: str
) -> tuple[bool, float, str]:
    """
    Confirm or dismiss a finding using AI.
    
    Returns:
        (confirmed: bool, confidence: float, reason: str)
    """
    pass
```

**Stretch Goals:**
- AI refactoring: Generate suggested code fixes
- Human approval workflow: Present findings and AI suggestions for review
- Auto-apply changes: Automatically apply AI-suggested fixes (with approval)

## GCGM (Green Cloud Goal Manager)

### Cost Estimation

**Metrics:**
- **Processing/RAM savings**: Estimated reduction in compute resources
- **Performance improvement**: Estimated speedup (percentage or factor)
- **Power/cooling costs**: Estimated data center cost savings (currency)
- **Developer time**: Estimated time saved from inefficiency (hours)

**Estimation Methods:**
- Rule-based: Each rule has associated cost estimation logic
- Historical data: Learn from previous fixes
- AI-assisted: Use AI to estimate impact (future)

### Jira Integration

**Features:**
- Create Jira issues for findings
- Link issues to findings in database
- Sync issue status from Jira
- Support bulk issue creation

**Issue Template:**
- Title: `[GCCO] {rule_id}: {rule_description}`
- Description: Include finding details, code snippet, cost estimate
- Labels: `gcrs`, `code-optimization`, `{language}`
- Priority: Based on cost savings estimate

### Performance Measurement

**Test Execution:**
1. **Baseline**: Run automated tests before fixes
   - Record metrics (execution time, memory, CPU, etc.)
   - Store in `performance_metric` table with `is_baseline = true`
2. **After Fixes**: Run tests after applying fixes
   - Record same metrics
   - Store with `is_baseline = false` and `commit_id`

**Comparison Reports:**
- Single finding: Before/after for that specific fix
- Single file: Aggregate before/after for all fixes in file
- Single commit: Aggregate before/after for all fixes in commit
- Multiple commits: Aggregate across commit range (stretch goal)

**Test Discovery:**
- Auto-discover test suites in repository
- Support common test frameworks (pytest, jest, etc.)
- Configurable test execution commands

### Stretch Goals

1. **Story Points/Time Estimation**
   - Estimate story points for fixing inefficiency
   - Estimate developer time needed
   - Store in `cost_estimate` table

2. **Project Plan Generation**
   - Generate project plan for fixing multiple findings
   - Prioritize by cost savings
   - Group related findings
   - Estimate timeline

## Implementation Phases

### Phase 1: MVP (Minimum Viable Product)

**Orchestrator:**
- [ ] Basic orchestrator module structure
- [ ] GCRS integration (whole repo scans only)
- [ ] GCCO integration (rule loading, pattern execution)
- [ ] Findings persistence to database
- [ ] Error handling (skip rule on failure)

**GCCO:**
- [ ] Rule configuration file (`rules.yaml`)
- [ ] Rule loading and discovery
- [ ] Pattern module interface definition
- [ ] AST parsing and pattern matching
- [ ] Findings generation and persistence
- [ ] Parallel rule execution

**Database:**
- [ ] Create `rule` table
- [ ] Create `finding` table
- [ ] Create `orchestration_run` table
- [ ] Migration scripts

**GCRS Enhancements:**
- [ ] Add scan scope parameters (incremental, per-commit) - TODO list created

### Phase 2: AI Confirmation & GCGM Core

**GCCO:**
- [ ] AI confirmation layer
- [ ] AI service integration
- [ ] Finding status management (pending → confirmed/dismissed)

**GCGM:**
- [ ] Cost estimation logic
- [ ] Cost estimation persistence
- [ ] Basic performance test execution
- [ ] Baseline metric collection

**Database:**
- [ ] Create `cost_estimate` table
- [ ] Create `performance_metric` table
- [ ] Update `finding` table with AI fields

### Phase 3: Advanced Features

**Orchestrator:**
- [ ] Scan scheduling (cron, event-driven)
- [ ] Retry logic
- [ ] Workflow state management

**GCGM:**
- [ ] Jira integration
- [ ] Performance comparison reports
- [ ] Aggregate cost savings

**GCRS:**
- [ ] Incremental scan implementation
- [ ] Per-commit scan implementation

### Phase 4: Stretch Goals

**GCCO:**
- [ ] AI code refactoring
- [ ] Human approval workflow
- [ ] Auto-apply changes

**GCGM:**
- [ ] Story points/time estimation
- [ ] Project plan generation
- [ ] Multi-commit comparisons

**Orchestrator:**
- [ ] Advanced scheduling
- [ ] Workflow visualization
- [ ] Performance optimization

## File Structure

```
gcrs/
├── orchestrator/
│   ├── __init__.py
│   ├── orchestrator.py      # Main orchestrator class
│   ├── scheduler.py         # Scan scheduling
│   ├── gcco_runner.py       # GCCO execution
│   ├── gcgm_runner.py       # GCGM execution
│   └── config.py            # Orchestrator configuration
├── rules/
│   ├── __init__.py
│   ├── python/
│   │   ├── __init__.py
│   │   ├── inefficient_loop.py
│   │   └── unnecessary_comprehension.py
│   ├── javascript/
│   │   ├── __init__.py
│   │   └── inefficient_array.py
│   └── docker/
│       ├── __init__.py
│       └── inefficient_layers.py
├── gcco/
│   ├── __init__.py
│   ├── rule_loader.py       # Load rules from config
│   ├── pattern_executor.py  # Execute pattern modules
│   ├── ai_confirmation.py   # AI confirmation layer (Phase 2)
│   └── models.py            # Finding, Rule models
├── gcgm/
│   ├── __init__.py
│   ├── cost_estimator.py    # Cost estimation logic
│   ├── jira_integration.py  # Jira API integration
│   ├── performance_tester.py # Test execution
│   └── comparison_generator.py # Before/after reports
└── rules.yaml               # Rule configuration (Phase 1)
```

## API Design

### Orchestrator API

```python
class Orchestrator:
    def schedule_scan(
        self,
        repo_id: int,
        scan_scope: ScanScope,
        schedule_config: dict
    ) -> int:  # Returns schedule_id
        """Schedule a scan."""
        pass
    
    def execute_scan_workflow(
        self,
        repo_id: int,
        scan_scope: ScanScope,
        filter_options: dict | None = None
    ) -> int:  # Returns orchestration_run_id
        """Execute complete scan workflow."""
        pass
    
    def execute_gcco_analysis(
        self,
        bom_id: int,
        filter_options: dict | None = None
    ) -> int:  # Returns orchestration_run_id
        """Execute GCCO analysis on BOM."""
        pass
    
    def execute_gcgm_workflow(
        self,
        finding_ids: list[int]
    ) -> int:  # Returns orchestration_run_id
        """Execute GCGM operations."""
        pass
```

### GCCO API

```python
class GCCO:
    def load_rules(self, config_path: Path) -> list[Rule]:
        """Load rules from configuration."""
        pass
    
    def analyze_file(
        self,
        file_path: Path,
        language: str | None,
        technology: str | None
    ) -> list[Finding]:
        """Analyze a file using all applicable rules."""
        pass
    
    def confirm_findings_with_ai(
        self,
        findings: list[Finding]
    ) -> list[Finding]:
        """Confirm findings using AI (Phase 2)."""
        pass
```

### GCGM API

```python
class GCGM:
    def estimate_cost_savings(
        self,
        finding_id: int
    ) -> CostEstimate:
        """Estimate cost savings for a finding."""
        pass
    
    def create_jira_issues(
        self,
        finding_ids: list[int],
        project_key: str
    ) -> list[JiraIssue]:
        """Create Jira issues for findings."""
        pass
    
    def run_performance_tests(
        self,
        repo_id: int,
        commit_hash: str | None = None
    ) -> list[PerformanceMetric]:
        """Run performance tests and record metrics."""
        pass
    
    def generate_comparison_report(
        self,
        finding_ids: list[int]
    ) -> ComparisonReport:
        """Generate before/after comparison report."""
        pass
```

## Error Handling

### Error Handling Strategies

**MVP (Phase 1):**
- Rule execution failure: Skip rule, log error, continue
- File parsing failure: Skip file, log error, continue
- Database error: Log error, fail operation

**Future (Configurable):**
- `skip_rule`: Skip failed rule (default)
- `skip_file`: Skip entire file if any rule fails
- `fail_run`: Fail entire run if any error occurs

### Retry Logic

**Scheduler:**
- Configurable max retries
- Exponential backoff
- Retry queue management
- Dead letter queue for permanent failures

## Configuration

### Orchestrator Configuration

```yaml
orchestrator:
  max_workers: 4  # Parallel rule execution
  batch_size: 100  # Files per batch
  error_handling: "skip_rule"  # skip_rule | skip_file | fail_run
  retry:
    max_retries: 3
    backoff_factor: 2.0
```

### GCCO Configuration

```yaml
gcco:
  rules_config: "rules.yaml"
  ai_service:
    provider: "openai"  # openai | anthropic | custom
    model: "gpt-4"
    api_key_env: "OPENAI_API_KEY"
    enabled: false  # Phase 2
```

### GCGM Configuration

```yaml
gcgm:
  jira:
    enabled: false
    base_url: "https://your-domain.atlassian.net"
    api_token_env: "JIRA_API_TOKEN"
  performance_tests:
    enabled: true
    test_command: "pytest --benchmark-only"
    timeout_seconds: 300
```

## Testing Strategy

### Unit Tests
- Rule loading and discovery
- Pattern module execution
- Finding generation
- Cost estimation logic

### Integration Tests
- Orchestrator → GCRS → Database
- Orchestrator → GCCO → Database
- Orchestrator → GCGM → Database
- Complete workflow end-to-end

### Performance Tests
- Parallel rule execution performance
- Large repository scan performance
- Database query optimization

## Security Considerations

1. **Rule Module Security**
   - Sandbox pattern module execution
   - Validate module paths (prevent path traversal)
   - Code signing for trusted modules (future)

2. **API Key Management**
   - Store API keys in environment variables
   - Never commit keys to repository
   - Rotate keys regularly

3. **Database Security**
   - Use parameterized queries
   - Limit database user permissions
   - Encrypt sensitive data

4. **File System Access**
   - Validate file paths
   - Restrict file access to repository root
   - Prevent arbitrary code execution

## Monitoring & Logging

### Metrics to Track
- Orchestration run duration
- Number of findings per run
- Rule execution success/failure rates
- Cost savings estimates
- Performance test results

### Logging
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for request tracking
- Audit trail for all operations

## Future Considerations

1. **Rule Marketplace**
   - Community-contributed rules
   - Rule versioning
   - Rule validation and testing

2. **Multi-Language Support**
   - Support for more programming languages
   - Language-specific AST parsers

3. **Cloud Integration**
   - AWS/Azure/GCP cost estimation
   - Cloud resource optimization

4. **CI/CD Integration**
   - Pre-commit hooks
   - Pull request analysis
   - Automated fix suggestions

5. **Dashboard/UI**
   - Visualization of findings
   - Cost savings reports
   - Performance comparisons
   - Rule management interface

---

## Appendix: Entity Relationship Diagram (Extended)

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
                └───< (many) finding
                       │
                       │ (1)              (1)
                       │                  │
                       ├───> (1) cost_estimate
                       │
                       └───< (many) jira_issue

repo (1) ────< (many) bom
  │
  │ (1)
  │
  └───< (many) scan_schedule

repo (1) ────< (many) orchestration_run
  │
  └───> (1) bom

rule (1) ────< (many) finding

repo (1) ────< (many) performance_metric
  │
  └───> (1) repo_commit
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-16  
**Status:** Design Phase


