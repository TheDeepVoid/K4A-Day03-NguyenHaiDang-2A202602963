# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Nguyễn Hải Đăng  
> **Mã Sinh Viên / Mã Học viên:** 2A202602963  
> **Chủ đề Lựa chọn:** 2. Trợ lý Quản lý Chi tiêu & Cảnh báo Ngân sách Cá nhân (Personal Finance Agent)  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
|:--- |:---: |:--- |
| **1. Multi-step Reasoning** | **5** / 5 | Khi người dùng thông báo khoản chi tự nhiên ("Vừa ăn tối 350k ở Kichi Kichi"), Agent phải bóc tách ngữ nghĩa (ăn tối -> danh mục ăn uống, số tiền 350.000 VNĐ, địa điểm Kichi Kichi), xác định công cụ phù hợp, kiểm tra hạn mức còn lại, cập nhật cơ sở dữ liệu và tính toán tỷ lệ ngân sách để đưa ra cảnh báo kịp thời. |
| **2. Tool Interaction** | **5** / 5 | Hệ thống bắt buộc phải kết nối với MCP Server bên ngoài qua giao thức Model Context Protocol (MCP) để: (1) Tra cứu định mức và lịch sử chi tiêu thời gian thực (`check_budget_limits_and_history`), và (2) Ghi nhận giao dịch vào cơ sở dữ liệu Notion/Google Sheets/Airtable (`update_finance_database`). Không có tool, LLM không thể biết số dư thực tế hay lưu vết thu chi. |
| **3. Dynamic Decision** | **4** / 5 | Quyết định và phản hồi tiếp theo của Agent phụ thuộc động vào kết quả quan sát (Observation) trả về từ MCP Server. Nếu số dư an toàn, Agent thông báo xác nhận bình thường. Nếu số dư giảm dưới 15% hoặc bị âm, Agent tự động kích hoạt cảnh báo nguy cơ bội chi (`NEAR_LIMIT_WARNING` / `OVER_BUDGET_WARNING`). Nếu danh mục không tồn tại, Agent xử lý ngoại lệ `NOT_FOUND` và hướng dẫn danh mục chuẩn mà không bịa đặt dữ liệu (Anti-Hallucination). |
| **4. Long Horizon Goal** | **4** / 5 | Hệ thống phục vụ mục tiêu dài hạn xuyên suốt chu kỳ tài chính tháng: duy trì kỷ luật chi tiêu, kiểm soát ngân sách theo từng danh mục, ngăn ngừa tình trạng cạn kiệt tài chính cuối tháng và bảo toàn số tiền tiết kiệm mục tiêu của người dùng. |
| **TỔNG ĐIỂM AGENTIC FIT** | **18 / 20** | *Tổng điểm 18/20 (> 12/20): Bài toán cực kỳ phù hợp để triển khai hệ sinh thái Agentic System.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật (Google Gemini — Test Case TC04: Multi-step Reasoning & Cảnh báo Ngân sách):

```json
[
  {
    "step": 1,
    "query": "Tôi vừa ăn tối 350k ở Kichi Kichi, hãy kiểm tra ngân sách ăn uống còn lại và ghi nhận giao dịch này vào sổ thu chi giúp tôi nhé.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "update_finance_database",
    "arguments": {
      "amount": 350000,
      "category": "ăn uống",
      "description": "Ăn tối tại Kichi Kichi",
      "destination": "Notion"
    },
    "observation": {
      "status": "NEAR_LIMIT_WARNING",
      "action": "TRANSACTION_RECORDED",
      "destination": "Notion",
      "category": "ăn uống",
      "amount": 350000.0,
      "description": "Ăn tối tại Kichi Kichi",
      "monthly_limit": 5000000,
      "spent": 4550000.0,
      "remaining": 450000.0,
      "currency": "VND",
      "usage_percentage": "91.0%",
      "alert": "⚠️ CẢNH BÁO SẮP VƯỢT HẠN MỨC: Danh mục 'ăn uống' đã sử dụng 91.0%. Số dư còn lại chỉ còn 450,000 VNĐ."
    },
    "latency_ms": 1914.49
  },
  {
    "step": 2,
    "query": "Tôi vừa ăn tối 350k ở Kichi Kichi, hãy kiểm tra ngân sách ăn uống còn lại và ghi nhận giao dịch này vào sổ thu chi giúp tôi nhé.",
    "action_type": "FINAL_ANSWER",
    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Tôi đã ghi nhận giao dịch chi tiêu của bạn vào cơ sở dữ liệu Notion thành công! \n\nDưới đây là thông tin chi tiết và tình hình ngân sách danh mục **Ăn uống** của bạn trong tháng này:\n\n- **Giao dịch vừa ghi nhận:** Ăn tối tại Kichi Kichi – **350,000 VNĐ**\n- **Hạn mức hàng tháng:** 5,000,000 VNĐ\n- **Tổng đã chi tiêu:** 4,550,000 VNĐ (đạt **91.0%** hạn mức)\n- **Số dư còn lại:** **450,000 VNĐ**\n\n⚠️ **CẢNH BÁO SẮP VƯỢT HẠN MỨC:** Danh mục **'ăn uống'** của bạn đã sử dụng 91.0% hạn mức. Số dư còn lại chỉ còn **450,000 VNĐ**, bạn hãy cân nhắc kỹ các khoản chi tiêu ăn uống trong phần còn lại của tháng để tránh vượt ngân sách nhé!",
    "latency_ms": 1632.34
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 4 lượt (TC02: `check_budget_limits_and_history`, TC03: `update_finance_database`, TC04: `update_finance_database`, TC05: `check_budget_limits_and_history`). TC01 là câu hỏi lý thuyết được Agent nhận diện trả lời trực tiếp mà không cần gọi Tool.
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
