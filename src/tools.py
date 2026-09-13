"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
Hỗ trợ chủ đề Trợ lý Quản lý Chi tiêu & Cảnh báo Ngân sách Cá nhân (Personal Finance Agent) và Học vụ VinUni.
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2 & FINANCE AGENT)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu học vụ sinh viên
    {
        "name": "academic_query",
        "description": "Tra cứu hồ sơ và thông tin học vụ của sinh viên VinUni bằng mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },

    # Tool 2: Đặt lịch hẹn học vụ (TODO 1.2 hoàn thiện)
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần đặt lịch (ví dụ: 'SV2026001')"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian hẹn (ví dụ: '14:00 15/09/2026')"
                },
                "advisor_name": {
                    "type": "string",
                    "description": "Tên cố vấn học tập cần gặp (ví dụ: 'PGS.TS Nguyễn Văn A')"
                }
            },
            "required": ["student_id", "datetime_str"]
        }
    },

    # Tool 3: Tra cứu định mức ngân sách & lịch sử chi tiêu (Personal Finance Agent)
    {
        "name": "check_budget_limits_and_history",
        "description": "Tra cứu số dư định mức hàng tháng, hạn mức chi tiêu và lịch sử giao dịch gần đây cho từng danh mục chi tiêu như ăn uống (dining), giải trí (entertainment), mua sắm (shopping), di chuyển (transport), học tập (education).",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Danh mục chi tiêu cần kiểm tra (ví dụ: 'ăn uống', 'giải trí', 'mua sắm', 'di chuyển', 'học tập', hoặc 'tất cả')"
                },
                "month": {
                    "type": "string",
                    "description": "Tháng cần tra cứu theo định dạng YYYY-MM (ví dụ: '2026-09'). Mặc định tháng hiện tại nếu không điền."
                }
            },
            "required": ["category"]
        }
    },

    # Tool 4: Ghi nhận giao dịch chi tiêu mới và cảnh báo hạn mức (Personal Finance Agent)
    {
        "name": "update_finance_database",
        "description": "Ghi nhận giao dịch chi tiêu mới vào cơ sở dữ liệu tài chính (Notion/Google Sheets/Airtable), tự động cập nhật số dư ngân sách còn lại và đưa ra cảnh báo nếu chi tiêu sắp vượt hoặc đã vượt hạn mức cho phép.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Danh mục chi tiêu của giao dịch (ví dụ: 'ăn uống', 'giải trí', 'mua sắm', 'di chuyển', 'học tập')"
                },
                "amount": {
                    "type": "number",
                    "description": "Số tiền chi tiêu trong giao dịch tính theo VNĐ (ví dụ: 350000)"
                },
                "description": {
                    "type": "string",
                    "description": "Nội dung chi tiêu chi tiết hoặc tên quán, dịch vụ (ví dụ: 'Ăn tối tại Kichi Kichi')"
                },
                "destination": {
                    "type": "string",
                    "description": "Hệ thống cơ sở dữ liệu đích để đồng bộ: 'Notion', 'Google Sheets', hoặc 'Airtable' (mặc định: 'Notion')"
                }
            },
            "required": ["category", "amount", "description"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "SV2026001": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
    },
    "SV2026002": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.60,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
    }
}

