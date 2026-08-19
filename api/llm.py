import re
import os
from typing import Set
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import HTTPException
from dotenv import load_dotenv

# Load GEMINI_API_KEY from environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def extract_numbers(text: str) -> Set[float]:
    """
    Extracts all numeric values (integers and decimals) from the given text
    and returns them as a set of floats. Thousand separator commas are normalized.
    """
    # Regex to capture decimals and integers, optionally with thousand separator commas (no word boundaries)
    pattern = r'\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?'
    raw_numbers = re.findall(pattern, text)
    numbers = set()
    for num in raw_numbers:
        cleaned = num.replace(',', '')
        try:
            val = float(cleaned)
            numbers.add(val)
        except ValueError:
            continue
    return numbers

def generate_with_numeric_validation(
    prompt: str,
    system_instruction: str = "제시된 정보의 숫자만을 정확히 사용하여 텍스트를 작성하십시오. 제시되지 않은 통계 수치를 임의로 창작해 기재하지 마십시오.",
    max_retries: int = 2
) -> str:
    """
    Calls the Gemini model using LangChain with zero temperature
    and validates that all numbers printed in the response are present in either the prompt or system instruction.
    Allows basic single-digit integers (0-9) to prevent false positives in formatting/numbering.
    Retries up to max_retries times with direct feedback, throwing a 500 error if it keeps hallucinating numbers.
    Model: GEMINI_MODEL_NAME env var (default: gemini-2.5-flash)
    """
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="GEMINI_API_KEY 환경변수가 설정되지 않았습니다."
        )

    # Compile whitelist numbers from inputs
    allowed_numbers = extract_numbers(prompt) | extract_numbers(system_instruction)
    
    # Pre-approve basic numbering/indices (0 to 9) to prevent false positives in markdown list indexing
    for i in range(10):
        allowed_numbers.add(float(i))
        
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash")
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.0
    )
    
    current_prompt = prompt
    last_response = ""
    
    for attempt in range(max_retries + 1):
        try:
            messages = [
                ("system", system_instruction),
                ("user", current_prompt)
            ]
            response = llm.invoke(messages)
            last_response = str(response.content)
            
            # Extract numbers from response
            response_numbers = extract_numbers(last_response)
            
            # Check if response numbers are a subset of allowed numbers
            forbidden_numbers = response_numbers - allowed_numbers
            
            if not forbidden_numbers:
                # Validation passes
                return last_response
            
            print(f"[Attempt {attempt + 1}] LLM Validation Failed. Hallucinated numbers detected: {forbidden_numbers}")
            
            # Add strict feedback for retry attempt
            current_prompt = (
                f"{prompt}\n\n"
                f"[경고: 이전 작성물에 제공되지 않은 숫자 {forbidden_numbers}가 포함되어 수치 검증에 실패했습니다. "
                f"오직 지문에 제공된 정확한 숫자들만 인용하여 다시 작성하십시오. 임의의 숫자를 창작하지 마십시오.]"
            )
            
        except Exception as e:
            print(f"Gemini API invocation error: {str(e)}")
            if attempt == max_retries:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Gemini API 실행 중 오류가 발생했습니다: {str(e)}"
                )
                
    # If all attempts fail
    raise HTTPException(
        status_code=500,
        detail="LLM 수치 검증 실패: AI가 제공되지 않은 임의의 수치를 반복적으로 생성했습니다."
    )
