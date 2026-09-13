"""
🌐 PERSONAL FINANCE AGENT WEB SERVER
Khởi tạo HTTP Server phục vụ giao diện người dùng (UI) và API tương tác thời gian thực với ReAct Agent.
"""

import copy
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import run_react_agent, save_waterfall_trace
from mcp_server import MCPPersonalFinanceServer
from providers import get_llm_provider
from tools import FINANCE_DATABASE, load_sample_finance_data, reset_to_zero_finance_data

provider = get_llm_provider()
mcp_server = MCPPersonalFinanceServer()


class FinanceAgentHTTPHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type="application/json", status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(status=204)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            # Phục vụ file HTML giao diện
            base_dir = os.path.dirname(os.path.abspath(__file__))
            html_path = os.path.join(base_dir, "web", "index.html")
            try:
                with open(html_path, "rb") as f:
                    content = f.read()
                self._set_headers("text/html; charset=utf-8")
                self.wfile.write(content)
            except Exception as e:
                self._set_headers("text/plain", 500)
                self.wfile.write(f"Lỗi tải giao diện: {str(e)}".encode("utf-8"))

        elif path == "/api/budget":
            # API lấy danh sách ngân sách hiện tại
            categories = FINANCE_DATABASE.get("categories", {})
            self._set_headers()
            self.wfile.write(json.dumps(categories, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/logs":
            # API lấy lịch sử waterfall trace logs
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            trace_path = os.path.join(base_dir, "docs", "trace_waterfall.json")
            logs = []
            if os.path.exists(trace_path):
                try:
                    with open(trace_path, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                except Exception:
                    logs = []
            self._set_headers()
            self.wfile.write(json.dumps(logs, ensure_ascii=False).encode("utf-8"))

        else:
            self._set_headers("text/plain", 404)
            self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == "/api/chat":
            user_message = payload.get("message", "").strip()
            if not user_message:
                self._set_headers(status=400)
                self.wfile.write(json.dumps({"error": "Nội dung tin nhắn không được để trống"}).encode("utf-8"))
                return

            print(f"\n🌐 [WEB REQUEST]: '{user_message}'")
            # Thực thi ReAct Agent Loop
            trace_logs = run_react_agent(user_message, provider, mcp_server)
            save_waterfall_trace(trace_logs)

            categories = FINANCE_DATABASE.get("categories", {})
            response_data = {
                "status": "success",
                "traces": trace_logs,
                "budget": categories
            }

            self._set_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/sample":
            # Nạp dữ liệu mẫu ban đầu
            updated_budget = load_sample_finance_data()
            print("📥 [WEB REQUEST]: Đã nạp dữ liệu mẫu (Sample Data) vào cơ sở dữ liệu.")

            self._set_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Đã nạp thành công dữ liệu tài chính mẫu!",
                "budget": updated_budget
            }, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/reset":
            # Khôi phục database về trạng thái mặc định: tất cả dữ liệu là 0
            updated_budget = reset_to_zero_finance_data()
            print("🔄 [WEB REQUEST]: Đã reset cơ sở dữ liệu ngân sách về mặc định (0).")

            self._set_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Đã khôi phục dữ liệu về trạng thái mặc định (0)!",
                "budget": updated_budget
            }, ensure_ascii=False).encode("utf-8"))

        else:
            self._set_headers("text/plain", 404)
            self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        # Thu gọn log HTTP để tránh rối terminal
        sys.stderr.write(f"📡 [HTTP] {self.address_string()} - {args[0]}\n")


def start_server(port=8000):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, FinanceAgentHTTPHandler)
    print("==========================================================")
    print("🚀 PERSONAL FINANCE AGENT - WEB UI SERVER")
    print("==========================================================")
    print(f"🔗 Máy chủ đang chạy tại: http://localhost:{port}")
    print(f"🌐 Giao diện Web: http://localhost:{port}/index.html")
    print(f"⚡ LLM Provider: {provider.__class__.__name__}")
    print(f"🔌 MCP Server: {mcp_server.server_name}")
    print("==========================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Đang dừng máy chủ Web...")
        httpd.server_close()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    start_server(port)