FINANCE_DATABASE = {
    "categories": {
        "ăn uống": {
            "monthly_limit": 5000000,
            "spent": 4200000,
            "remaining": 800000,
            "currency": "VND",
            "recent_transactions": [
                {"date": "2026-09-02", "amount": 120000, "description": "Cơm trưa văn phòng"},
                {"date": "2026-09-05", "amount": 250000, "description": "Cafe Highlands cùng bạn"},
                {"date": "2026-09-10", "amount": 480000, "description": "Pizza 4P's"}
            ]
        },
        "giải trí": {
            "monthly_limit": 2000000,
            "spent": 1400000,
            "remaining": 600000,
            "currency": "VND",
            "recent_transactions": [
                {"date": "2026-09-03", "amount": 220000, "description": "Vé xem phim CGV"},
                {"date": "2026-09-08", "amount": 500000, "description": "Boardgame & nước"}
            ]
        },
        "mua sắm": {
            "monthly_limit": 3000000,
            "spent": 2900000,
            "remaining": 100000,
            "currency": "VND",
            "recent_transactions": [
                {"date": "2026-09-04", "amount": 1500000, "description": "Quần áo Uniqlo"},
                {"date": "2026-09-09", "amount": 1400000, "description": "Giày thể thao"}
            ]
        },
        "di chuyển": {
            "monthly_limit": 1500000,
            "spent": 650000,
            "remaining": 850000,
            "currency": "VND",
            "recent_transactions": [
                {"date": "2026-09-01", "amount": 300000, "description": "Vé tháng VinBus"},
                {"date": "2026-09-07", "amount": 150000, "description": "GrabBike"}
            ]
        },
        "học tập": {
            "monthly_limit": 2000000,
            "spent": 500000,
            "remaining": 1500000,
            "currency": "VND",
            "recent_transactions": [
                {"date": "2026-09-06", "amount": 500000, "description": "Sách AI & Prompt Engineering"}
            ]
        }
    }
}


def _normalize_category(cat: str) -> str:
    """Chuẩn hóa tên danh mục chi tiêu"""
    c = cat.strip().lower()
    mapping = {
        "an uong": "ăn uống",
        "ăn uống": "ăn uống",
        "an_uong": "ăn uống",
        "dining": "ăn uống",
        "food": "ăn uống",
        "restaurant": "ăn uống",
        "giai tri": "giải trí",
        "giải trí": "giải trí",
        "entertainment": "giải trí",
        "mua sam": "mua sắm",
        "mua sắm": "mua sắm",
        "shopping": "mua sắm",
        "di chuyen": "di chuyển",
        "di chuyển": "di chuyển",
        "transport": "di chuyển",
        "hoc tap": "học tập",
        "học tập": "học tập",
        "education": "học tập"
    }
    return mapping.get(c, c)


def execute_academic_query(student_id: str) -> str:
    """Thực thi tra cứu học vụ theo mã sinh viên"""
    student = MOCK_DATABASE.get(student_id.strip().upper())
    if student:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": student_id,
            "data": student
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)


def execute_schedule_appointment(student_id: str, datetime_str: str, advisor_name: str = "PGS.TS Nguyễn Văn A") -> str:
    """Thực thi đặt lịch hẹn tư vấn học vụ"""
    return json.dumps({
        "status": "SUCCESS",
        "message": f"Đã đặt lịch hẹn tư vấn học vụ thành công cho sinh viên {student_id} với {advisor_name} vào lúc {datetime_str}.",
        "appointment_details": {
            "student_id": student_id,
            "datetime": datetime_str,
            "advisor": advisor_name,
            "status": "CONFIRMED"
        }
    }, ensure_ascii=False)


def execute_check_budget_limits_and_history(category: str, month: str = "2026-09") -> str:
    """Tra cứu hạn mức, số dư và lịch sử chi tiêu cá nhân"""
    cat_key = _normalize_category(category)
    categories = FINANCE_DATABASE["categories"]
    
    if cat_key == "tất cả" or cat_key == "all":
        overview = {}
        for k, v in categories.items():
            overview[k] = {
                "monthly_limit": v["monthly_limit"],
                "spent": v["spent"],
                "remaining": v["remaining"],
                "usage_percentage": f"{(v['spent'] / v['monthly_limit'] * 100):.1f}%"
            }
        return json.dumps({
            "status": "SUCCESS",
            "month": month,
            "categories": overview
        }, ensure_ascii=False)

    cat_data = categories.get(cat_key)
    if not cat_data:
        valid_cats = ", ".join(categories.keys())
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy danh mục ngân sách '{category}'. Các danh mục hiện có: {valid_cats}."
        }, ensure_ascii=False)

    limit = cat_data["monthly_limit"]
    spent = cat_data["spent"]
    remaining = cat_data["remaining"]
    usage_pct = (spent / limit) * 100

    alert = ""
    if remaining < 0:
        alert = f"⚠️ CẢNH BÁO NGUY HIỂM: Đã bội chi {-remaining:,.0f} VNĐ!"
    elif usage_pct >= 80:
        alert = f"⚠️ CẢNH BÁO: Đã dùng {usage_pct:.1f}% ngân sách! Chỉ còn {remaining:,.0f} VNĐ."
    else:
        alert = f"✅ Ngân sách an toàn, còn lại {remaining:,.0f} VNĐ ({100 - usage_pct:.1f}%)."

    return json.dumps({
        "status": "SUCCESS",
        "category": cat_key,
        "month": month,
        "monthly_limit": limit,
        "spent": spent,
        "remaining": remaining,
        "currency": cat_data["currency"],
        "usage_percentage": f"{usage_pct:.1f}%",
        "alert": alert,
        "recent_transactions": cat_data.get("recent_transactions", [])
    }, ensure_ascii=False)


