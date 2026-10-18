"""Smoke checks must release database handles before temporary folder cleanup."""

import importlib.util
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize('target', ['bundle', 'installer'])
@pytest.mark.parametrize('painting_count', [900, 899])
def test_smoke_closes_database_even_when_collection_check_fails(tmp_path, monkeypatch, target, painting_count):
    script = 'packaging/build_bundle.py' if target == 'bundle' else 'packaging/windows/smoke_test.py'
    spec = importlib.util.spec_from_file_location(f'{target}_smoke_check', ROOT / script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_connect = sqlite3.connect
    connections = []

    def connect(*args, **kwargs):
        database = original_connect(*args, **kwargs)
        connections.append(database)
        return database

    def run(command, **kwargs):
        # Stand in for the launched game; verification uses a real SQLite file.
        if '--smoke-test' in command:
            data = Path(command[command.index('--data-dir') + 1])
            data.mkdir(parents=True, exist_ok=True)
            with closing(original_connect(data / 'progress.sqlite3')) as database:
                database.execute('CREATE TABLE paintings (id INTEGER PRIMARY KEY)')
                database.executemany('INSERT INTO paintings VALUES (?)', [(n,) for n in range(painting_count)])
                database.commit()

    monkeypatch.setattr(module.sqlite3, 'connect', connect)
    monkeypatch.setattr(module.subprocess, 'run', run)
    if target == 'bundle':
        monkeypatch.setattr(sys, 'argv', ['build_bundle.py', '--dist-dir', str(tmp_path / 'bundle')])
        monkeypatch.setattr(module, 'validate_resources', lambda bundle: None)
    else:
        monkeypatch.setattr(module, 'ROOT', tmp_path)
        (tmp_path / 'dist').mkdir()
        (tmp_path / 'dist/Piksel-Atolyesi-0.17.0-Setup-x64.exe').touch()
    try:
        if painting_count == 900:
            module.main()
        else:
            with pytest.raises(RuntimeError, match='collection is incomplete'):
                module.main()
        assert len(connections) == 1
        # Retain a reference to catch missing close() on Linux as well as Windows.
        for database in connections:
            with pytest.raises(sqlite3.ProgrammingError, match='closed database'):
                database.execute('SELECT 1')
    finally:
        for database in connections:
            database.close()
