import pytest
from customsdesk.generate import generate
from customsdesk.warehouse import engine

@pytest.fixture
def source(tmp_path):
    path=tmp_path/'source'; generate(path,shipments=50,queries=80,parts=20)
    return path
@pytest.fixture
def db():
    result=engine('sqlite:///:memory:')
    yield result
    result.dispose()
