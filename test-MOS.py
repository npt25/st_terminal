import streamlit as st
import pandas as pd
import os
from vnstock3 import Stock  # Đây là ví dụ, bạn cần sửa lại import nếu khác

# Đường dẫn đến thư mục chứa dữ liệu đã giải nén
extraction_directory = '/mnt/data/vnstock3_extracted/vnstock3/'

# Chức năng của ứng dụng
st.title('Ứng dụng Phân Tích Tài Chính Chứng Khoán')
st.sidebar.header('Chọn Mã Chứng Khoán')

# Người dùng chọn mã chứng khoán
stock_symbols = ['VCB', 'VNM', 'HPG', 'FPT']  # Bạn có thể cập nhật danh sách này
selected_stock = st.sidebar.selectbox('Chọn mã chứng khoán:', stock_symbols)

# Người dùng nhập số năm để phân tích
num_years = st.sidebar.slider('Số năm phân tích:', min_value=1, max_value=10, value=5)

# Lấy dữ liệu từ thư viện vnstock3
stock = Stock(selected_stock)

try:
    # Lấy các chỉ số từ bảng cân đối kế toán
    balance_sheet = stock.finance.balance_sheet(period='year', lang='vi', dropna=True)
    balance_sheet_filtered = balance_sheet[balance_sheet['Năm'] >= (2023 - num_years + 1)].copy()
    if 'Năm' in balance_sheet_filtered.columns and 'VỐN CHỦ SỞ HỮU (Tỷ đồng)' in balance_sheet_filtered.columns and 'NỢ PHẢI TRẢ (Tỷ đồng)' in balance_sheet_filtered.columns:
        balance_sheet_filtered = balance_sheet_filtered[['Năm', 'VỐN CHỦ SỞ HỮU (Tỷ đồng)', 'NỢ PHẢI TRẢ (Tỷ đồng)']]
        if 'Nợ dài hạn (Tỷ đồng)' in balance_sheet.columns:
            balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'] = balance_sheet['Nợ dài hạn (Tỷ đồng)'].copy()
        else:
            balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'] = 0
    else:
        st.error("Thiếu cột cần thiết trong bảng cân đối kế toán")

    # Lấy các chỉ số từ báo cáo lãi lỗ
    income_statement = stock.finance.income_statement(period='year', lang='vi', dropna=True)
    income_statement_filtered = income_statement[income_statement['Năm'] >= (2023 - num_years + 1)].copy()
    if 'Năm' in income_statement_filtered.columns and 'Doanh thu (Tỷ đồng)' in income_statement_filtered.columns and 'Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)' in income_statement_filtered.columns:
        income_statement_filtered = income_statement_filtered[['Năm', 'Doanh thu (Tỷ đồng)', 'Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)']]
    else:
        st.error("Thiếu cột cần thiết trong báo cáo lãi lỗ")

    # Lấy các chỉ số từ báo cáo lưu chuyển tiền tệ
    cash_flow = stock.finance.cash_flow(period='year', dropna=True)
    cash_flow_filtered = cash_flow[cash_flow['yearReport'] >= (2023 - num_years + 1)].copy()
    if 'yearReport' in cash_flow_filtered.columns and 'Net cash inflows/outflows from operating activities' in cash_flow_filtered.columns:
        cash_flow_filtered = cash_flow_filtered[['yearReport', 'Net cash inflows/outflows from operating activities']]
        cash_flow_filtered.rename(columns={'yearReport': 'Năm'}, inplace=True)
    else:
        st.error("Thiếu cột cần thiết trong báo cáo lưu chuyển tiền tệ")

    # Tính toán và hiển thị các chỉ số tài chính
    st.subheader(f'Kết Quả Phân Tích Cho Mã Chứng Khoán: {selected_stock}')
    st.write('### Bảng Cân Đối Kế Toán')
    st.dataframe(balance_sheet_filtered)

    st.write('### Báo Cáo Lãi Lỗ')
    st.dataframe(income_statement_filtered)

    st.write('### Báo Cáo Lưu Chuyển Tiền Tệ')
    st.dataframe(cash_flow_filtered)

    # Thêm các chỉ số bổ sung
    balance_sheet_filtered['ROE (%)'] = (income_statement_filtered['Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)'] / balance_sheet_filtered['VỐN CHỦ SỞ HỮU (Tỷ đồng)']) * 100
    st.write('### Tỷ Suất Lợi Nhuận Trên Vốn Chủ Sở Hữu (ROE)')
    st.dataframe(balance_sheet_filtered[['Năm', 'ROE (%)']])

except ValueError as e:
    st.error(f"Lỗi: {str(e)}")

except Exception as e:
    st.error(f"Có lỗi xảy ra: {str(e)}")

# Chạy ứng dụng Streamlit
# Để chạy ứng dụng: `streamlit run your_script.py`
