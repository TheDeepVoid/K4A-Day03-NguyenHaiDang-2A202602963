"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng kiến trúc MCP Server (Client-Server Architecture) cung cấp công cụ chuẩn hóa.
Hỗ trợ cả Personal Finance Server và Academic Server theo chuẩn giao thức MCP JSON-RPC 2.0.
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class MCPAcademicServer:
    """
    Giả lập MCP Server tuân thủ chuẩn giao thức Model Context Protocol
    """
    def __init__(self, server_name: str = "vinuni-academic-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"

    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách các Tools chuẩn giao thức MCP"""
        return TOOLS_SCHEMA

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        [TASK 2.1] HỌC VIÊN HOÀN THIỆN HÀM THỰC THI TOOL TRÊN MCP SERVER
        Thực thi request gọi Tool theo chuẩn MCP JSON-RPC 2.0
        """
        # 1. Điều phối thực thi Tool qua dispatch_tool_call
        raw_result = dispatch_tool_call(tool_name, arguments)

        # 2. Chuyển đổi kết quả JSON string thành Python Dictionary
        try:
            content = json.loads(raw_result)
        except Exception:
            content = {"raw": raw_result}

        # 3. Đóng gói phản hồi chuẩn MCP JSON-RPC 2.0
        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content
        }


# Alias cho chủ đề Quản lý Chi tiêu Cá nhân
class MCPPersonalFinanceServer(MCPAcademicServer):
    def __init__(self, server_name: str = "personal-finance-mcp-server"):
        super().__init__(server_name=server_name)


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (personal-finance & academic)")
    print("==========================================================")
    server = MCPAcademicServer()
    tools = server.list_tools()

    print(f"✅ Khởi tạo thành công MCP Server: {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng Tools công bố: {len(tools)}")

    # Kiểm tra trạng thái TODO 1.2 (Tool Schema)
    has_schedule_props = any(t["name"] == "schedule_appointment" and t["parameters"].get("properties") for t in tools)
    if not has_schedule_props:
        print("⏳ [TODO 1.2]: Tool 'schedule_appointment' chưa được định nghĩa properties trong 'src/tools.py'.")
    else:
        print("✅ [TODO 1.2]: Tool 'schedule_appointment' đã có schema đầy đủ.")

    # Kiểm tra trạng thái TODO 2.1 (call_tool)
    test_call = server.call_tool("academic_query", {"student_id": "SV2026001"})
    if not test_call or not test_call.get("result"):
        print("⏳ [TODO 2.1]: Hàm call_tool() đang trả về rỗng. Học viên hãy hoàn thiện TODO 2.1 trong 'src/mcp_server.py'!")
    else:
        print(f"✅ [TODO 2.1]: Test dispatch tool 'academic_query' thành công:")
        print(f"   Response JSON-RPC: {json.dumps(test_call, ensure_ascii=False)}")

    # Kiểm tra thử nghiệm Finance Tools
    finance_test = server.call_tool("check_budget_limits_and_history", {"category": "ăn uống"})
    print(f"✅ [FINANCE TOOL]: Test 'check_budget_limits_and_history' thành công:")
    print(f"   Response JSON-RPC: {json.dumps(finance_test, ensure_ascii=False)}")
