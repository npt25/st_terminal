import streamlit as st
from vnstock3 import Vnstock
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import io
import logging

# Khởi tạo đối tượng Vnstock để lấy danh sách cổ phiếu
stock_data = Vnstock()
logger = logging.getLogger(__name__)

st.title("Stock Data Analyzer")
st.sidebar.header("Tùy chọn")

# Nhập mã cổ phiếu
symbol = st.sidebar.text_input("Nhập mã cổ phiếu (ví dụ: ACB):", "ACB")

# Nhập số năm muốn phân tích
num_years = st.sidebar.slider("Chọn số năm phân tích:", min_value=5, max_value=10, value=10)

if st.sidebar.button("Lấy dữ liệu"):
    with st.spinner('Đang lấy dữ liệu...'):
        try:
            # Lấy danh sách tất cả các mã cổ phiếu từ nguồn VCI
            # Lọc chỉ những mã có 3 chữ cái
            all_symbols_raw = stock_data.stock(symbol='ACB', source='VCI').listing.all_symbols()
            all_symbols = [entry['ticker'] for entry in all_symbols_raw if isinstance(entry, dict) and 'ticker' in entry and isinstance(entry['ticker'], str) and len(entry['ticker']) == 3 and entry['ticker'].isalpha()]

            # Lọc các mã cổ phiếu có dữ liệu hợp lệ
            valid_symbols = []  # Lưu trữ các mã cổ phiếu hợp lệ
            for symbol in all_symbols:  # Duyệt qua tất cả các mã cổ phiếu để xác minh
                try:
                    # Kiểm tra xem mã cổ phiếu có dữ liệu không
                    stock = stock_data.stock(symbol=symbol, source='VCI')
                    balance_sheet = stock.finance.balance_sheet(period='year', lang='vi', dropna=True)
                    if not balance_sheet.empty:
                        valid_symbols.append(symbol)
                except Exception as e:
                    logger.warning(f"Mã cổ phiếu {symbol} không hợp lệ hoặc không có dữ liệu: {e}")
                    continue

            # Giới hạn danh sách mã cổ phiếu chỉ lấy 5 mã đầu tiên
            valid_symbols = valid_symbols[:5]

            # Lấy dữ liệu tài chính cho mã cổ phiếu đã nhập
            stock = stock_data.stock(symbol=symbol, source='VCI')

            # Lấy các chỉ số từ Bảng cân đối kế toán
            balance_sheet = stock.finance.balance_sheet(period='year', lang='vi', dropna=True)
            if balance_sheet.empty:
                raise ValueError("Không có dữ liệu bảng cân đối kế toán")
            if 'Năm' in balance_sheet.columns and 'VỐN CHỦ SỞ HỮU (Tỷ đồng)' in balance_sheet.columns and 'NỢ PHẢI TRẢ (Tỷ đồng)' in balance_sheet.columns:
                balance_sheet_filtered = balance_sheet[['Năm', 'VỐN CHỦ SỞ HỮU (Tỷ đồng)', 'NỢ PHẢI TRẢ (Tỷ đồng)']].copy()
                # Kiểm tra nếu cột "Nợ dài hạn (Tỷ đồng)" không tồn tại, thêm cột này với giá trị mặc định là 0
                balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'] = balance_sheet.get('Nợ dài hạn (Tỷ đồng)', 0)
            else:
                raise ValueError("Thiếu cột cần thiết trong bảng cân đối kế toán")

            # Lấy các chỉ số từ Báo cáo lãi lỗ
            income_statement = stock.finance.income_statement(period='year', lang='vi', dropna=True)
            if income_statement.empty:
                raise ValueError("Không có dữ liệu báo cáo lãi lỗ")
            if 'Năm' in income_statement.columns and 'Doanh thu (Tỷ đồng)' in income_statement.columns and 'Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)' in income_statement.columns:
                income_statement_filtered = income_statement[['Năm', 'Doanh thu (Tỷ đồng)', 'Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)']].copy()
            else:
                raise ValueError("Thiếu cột cần thiết trong báo cáo lãi lỗ")

            # Lấy các chỉ số từ Báo cáo lưu chuyển tiền tệ
            cash_flow = stock.finance.cash_flow(period='year', dropna=True)
            if cash_flow.empty:
                raise ValueError("Không có dữ liệu báo cáo lưu chuyển tiền tệ")
            if 'yearReport' in cash_flow.columns and 'Net cash inflows/outflows from operating activities' in cash_flow.columns:
                cash_flow_filtered = cash_flow[['yearReport', 'Net cash inflows/outflows from operating activities']].copy()
                cash_flow_filtered.rename(columns={'yearReport': 'Năm'}, inplace=True)  # Đổi tên cột 'yearReport' thành 'Năm'
            else:
                raise ValueError("Thiếu cột cần thiết trong báo cáo lưu chuyển tiền tệ")

            # Lấy các chỉ số từ Chỉ số tài chính
            financial_ratios = stock.finance.ratio(period='year', lang='vi', dropna=True)
            if financial_ratios.empty:
                raise ValueError("Không có dữ liệu chỉ số tài chính")
            required_columns = [('Meta', 'Năm'), ('Chỉ tiêu định giá', 'EPS (VND)'), ('Chỉ tiêu định giá', 'BVPS (VND)'), ('Chỉ tiêu định giá', 'Số CP lưu hành (Triệu CP)'), ('Chỉ tiêu định giá', 'P/E')]
            if all(col in financial_ratios.columns for col in required_columns):
                financial_ratios_filtered = financial_ratios[required_columns].copy()
                financial_ratios_filtered.columns = ['Năm', 'EPS', 'BVPS', 'Số CP lưu hành', 'P/E']
            else:
                raise ValueError("Thiếu cột cần thiết trong chỉ số tài chính")

            # Tính toán các chỉ số bổ sung
            balance_sheet_filtered['ROE (%)'] = (income_statement_filtered['Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)'] / balance_sheet_filtered['VỐN CHỦ SỞ HỮU (Tỷ đồng)']) * 100
            balance_sheet_filtered['Nợ dài hạn/Vốn chủ sở hữu (%)'] = (balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'] / balance_sheet_filtered['VỐN CHỦ SỞ HỮU (Tỷ đồng)']) * 100
            balance_sheet_filtered['ROIC (%)'] = (income_statement_filtered['Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)'] / (balance_sheet_filtered['VỐN CHỦ SỞ HỮU (Tỷ đồng)'] + balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'])) * 100

            # Hiển thị dữ liệu
            st.write("### Bảng cân đối kế toán:")
            st.dataframe(balance_sheet_filtered)

            st.write("### Báo cáo lãi lỗ:")
            st.dataframe(income_statement_filtered)

            st.write("### Báo cáo lưu chuyển tiền tệ:")
            st.dataframe(cash_flow_filtered)

            st.write("### Chỉ số tài chính:")
            st.dataframe(financial_ratios_filtered)

            st.success(f"Dữ liệu cho mã cổ phiếu {symbol} đã sẵn sàng!")
        except Exception as e:
            st.error(f"Không tìm thấy dữ liệu cho mã cổ phiếu {symbol}: {e}")
