import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from api.llm import extract_numbers, generate_with_numeric_validation

def test_extract_numbers():
    # 1. Test extraction of various numeric formats from text
    text = "양천구의 수검률은 41.9% 이며, 미수검자는 1,034명입니다. (2024년 기준, target: 300)"
    nums = extract_numbers(text)
    
    # 41.9, 1034, 2024, 300 must be extracted
    assert 41.9 in nums
    assert 1034.0 in nums
    assert 2024.0 in nums
    assert 300.0 in nums
    assert len(nums) == 4

@patch("api.llm.ChatGoogleGenerativeAI")
def test_validation_passes_when_numbers_are_whitelisted(mock_chat_class):
    # 2. Test successful pass when the LLM outputs only whitelisted numbers
    mock_llm = MagicMock()
    mock_chat_class.return_value = mock_llm
    
    mock_response = MagicMock()
    mock_response.content = "2024년도 미수검자는 총 1,034명이며 1순위 타겟입니다."
    mock_llm.invoke.return_value = mock_response
    
    prompt = "2024년도 미수검자는 1,034명입니다."
    result = generate_with_numeric_validation(prompt)
    
    assert "1,034명" in result
    assert mock_llm.invoke.call_count == 1

@patch("api.llm.ChatGoogleGenerativeAI")
def test_validation_fails_and_retries_then_passes(mock_chat_class):
    # 3. Test retry behavior: first call hallucinates 5000, retry corrects it to 1034
    mock_llm = MagicMock()
    mock_chat_class.return_value = mock_llm
    
    # First response (has forbidden 5,000)
    resp1 = MagicMock()
    resp1.content = "미수검자는 5,000명으로 예측됩니다."
    
    # Second response (has correct 1,034)
    resp2 = MagicMock()
    resp2.content = "미수검자는 1,034명입니다."
    
    mock_llm.invoke.side_effect = [resp1, resp2]
    
    prompt = "2024년 미수검자 1,034명."
    result = generate_with_numeric_validation(prompt, max_retries=2)
    
    assert "1,034명" in result
    assert mock_llm.invoke.call_count == 2

@patch("api.llm.ChatGoogleGenerativeAI")
def test_validation_fails_completely_after_max_retries(mock_chat_class):
    # 4. Test exhaustion of retries (raised HTTPException 500)
    mock_llm = MagicMock()
    mock_chat_class.return_value = mock_llm
    
    resp = MagicMock()
    resp.content = "미수검자는 9,999명입니다."
    mock_llm.invoke.return_value = resp
    
    prompt = "2024년 미수검자 1,034명."
    
    with pytest.raises(HTTPException) as exc_info:
        generate_with_numeric_validation(prompt, max_retries=2)
        
    assert exc_info.value.status_code == 500
    assert "LLM 수치 검증 실패" in exc_info.value.detail
    assert mock_llm.invoke.call_count == 3  # Initial (1) + Retries (2) = 3
