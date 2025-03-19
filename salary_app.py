import streamlit as st
import pandas as pd
import json
import os
from fpdf import FPDF

# Định nghĩa Employee
class Employee:
    def __init__(self, id, name, region, base_salary, bonus, dependents, allowance, membership_card):
        self.id = id
        self.name = name
        self.region = region
        self.base_salary = base_salary
        self.bonus = bonus
        self.dependents = dependents
        self.allowance = allowance
        self.membership_card = membership_card
        self.insurance = self.calculate_insurance()
        self.tax = self.calculate_tax()
        self.net_salary = self.calculate_net_salary()

    def calculate_insurance(self):
        return self.base_salary * 0.105

    def calculate_tax(self):
        MIN_SALARY = [4680000, 4160000, 3640000, 3250000]
        if self.base_salary < MIN_SALARY[self.region - 1]:
            st.warning(f"Cảnh báo: Lương thấp hơn mức tối thiểu vùng {self.region}!")
        taxable_income = self.base_salary + self.bonus - 11000000 - (self.dependents * 4400000)
        if taxable_income <= 0:
            return 0
        tax_brackets = [
            (5000000, 0.05, 0), (10000000, 0.1, 250000), (18000000, 0.15, 750000),
            (32000000, 0.2, 1650000), (52000000, 0.25, 3250000), (80000000, 0.3, 5850000)
        ]
        for limit, rate, deduction in tax_brackets:
            if taxable_income <= limit:
                return taxable_income * rate - deduction
        return taxable_income * 0.35 - 9850000

    def calculate_net_salary(self):
        return self.base_salary + self.bonus - self.tax - self.insurance + self.allowance

# Định nghĩa file JSON để lưu dữ liệu
DATA_FILE = "employees.json"

def save_data(employees):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([vars(e) for e in employees], f, ensure_ascii=False, indent=4)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [
                Employee(
                    id=row["id"],
                    name=row["name"],
                    region=row["region"],
                    base_salary=row["base_salary"],
                    bonus=row["bonus"],
                    dependents=row["dependents"],
                    allowance=row["allowance"],
                    membership_card=row["membership_card"]
                )
                for row in data
            ]
    return []

# Hàm xuất phiếu lương PDF
def generate_salary_report(employees):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", "DejaVuSans-Bold.ttf", uni=True)
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(200, 10, "BÁO CÁO LƯƠNG NHÂN VIÊN", ln=True, align="C")

    for emp in employees:
        pdf.cell(200, 10, f"ID: {emp.id}", ln=True)
        pdf.cell(200, 10, f"Tên: {emp.name}", ln=True)
        pdf.cell(200, 10, f"Lương thực lĩnh: {emp.net_salary:,.0f} VND", ln=True)
        pdf.cell(200, 10, "-" * 50, ln=True)

    pdf_path = "salary_report.pdf"
    pdf.output(pdf_path, "F")
    return pdf_path

# Giao diện Streamlit
st.title("Hệ thống tính lương và phúc lợi")

# Tải dữ liệu nhân viên
employees = load_data()

# Form thêm nhân viên
st.sidebar.header("Thêm nhân viên")
with st.sidebar.form("add_employee_form"):
    id = st.number_input("ID", min_value=1, step=1)
    name = st.text_input("Tên nhân viên")
    region = st.selectbox("Vùng", [1, 2, 3, 4])
    base_salary = st.number_input("Lương cơ bản", min_value=0.0)
    bonus = st.number_input("Thưởng", min_value=0.0)
    dependents = st.number_input("Số người phụ thuộc", min_value=0, step=1)
    allowance = st.number_input("Trợ cấp", min_value=0.0)
    membership_card = st.text_input("Loại thẻ thành viên")

    if st.form_submit_button("Thêm nhân viên"):
        emp = Employee(id, name, region, base_salary, bonus, dependents, allowance, membership_card)
        employees.append(emp)
        save_data(employees)
        st.success("Đã thêm nhân viên!")

# Hiển thị danh sách nhân viên
st.header("Danh sách nhân viên")
if employees:
    data = []
    for emp in employees:
        data.append([
            emp.id, emp.name, emp.region, emp.base_salary, emp.bonus, emp.dependents,
            emp.allowance, emp.membership_card, emp.insurance, emp.tax, emp.net_salary
        ])
    df = pd.DataFrame(data, columns=[
        "ID", "Tên", "Vùng", "Lương cơ bản", "Thưởng", "Số người phụ thuộc",
        "Trợ cấp", "Thẻ thành viên", "Bảo hiểm", "Thuế", "Lương thực lĩnh"
    ])
    st.write(df)

    # Xóa nhân viên
    st.subheader("Xóa nhân viên")
    delete_id = st.number_input("Nhập ID nhân viên cần xóa", min_value=1, step=1)
    if st.button("Xóa nhân viên"):
        employees = [e for e in employees if e.id != delete_id]
        save_data(employees)
        st.success("Nhân viên đã được xóa!")
        st.experimental_rerun()

else:
    st.info("Chưa có nhân viên nào!")

# Xuất báo cáo lương
if st.button("Tạo báo cáo lương"):
    pdf_path = generate_salary_report(employees)
    st.success("Đã tạo báo cáo lương!")
    st.download_button("Tải báo cáo lương", open(pdf_path, "rb"), file_name="salary_report.pdf")
