import pytest
from customsdesk.dashboard import response_bucket,validate_model
from customsdesk.pipeline import run
from pathlib import Path

@pytest.mark.parametrize("value,expected",[(None,"Not responded"),(0,"01: 0–24h"),(24,"01: 0–24h"),(24.1,"02: >24–48h"),(48,"02: >24–48h"),(72,"03: >48–72h"),(73,"04: >72h")])
def test_response_band(value,expected):
    assert response_bucket(value)==expected

def test_negative_response():
    with pytest.raises(ValueError):response_bucket(-1)

def test_relationship_contract(db,source,tmp_path):
    run(db,source,tmp_path/"reports")
    names,checks=validate_model(Path(__file__).resolve().parents[1],db)
    assert len(names)==22 and len(checks)==11
    assert all(c["status"]=="PASS" for c in checks)


def test_existing_password_preserved(tmp_path,monkeypatch):
    from customsdesk.local_setup import prepare_env
    monkeypatch.setattr("customsdesk.local_setup.choose_port",lambda *a:5434)
    (tmp_path/".env").write_text("POSTGRES_PASSWORD=keep-existing-password\n")
    settings,rotated,_=prepare_env(tmp_path)
    assert not rotated and settings.url.password=="keep-existing-password"


def test_existing_url_preserved(tmp_path):
    from customsdesk.local_setup import prepare_env,SetupError
    p=tmp_path/".env";content="DATABASE_URL=postgresql+psycopg://u:p@localhost:5434/customsdesk\n";p.write_text(content)
    with pytest.raises(SetupError,match="preserved"):prepare_env(tmp_path)
    assert p.read_text()==content
