import streamlit as st
from vnstock3 import Vnstock
import pandas as pd
import numpy as np
import io

# Khởi tạo đối tượng Vnstock để lấy danh sách cổ phiếu
stock_data = Vnstock()

# Nhập mã cổ phiếu và số năm muốn phân tích thông qua Streamlit
st.title("Phân tích tài chính cổ phiếu")
symbol = st.sidebar.text_input("Nhập mã cổ phiếu (ví dụ: ACB):", "ACB")
num_years = st.sidebar.slider("Chọn số năm phân tích:", min_value=5, max_value=10, value=10)

# Khi người dùng nhấn nút "Lấy dữ liệu"
if st.sidebar.button("Lấy dữ liệu"):
    with st.spinner('Đang lấy dữ liệu...'):
        # Hàm để lấy dữ liệu tài chính cho một mã cổ phiếu với số năm nhất định
        def fetch_stock_data(symbol, num_years):
            try:
                # Khởi tạo đối tượng cho mã cổ phiếu hiện tại
                stock = stock_data.stock(symbol=symbol, source='VCI')

                # Lấy các chỉ số từ Bảng cân đối kế toán
                balance_sheet = stock.finance.balance_sheet(period='year', lang='vi', dropna=True)
                balance_sheet_filtered = balance_sheet[balance_sheet['Năm'] >= (2023 - num_years + 1)].copy()
                if 'Năm' in balance_sheet_filtered.columns and 'VỐN CHỦ SỞ HỮU (Tỷ đồng)' in balance_sheet_filtered.columns and 'NỢ PHẢI TRẢ (Tỷ đồng)' in balance_sheet_filtered.columns:
                    balance_sheet_filtered = balance_sheet_filtered[['Năm', 'VỐN CHỦ SỞ HỮU (Tỷ đồng)', 'NỢ PHẢI TRẢ (Tỷ đồng)']]
                    if 'Nợ dài hạn (Tỷ đồng)' in balance_sheet.columns:
                        balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'] = balance_sheet['Nợ dài hạn (Tỷ đồng)'].copy()
                    else:
                        balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'] = 0
                else:
                    raise ValueError("Thiếu cột cần thiết trong bảng cân đối kế toán")

                # Lấy các chỉ số từ Báo cáo lãi lỗ
                income_statement = stock.finance.income_statement(period='year', lang='vi', dropna=True)
                income_statement_filtered = income_statement[income_statement['Năm'] >= (2023 - num_years + 1)].copy()
                if 'Năm' in income_statement_filtered.columns and 'Doanh thu (Tỷ đồng)' in income_statement_filtered.columns and 'Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)' in income_statement_filtered.columns:
                    income_statement_filtered = income_statement_filtered[['Năm', 'Doanh thu (Tỷ đồng)', 'Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)']]
                else:
                    raise ValueError("Thiếu cột cần thiết trong báo cáo lãi lỗ")

                # Lấy các chỉ số từ Báo cáo lưu chuyển tiền tệ
                cash_flow = stock.finance.cash_flow(period='year', dropna=True)
                cash_flow_filtered = cash_flow[cash_flow['yearReport'] >= (2023 - num_years + 1)].copy()
                if 'yearReport' in cash_flow_filtered.columns and 'Net cash inflows/outflows from operating activities' in cash_flow_filtered.columns:
                    cash_flow_filtered = cash_flow_filtered[['yearReport', 'Net cash inflows/outflows from operating activities']]
                    cash_flow_filtered.rename(columns={'yearReport': 'Năm'}, inplace=True)
                else:
                    raise ValueError("Thiếu cột cần thiết trong báo cáo lưu chuyển tiền tệ")

                # Lấy các chỉ số từ Chỉ số tài chính
                financial_ratios = stock.finance.ratio(period='year', lang='vi', dropna=True)
                financial_ratios_filtered = financial_ratios[financial_ratios[('Meta', 'Năm')] >= (2023 - num_years + 1)].copy()
                required_columns = [('Meta', 'Năm'), ('Chỉ tiêu định giá', 'EPS (VND)'), ('Chỉ tiêu định giá', 'BVPS (VND)'), ('Chỉ tiêu định giá', 'Số CP lưu hành (Triệu CP)'), ('Chỉ tiêu định giá', 'P/E')]
                if all(col in financial_ratios_filtered.columns for col in required_columns):
                    financial_ratios_filtered = financial_ratios_filtered[required_columns]
                    financial_ratios_filtered.columns = ['Năm', 'EPS', 'BVPS', 'Số CP lưu hành', 'P/E']
                else:
                    raise ValueError("Thiếu cột cần thiết trong chỉ số tài chính")

                # Tính toán các chỉ số bổ sung
                balance_sheet_filtered['ROE (%)'] = (income_statement_filtered['Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)'] / balance_sheet_filtered['VỐN CHỦ SỞ HỮU (Tỷ đồng)']) * 100
                balance_sheet_filtered['Nợ dài hạn/Vốn chủ sở hữu (%)'] = (balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'] / balance_sheet_filtered['VỐN CHỦ SỞ HỮU (Tỷ đồng)']) * 100
                balance_sheet_filtered['ROIC (%)'] = (income_statement_filtered['Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)'] / (balance_sheet_filtered['VỐN CHỦ SỞ HỮU (Tỷ đồng)'] + balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'])) * 100

                # Kết hợp tất cả các chỉ số của mã cổ phiếu hiện tại
                merged_data = balance_sheet_filtered.merge(income_statement_filtered, on='Năm', how='inner')
                merged_data = merged_data.merge(cash_flow_filtered, on='Năm', how='inner')
                merged_data = merged_data.merge(financial_ratios_filtered, on='Năm', how='inner')

                # Thêm cột mã cổ phiếu vào DataFrame
                merged_data.insert(0, 'Mã cổ phiếu', symbol)

                return merged_data
            except Exception as e:
                st.error(f"Lỗi xảy ra với mã cổ phiếu {symbol}: {e}")
                return None

        # Lấy dữ liệu tài chính cho mã cổ phiếu được nhập
        stock_data_result = fetch_stock_data(symbol, num_years)

        # Nếu có dữ liệu
        if stock_data_result is not None:
            # Tạo bảng tổng hợp các chỉ số tài chính
            with st.container():
                st.subheader("Tổng hợp dữ liệu tài chính")
                st.table(stock_data_result[['Năm', 'VỐN CHỦ SỞ HỮU (Tỷ đồng)', 'Doanh thu (Tỷ đồng)', 'Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)',
                                           'Net cash inflows/outflows from operating activities', 'Nợ dài hạn (Tỷ đồng)', 'EPS', 'BVPS', 'P/E']])

            # Tạo bảng giá trị hiện tại (Present Value)
            present_value_summary = pd.DataFrame({
                '': ['P/E Median', 'CAGR Future', 'EPS Future', 'Value Future', 'Value Present', 'MOS'],
                'Giá trị': [None, None, None, None, None, None]  # Giá trị này cần được tính toán phù hợp trước
            })

            with st.container():
                st.subheader("Giá trị hiện tại (Present Value)")
                st.table(present_value_summary)

            # Tạo bảng MOS Market Cap
            mos_market_cap_summary = pd.DataFrame({
                '': ['MOS', 'Outstanding Shares 2023', 'MOS Market Cap'],
                'Giá trị': [None, None, None]  # Giá trị này cần được tính toán phù hợp trước
            })

            with st.container():
                st.subheader("MOS Market Cap")
                st.table(mos_market_cap_summary)

            # Tạo bảng Pay Back Time
            payback_data = pd.DataFrame({'Years': range(0, 15), 'Retained Earning (million)': [None] * 15})

            with st.container():
                st.subheader("Pay Back Time")
                st.table(payback_data)

            # Tải về file Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                stock_data_result.to_excel(writer, index=False, sheet_name='Tổng hợp dữ liệu tài chính')
                present_value_summary.to_excel(writer, index=False, sheet_name='Present Value')
                mos_market_cap_summary.to_excel(writer, index=False, sheet_name='MOS Market Cap')
                payback_data.to_excel(writer, index=False, sheet_name='Pay Back Time')

            st.download_button(
                label="Tải về file Excel", 
                data=output.getvalue(), 
                file_name=f"{symbol}_stock_data.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            st.error(f"Không tìm thấy dữ liệu cho mã cổ phiếu {symbol}.")
