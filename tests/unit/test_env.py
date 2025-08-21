"""Test environment setup."""
import sys
import pytest
from fastapi import FastAPI
from pydantic import BaseModel

def test_python_version():
    """Test Python version is 3.8+."""
    assert sys.version_info >= (3, 8), "Python version should be 3.8 or higher"

def test_fastapi_import():
    """Test FastAPI can be imported."""
    app = FastAPI()
    assert app is not None, "FastAPI should be importable"

def test_pydantic_import():
    """Test Pydantic can be imported and used."""
    class TestModel(BaseModel):
        name: str
        value: int
    
    model = TestModel(name="test", value=42)
    assert model.name == "test", "Pydantic model should work"
    assert model.value == 42, "Pydantic model should work"
