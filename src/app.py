"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
Chủ đề: Trợ lý Quản lý Chi tiêu & Cảnh báo Ngân sách Cá nhân (Personal Finance Agent).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer, MCPPersonalFinanceServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")
    return response


def format_observation_summary(tool_name: str, obs_data: dict) -> str:
    """Định dạng kết quả trả về từ MCP Server thành văn bản súc tích, dễ hiểu"""
    if not obs_data:
        return "Chưa nhận được dữ liệu từ MCP Server."

    if obs_data.get("status") == "UNKNOWN_TOOL":
        supported = obs_data.get("supported_tools", ["check_budget_limits_and_history", "update_finance_database"])
        return (
            f"❌ [LỖI: CÔNG CỤ CHƯA ĐƯỢC THIẾT LẬP]: {obs_data.get('error', f'Công cụ {tool_name} không tồn tại.')}\n"
            f"Hệ thống đã dừng hành động để tránh ảo giác dữ liệu (Anti-Hallucination).\n"
            f"Các công cụ khả dụng hiện có trên MCP Server: {', '.join(supported)}."
        )

    if obs_data.get("status") == "EXECUTION_ERROR":
        return f"❌ [LỖI THỰC THI]: {obs_data.get('error', 'Lỗi thực thi công cụ trên hệ thống.')}"

    if obs_data.get("status") == "NOT_FOUND":
        return obs_data.get("message", "Không tìm thấy dữ liệu yêu cầu.")

    # Định dạng kết quả tra cứu ngân sách cá nhân
    if "monthly_limit" in obs_data and "spent" in obs_data and obs_data.get("action") != "TRANSACTION_RECORDED":
        cat = obs_data.get("category", "").upper()
        limit = obs_data.get("monthly_limit", 0)
        spent = obs_data.get("spent", 0)
        rem = obs_data.get("remaining", 0)
        pct = obs_data.get("usage_percentage", "")
        alert = obs_data.get("alert", "")
        return (
            f"📊 [BÁO CÁO NGÂN SÁCH - DANH MỤC {cat}]:\n"
            f"- Hạn mức định mức tháng: {limit:,.0f} VNĐ\n"
            f"- Đã chi tiêu: {spent:,.0f} VNĐ ({pct})\n"
            f"- Số dư khả dụng còn lại: {rem:,.0f} VNĐ\n"
            f"- Đánh giá & Cảnh báo: {alert}"
        )

    # Định dạng kết quả ghi nhận chi tiêu & cập nhật DB
    if obs_data.get("action") == "TRANSACTION_RECORDED":
        desc = obs_data.get("description", "")
        amt = obs_data.get("amount", 0)
        dest = obs_data.get("destination", "Notion")
        cat = obs_data.get("category", "")
        rem = obs_data.get("remaining", 0)
        limit = obs_data.get("monthly_limit", 0)
        pct = obs_data.get("usage_percentage", "")
        alert = obs_data.get("alert", "")
        return (
            f"📝 [GHI NHẬN CHI TIÊU THÀNH CÔNG]:\n"
            f"- Giao dịch: '{desc}' (-{amt:,.0f} VNĐ) đã đồng bộ vào {dest}.\n"
            f"- Danh mục: {cat}\n"
            f"- Ngân sách còn lại: {rem:,.0f} / {limit:,.0f} VNĐ ({pct} đã sử dụng)\n"
            f"- Trạng thái: {alert}"
        )

    # Định dạng kết quả học vụ sinh viên (nếu có)
    if "data" in obs_data:
        d = obs_data["data"]
        return (
            f"Kết quả tra cứu cho sinh viên {obs_data.get('student_id', '')} ({d.get('full_name', '')}): "
            f"Lớp {d.get('class', '')}, GPA: {d.get('gpa', '')}, Email: {d.get('email', '')}, "
            f"Trạng thái: {d.get('status', '')}, Cố vấn: {d.get('advisor', '')}."
        )

    if "message" in obs_data:
        return obs_data["message"]

    return f"Đã hoàn tất xử lý qua MCP Server: {json.dumps(obs_data, ensure_ascii=False)}"


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server
    Trả về danh sách trace log của phiên thực thi.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()
    current_prompt = user_query
    executed_tools = []
    last_obs_data = {}
    last_tool_name = ""

    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")

        # Gọi LLM với Native Tool Calling Specs
        llm_response = provider.generate_with_tools(current_prompt, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)

        thought = llm_response.get("thought", "Đang suy luận.")
        print(f"🧠 [Thought]: {thought}")

        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp
        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            break

        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})
            last_tool_name = tool_name

            tool_sig = (tool_name, json.dumps(arguments, sort_keys=True))
            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")

            # Kiểm tra tránh lặp vô hạn TRƯỚC khi thực thi để không gây side effect kép
            if tool_sig in executed_tools:
                print("⚠️ [ReAct Notice]: Đã phát hiện gọi trùng công cụ. Không thực thi lại, tiến hành tổng hợp câu trả lời cuối cùng.")
                final_answer = format_observation_summary(last_tool_name, last_obs_data)
                print(f"🏁 [Final Answer]: {final_answer}")
                trace_logs.append({
                    "step": step,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": f"Công cụ '{tool_name}' đã được thực thi trước đó cùng tham số. Tổng hợp kết quả từ Observation gần nhất.",
                    "output": final_answer,
                    "latency_ms": latency_ms
                })
                break

            # Thực thi Tool qua MCP Server (chỉ khi công cụ chưa được gọi cùng tham số)
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})
            last_obs_data = obs_data

            if not obs_data:
                print(f"👁️ [Observation từ MCP Server]: {{}}")
                print(f"⚠️ [CHÚ Ý]: MCP Server trả về kết quả rỗng!")
            else:
                obs_str = json.dumps(obs_data, ensure_ascii=False)
                print(f"👁️ [Observation từ MCP Server]: {obs_str}")

            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })

            executed_tools.append(tool_sig)

            # Cập nhật context cho bước ReAct tiếp theo
            obs_formatted = json.dumps(obs_data, ensure_ascii=False)
            if obs_data.get("status") in ["UNKNOWN_TOOL", "EXECUTION_ERROR"]:
                current_prompt = (
                    f"Yêu cầu ban đầu của người dùng: {user_query}\n\n"
                    f"CẢNH BÁO QUAN TRỌNG TỪ MCP SERVER:\n"
                    f"- Thao tác công cụ '{tool_name}' không thành công: {obs_formatted}\n"
                    f"- YÊU CẦU BẮT BUỘC: Bạn không được gọi lại công cụ này và TUYỆT ĐỐI KHÔNG được tự bịa đặt kết quả thành công.\n"
                    f"Hãy đưa ra thông báo lỗi chính xác, nêu rõ công cụ chưa được thiết lập trên hệ thống và hướng dẫn người dùng sử dụng các công cụ quản lý chi tiêu hiện có."
                )
            else:
                current_prompt = (
                    f"Yêu cầu ban đầu của người dùng: {user_query}\n\n"
                    f"Các bước đã thực hiện:\n"
                    f"- Đã gọi công cụ: {tool_name} với tham số {json.dumps(arguments, ensure_ascii=False)}\n"
                    f"- [Observation] Kết quả quan sát từ MCP Server:\n{obs_formatted}\n\n"
                    f"Dựa vào thông tin trên, hãy thực hiện hành động tiếp theo (gọi thêm công cụ nếu cần cập nhật tiếp) "
                    f"hoặc đưa ra câu trả lời cuối cùng (Final Answer) đầy đủ, chính xác và có cảnh báo nếu sắp/đã vượt hạn mức."
                )

    # Nếu thoát vòng lặp mà chưa có FINAL_ANSWER (đạt max iterations)
    if not trace_logs or trace_logs[-1]["action_type"] != "FINAL_ANSWER":
        final_answer = format_observation_summary(last_tool_name, last_obs_data)
        print(f"🏁 [Final Answer - Fallback]: {final_answer}")
        trace_logs.append({
            "step": step + 1,
            "query": user_query,
            "action_type": "FINAL_ANSWER",
            "thought": "Đạt giới hạn vòng lặp suy luận, xuất kết quả tổng hợp.",
            "output": final_answer,
            "latency_ms": 10.0
        })

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🏫 VINUNI AI COURSE - DAY 03 LAB: CHATBOT VS REACT AGENT")
    print("💰 THEME: TRỢ LÝ QUẢN LÝ CHI TIÊU & CẢNH BÁO NGÂN SÁCH")
    print("==========================================================")

    provider = get_llm_provider()
    mcp_server = MCPPersonalFinanceServer()

    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")

    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Câu hỏi chung: 'Quy tắc quản lý tài chính 50/30/20 hoạt động như thế nào?'")
        print("   - Tra cứu ngân sách: 'Hãy kiểm tra giúp tôi ngân sách ăn uống trong tháng này còn lại bao nhiêu'")
        print("   - Ghi nhận chi tiêu & Cảnh báo: 'Tôi vừa ăn tối 350k ở Kichi Kichi, hãy kiểm tra ngân sách ăn uống còn lại và ghi nhận giao dịch này'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Người dùng hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        from tools import load_sample_finance_data
        load_sample_finance_data()
        print("📥 [DATABASE]: Đã nạp dữ liệu tài chính mẫu (Sample Data) để kiểm thử 5 Test Cases.")
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []

        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")

            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1

        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("   1. Chat trực tiếp liên tục: python src/app.py --interactive")
        print("   2. Chạy toàn bộ Test Cases: python src/app.py --all\n")

        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu ngân sách ăn uống) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")