def execute_update_finance_database(category: str, amount: float, description: str, destination: str = "Notion") -> str:
    """Ghi nhận giao dịch chi tiêu mới và cập nhật số dư ngân sách"""
    cat_key = _normalize_category(category)
    categories = FINANCE_DATABASE["categories"]

    if cat_key not in categories:
        # Tự động tạo danh mục mới với hạn mức mặc định 3,000,000 VND
        categories[cat_key] = {
            "monthly_limit": 3000000,
            "spent": 0,
            "remaining": 3000000,
            "currency": "VND",
            "recent_transactions": []
        }

    cat_data = categories[cat_key]
    amount_num = float(amount)
    cat_data["spent"] += amount_num
    cat_data["remaining"] -= amount_num
    
    cat_data["recent_transactions"].insert(0, {
        "date": "2026-09-13",
        "amount": amount_num,
        "description": description,
        "destination": destination
    })

    limit = cat_data["monthly_limit"]
    spent = cat_data["spent"]
    remaining = cat_data["remaining"]
    usage_pct = (spent / limit) * 100

    if remaining < 0:
        status = "OVER_BUDGET_WARNING"
        alert = f"🚨 CẢNH BÁO VƯỢT HẠN MỨC: Danh mục '{cat_key}' đã vượt ngân sách {-remaining:,.0f} VNĐ! Hãy tạm dừng chi tiêu danh mục này."
    elif usage_pct >= 85:
        status = "NEAR_LIMIT_WARNING"
        alert = f"⚠️ CẢNH BÁO SẮP VƯỢT HẠN MỨC: Danh mục '{cat_key}' đã sử dụng {usage_pct:.1f}%. Số dư còn lại chỉ còn {remaining:,.0f} VNĐ."
    else:
        status = "SUCCESS"
        alert = f"✅ Ngân sách danh mục '{cat_key}' vẫn trong tầm kiểm soát ({usage_pct:.1f}% đã dùng). Còn lại {remaining:,.0f} VNĐ."

    return json.dumps({
        "status": status,
        "action": "TRANSACTION_RECORDED",
        "destination": destination,
        "category": cat_key,
        "amount": amount_num,
        "description": description,
        "monthly_limit": limit,
        "spent": spent,
        "remaining": remaining,
        "currency": "VND",
        "usage_percentage": f"{usage_pct:.1f}%",
        "alert": alert
    }, ensure_ascii=False)


# Tool Dispatch Table
TOOL_DISPATCH_MAP = {
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment,
    "check_budget_limits_and_history": execute_check_budget_limits_and_history,
    "check_budget_limits": execute_check_budget_limits_and_history,
    "check_budget": execute_check_budget_limits_and_history,
    "update_finance_database": execute_update_finance_database,
    "update_finance": execute_update_finance_database,
    "record_expense": execute_update_finance_database
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Điều phối và thực thi các Tool đã đăng ký trên hệ thống"""
    handler = TOOL_DISPATCH_MAP.get(tool_name)
    if handler:
        try:
            return handler(**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
