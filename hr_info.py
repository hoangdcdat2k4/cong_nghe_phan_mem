import streamlit as st
from pymongo import MongoClient
from datetime import datetime, date
import time
import pandas as pd
import plotly.express as px

# Kết nối MongoDB
client = MongoClient("mongodb+srv://tunnguyen2910:Z8UUBbXK20o37JtO@cluster0.xvngw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["hr_system"]

# Collections
employees = db["employees"]
departments = db["departments"]
attendance = db["attendance"]
leaves = db["leaves"]
reviews = db["reviews"]

# Cấu hình trang
st.set_page_config(
    page_title="HR Management System",
    page_icon="🏢",
    layout="wide"
)

# CSS tùy chỉnh
st.markdown("""
    <style>
    .main {
        background-color: #F5F5F5;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    .css-1aumxhk {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# Xác thực đơn giản
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Đăng nhập hệ thống HR")
    username = st.text_input("Tên đăng nhập")
    password = st.text_input("Mật khẩu", type="password")
    
    if st.button("Đăng nhập"):
        if username == "admin" and password == "admin123":
            st.session_state.authenticated = True
            st.success("Đăng nhập thành công!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Thông tin đăng nhập không chính xác")
    st.stop()

# Helper functions
def get_departments():
    return list(departments.find())

def get_employees():
    return list(employees.find())

# Giao diện chính
st.title("🏢 Hệ thống Quản lý Nhân sự Thế hệ mới")
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Tổng quan",
    "👥 Nhân viên",
    "📊 Phòng ban",
    "🕒 Chấm công",
    "📝 Quản lý nghỉ phép",
    "📈 Báo cáo"
])

with tab1:  # Dashboard
    st.subheader("Bảng điều khiển tổng quan")
    col1, col2, col3 = st.columns(3)
    
    # Thống kê
    with col1:
        st.metric("Tổng nhân viên", employees.count_documents({}))
    with col2:
        st.metric("Tổng phòng ban", departments.count_documents({}))
    with col3:
        st.metric("Nghỉ phép đang chờ", leaves.count_documents({"status": "pending"}))
    
    # Biểu đồ
    st.subheader("Phân tích nhân sự")
    df = pd.DataFrame(list(employees.find()))
    if not df.empty:
        fig = px.pie(df, names='position', title='Phân bố theo chức vụ')
        st.plotly_chart(fig)

with tab2:  # Quản lý nhân viên
    st.subheader("Quản lý hồ sơ nhân viên")
    
    with st.expander("Thêm nhân viên mới"):
        with st.form("add_employee"):
            name = st.text_input("Họ tên")
            position = st.selectbox("Chức vụ", ["Nhân viên", "Trưởng phòng", "Giám đốc"])
            salary = st.number_input("Lương", min_value=0)
            department = st.selectbox("Phòng ban", [d["name"] for d in get_departments()])
            email = st.text_input("Email")
            phone = st.text_input("Số điện thoại")
            
            if st.form_submit_button("Thêm nhân viên"):
                department_id = departments.find_one({"name": department})["_id"]
                employee_data = {
                    "name": name,
                    "position": position,
                    "salary": salary,
                    "department_id": department_id,
                    "email": email,
                    "phone": phone,
                    "hire_date": datetime.now().strftime("%Y-%m-%d")
                }
                employees.insert_one(employee_data)
                st.success("Đã thêm nhân viên thành công!")

    with st.expander("Danh sách nhân viên"):
        search_query = st.text_input("Tìm kiếm nhân viên")
        if search_query:
            results = employees.find({"name": {"$regex": search_query, "$options": "i"}})
        else:
            results = get_employees()
        
        for emp in results:
            dept = departments.find_one({"_id": emp["department_id"]})
            with st.container():
                col1, col2, col3 = st.columns([2,3,2])
                with col1:
                    st.write(f"**{emp['name']}**")
                    st.caption(f"📧 {emp['email']}")
                with col2:
                    st.write(f"📌 {emp['position']}")
                    st.write(f"🏢 {dept['name'] if dept else 'Chưa phân bộ phận'}")
                with col3:
                    st.write(f"💰 {emp['salary']:,.0f} VND")
                st.divider()

with tab3:  # Quản lý phòng ban
    st.subheader("Quản lý phòng ban")
    
    with st.expander("Thêm phòng ban mới"):
        with st.form("add_department"):
            name = st.text_input("Tên phòng ban")
            manager = st.selectbox("Trưởng phòng", [e["name"] for e in get_employees()])
            budget = st.number_input("Ngân sách", min_value=0)
            
            if st.form_submit_button("Thêm phòng ban"):
                manager_id = employees.find_one({"name": manager})["_id"]
                department_data = {
                    "name": name,
                    "manager_id": manager_id,
                    "budget": budget,
                    "created_at": datetime.now()
                }
                departments.insert_one(department_data)
                st.success("Đã thêm phòng ban thành công!")

    # Hiển thị danh sách phòng ban
    for dept in get_departments():
        manager = employees.find_one({"_id": dept["manager_id"]})
        with st.container():
            col1, col2 = st.columns([3,2])
            with col1:
                st.write(f"### {dept['name']}")
                st.write(f"💼 Trưởng phòng: {manager['name'] if manager else 'Chưa bổ nhiệm'}")
            with col2:
                st.write(f"🏦 Ngân sách: {dept['budget']:,.0f} VND")
                st.progress(min(dept['budget'] / 100000000, 1))
            st.divider()

with tab4:  # Chấm công
    st.subheader("Hệ thống chấm công")
    
    emp_name = st.selectbox("Chọn nhân viên", [e["name"] for e in get_employees()])
    today = date.today().strftime("%Y-%m-%d")
    
    if 'last_action' not in st.session_state:
        st.session_state.last_action = None
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 Check-in"):
            employees.update_one(
                {"name": emp_name},
                {"$push": {"attendance": {"date": today, "time_in": datetime.now().strftime("%H:%M")}}}
            )
            st.session_state.last_action = "checkin"
            st.success(f"Đã check-in lúc {datetime.now().strftime('%H:%M')}")
    
    with col2:
        if st.button("🔴 Check-out"):
            employees.update_one(
                {"name": emp_name},
                {"$push": {"attendance": {"date": today, "time_out": datetime.now().strftime("%H:%M")}}}
            )
            st.session_state.last_action = "checkout"
            st.success(f"Đã check-out lúc {datetime.now().strftime('%H:%M')}")
    
    st.subheader("Lịch sử chấm công")
    emp = employees.find_one({"name": emp_name})
    if emp and "attendance" in emp:
        df = pd.DataFrame(emp["attendance"])
        st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)

with tab5:  # Quản lý nghỉ phép
    st.subheader("Quản lý đơn xin nghỉ phép")
    
    with st.expander("🏖️ Nộp đơn xin nghỉ"):
        with st.form("leave_form"):
            emp_name = st.selectbox("Nhân viên", [e["name"] for e in get_employees()])
            start_date = st.date_input("Ngày bắt đầu")
            end_date = st.date_input("Ngày kết thúc")
            reason = st.text_area("Lý do")
            
            if st.form_submit_button("Gửi đơn"):
                emp_id = employees.find_one({"name": emp_name})["_id"]
                leave_data = {
                    "employee_id": emp_id,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "reason": reason,
                    "status": "pending",
                    "applied_at": datetime.now()
                }
                leaves.insert_one(leave_data)
                st.success("Đã gửi đơn thành công!")
    
    st.subheader("Danh sách đơn nghỉ phép")
    for leave in leaves.find():
        emp = employees.find_one({"_id": leave["employee_id"]})
        status_color = {
            "pending": "🟡",
            "approved": "🟢",
            "rejected": "🔴"
        }.get(leave["status"], "⚪")
        
        with st.container():
            col1, col2 = st.columns([1,4])
            with col1:
                st.write(f"### {status_color} {leave['status'].upper()}")
            with col2:
                st.write(f"**{emp['name']}**")
                st.write(f"📅 {leave['start_date']} → {leave['end_date']}")
                st.write(f"📝 {leave['reason']}")
                
                if leave["status"] == "pending":
                    if st.button("Duyệt", key=f"approve_{leave['_id']}"):
                        leaves.update_one({"_id": leave["_id"]}, {"$set": {"status": "approved"}})
                        st.rerun()
                    st.button("Từ chối", key=f"reject_{leave['_id']}")

with tab6:  # Báo cáo
    st.subheader("Báo cáo và phân tích")
    
    # Phân tích lương
    st.write("### Phân bố lương")
    df = pd.DataFrame(list(employees.find()))
    if not df.empty:
        fig = px.box(df, y="salary", points="all")
        st.plotly_chart(fig)
    
    # Thống kê phòng ban
    st.write("### Thống kê phòng ban")
    dept_data = []
    for dept in get_departments():
        count = employees.count_documents({"department_id": dept["_id"]})
        dept_data.append({
            "Phòng ban": dept["name"],
            "Số nhân viên": count,
            "Ngân sách": dept["budget"]
        })
    df_dept = pd.DataFrame(dept_data)
    st.dataframe(df_dept, use_container_width=True)