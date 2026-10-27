import importlib
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("ONE_STEP_DB", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("ONE_STEP_MODEL_MODE", "mock")
    root = str(Path(__file__).resolve().parents[1] / "backend")
    if root not in sys.path: sys.path.insert(0, root)
    import app as api
    importlib.reload(api)
    return TestClient(api.app)


def start(c):
    response=c.post('/api/sessions', json={'skill_type':'breathing'})
    assert response.status_code == 201
    return response.json()['id']


def finish(c, sid, status='completed', seconds=70):
    response=c.patch(f'/api/sessions/{sid}', json={'status':status,'actual_exercise_seconds':seconds,'paused_seconds':0})
    assert response.status_code==200
    return response.json()


def test_support_independent_of_model(env, monkeypatch):
    monkeypatch.setenv('ONE_STEP_MODEL_MODE','fail')
    r=env.get('/support.html')
    assert r.status_code == 200 and '988' in r.text and 'not monitored' in r.text


def test_home_has_persistent_support_link(env):
    r=env.get('/')
    assert r.status_code==200 and 'href="/support.html"' in r.text


def test_start_and_complete_persists(env):
    sid=start(env)
    row=finish(env,sid)
    assert row['status']=='completed' and row['actual_exercise_seconds']==70
    assert env.get('/api/sessions').json()[0]['id']==sid


def test_leave_early_saves_no_penalty(env):
    sid=start(env)
    row=finish(env,sid,'left_early',17.4)
    assert row['status']=='left_early' and row['actual_exercise_seconds']==17.4


def test_interrupted_session_record(env):
    sid=start(env)
    assert finish(env,sid,'interrupted',0)['status']=='interrupted'


def test_no_double_completion(env):
    sid=start(env);finish(env,sid)
    assert env.patch(f'/api/sessions/{sid}',json={'status':'completed','actual_exercise_seconds':71}).status_code==409


def test_model_mock_chat_and_history(env):
    sid=start(env);finish(env,sid)
    answer=env.post('/api/chat',json={'session_id':sid,'text':'Fictional example: I struggled with the pace.'}).json()
    assert answer['response_mode']=='mock'
    rows=env.get(f'/api/messages?session_id={sid}').json()
    assert [m['role'] for m in rows]==['user','assistant']
    assert rows[-1]['response_mode']=='mock'


def test_model_failure_fallback_saves(env, monkeypatch):
    sid=start(env);finish(env,sid)
    monkeypatch.setenv('ONE_STEP_MODEL_MODE','fail')
    answer=env.post('/api/chat',json={'session_id':sid,'text':'Fictional test: hello'}).json()
    assert answer['response_mode']=='fallback'
    assert 'Crisis support' in answer['reply']
    assert env.get('/support.html').status_code==200


def test_crisis_keyword_fixed_response(env):
    sid=start(env);finish(env,sid)
    answer=env.post('/api/chat',json={'session_id':sid,'text':'Fictional test: kill myself'}).json()
    assert answer['response_mode']=='safety' and 'not monitored' in answer['reply']


def test_reject_chat_during_skill(env):
    sid=start(env)
    assert env.post('/api/chat',json={'session_id':sid,'text':'Hello'}).status_code==409


def test_invalid_session_and_skill(env):
    assert env.post('/api/sessions',json={'skill_type':'fictional-unapproved'}).status_code==422
    assert env.get('/api/messages?session_id=99999').status_code==404


def test_read_only_support_works_without_any_session(env):
    assert env.get('/support.html').status_code == 200
    assert env.get('/api/sessions').json()==[]
