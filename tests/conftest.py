import pytest
from app.sql_database import connect
from app.data_pipeline import run_pipeline, save_to_sqlite
from app.analytics import Analytics


@pytest.fixture
def sample_db(tmp_path):
    db = tmp_path / "test.sqlite"
    datasets, report = run_pipeline("data/sample")
    save_to_sqlite(datasets, str(db))
    return str(db), report


@pytest.fixture
def conn(sample_db):
    db, _ = sample_db
    c = connect(db)
    yield c
    c.close()


@pytest.fixture
def analytics(conn):
    return Analytics(conn)


@pytest.fixture
def client(sample_db):
    from app.main import create_app

    db, _ = sample_db
    return create_app(db_path=db, mongo_repo=None)
