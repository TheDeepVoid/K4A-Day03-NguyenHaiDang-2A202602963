"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        prompt_lower = prompt.lower()

        # Nhận diện phản hồi sau khi nhận Observation trong ReAct Loop
        if "[observation" in prompt_lower or "observation từ" in prompt_lower:
            return {
                "type": "text",
                "content": "[Mock Agent Response]: Đã hoàn tất tra cứu và cập nhật dữ liệu tài chính thành công. Cảnh báo: Hạn mức chi tiêu ăn uống đã sử dụng trên 80%, vui lòng chú ý tiết kiệm.",
                "thought": "Đã nhận được kết quả Observation từ Tool, tổng hợp câu trả lời cuối cùng."
            }

        # Mô phỏng nhận diện intent gọi Tool cho cả Personal Finance và Học vụ
        if "kichi" in prompt_lower or "350k" in prompt_lower or "ghi nhận" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "update_finance_database",
                "arguments": {
                    "category": "ăn uống",
                    "amount": 350000,
                    "description": "Ăn tối tại Kichi Kichi",
                    "destination": "Notion"
                },
                "thought": "Người dùng vừa chi tiêu 350.000 VNĐ cho bữa ăn tối tại Kichi Kichi. Tôi sẽ gọi tool 'update_finance_database' để ghi nhận vào Notion và kiểm tra cảnh báo ngân sách."
            }
        elif "crypto" in prompt_lower or "tiền ảo" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "check_budget_limits_and_history",
                "arguments": {"category": "crypto"},
                "thought": "Người dùng muốn tra cứu danh mục ngân sách 'crypto'. Tôi sẽ gọi tool check_budget_limits_and_history để kiểm tra hạn mức danh mục này."
            }
        elif "ngân sách" in prompt_lower or "ăn uống" in prompt_lower or "hạn mức" in prompt_lower or "định mức" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "check_budget_limits_and_history",
                "arguments": {"category": "ăn uống"},
                "thought": "Người dùng muốn kiểm tra ngân sách và hạn mức chi tiêu ăn uống. Tôi sẽ gọi tool check_budget_limits_and_history."
            }
        elif "sv2026001" in prompt_lower and "đặt lịch" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {"student_id": "SV2026001", "datetime_str": "14:00 15/09/2026", "advisor_name": "PGS.TS Nguyễn Văn A"},
                "thought": "Người dùng yêu cầu đặt lịch hẹn tư vấn cho sinh viên SV2026001. Tôi sẽ gọi tool schedule_appointment."
            }
        elif "sv2026001" in prompt_lower or "tra cứu" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": "SV2026001"},
                "thought": "Người dùng muốn tra cứu thông tin học vụ của sinh viên SV2026001. Tôi sẽ gọi tool academic_query."
            }
        elif "50/30/20" in prompt_lower or "nguyên tắc" in prompt_lower or "tài chính" in prompt_lower:
            return {
                "type": "text",
                "content": "[Mock Agent Response]: Quy tắc 50/30/20 là phương pháp phân bổ thu nhập cá nhân: 50% cho nhu cầu thiết yếu, 30% cho mong muốn cá nhân và 20% cho tiết kiệm/đầu tư.",
                "thought": "Câu hỏi chung về nguyên tắc tài chính 50/30/20, trả lời trực tiếp không cần gọi Tool."
            }
        else:
            return {
                "type": "text",
                "content": f"[Mock Agent Response]: Xin chào! Tôi là Trợ lý Quản lý Chi tiêu Cá nhân. Tôi có thể giúp bạn kiểm tra ngân sách, ghi chép giao dịch và cảnh báo vượt hạn mức.",
                "thought": "Câu hỏi chung, trả lời trực tiếp không cần gọi Tool."
            }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
