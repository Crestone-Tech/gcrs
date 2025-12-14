from gcrs.db import get_db_session, get_or_create_repo

with get_db_session() as session:
    repo = get_or_create_repo(
        session=session,
        uri="https://github.com/user/repo.git",
        git_owner_account="user",
        repo_name="repo",
    )
    print(repo)