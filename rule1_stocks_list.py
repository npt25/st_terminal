import streamlit as st
from vnstock3 import Vnstock
import pandas as pd
import numpy as np

# Khởi tạo đối tượng Vnstock để lấy danh sách cổ phiếu
stock_data = Vnstock()

# Nhập số năm muốn phân tích thông qua Streamlit
st.title("Phân tích tài chính cổ phiếu")
num_years = st.sidebar.slider("Chọn số năm phân tích:", min_value=5, max_value=10, value=10)

# Khi người dùng nhấn nút "Generate"
if st.sidebar.button("Generate"):
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

                # Tính OCPS (Operating Cashflow Per Share)
                if 'Số CP lưu hành' in financial_ratios_filtered.columns and 'Net cash inflows/outflows from operating activities' in cash_flow_filtered.columns:
                    cash_flow_filtered['OCPS'] = cash_flow_filtered['Net cash inflows/outflows from operating activities'] / (financial_ratios_filtered['Số CP lưu hành'] * 1_000_000)
                else:
                    cash_flow_filtered['OCPS'] = None

                # Tính tỷ lệ tăng trưởng hàng năm trong num_years của doanh thu, vốn chủ sở hữu, EPS, BVPS, OCPS
                metrics_info = {
                    'Doanh thu (Tỷ đồng)': income_statement_filtered,
                    'VỐN CHỦ SỞ HỮU (Tỷ đồng)': balance_sheet_filtered,
                    'EPS': financial_ratios_filtered,
                    'BVPS': financial_ratios_filtered,
                    'OCPS': cash_flow_filtered
                }

                for metric, data_source in metrics_info.items():
                    final_year = 2023
                    initial_year = final_year - (num_years - 1)
                    column_name = f'Tăng trưởng {metric} {num_years} năm (%)'

                    if (initial_year in data_source['Năm'].values) and (final_year in data_source['Năm'].values):
                        initial_value = data_source.loc[data_source['Năm'] == initial_year, metric].values[0]
                        final_value = data_source.loc[data_source['Năm'] == final_year, metric].values[0]
                        threshold = 0.001
                        if abs(initial_value) > threshold:
                            nper = num_years - 1
                            cagr_years = ((final_value / initial_value) ** (1 / nper)) - 1
                            data_source[column_name] = cagr_years * 100
                        else:
                            data_source[column_name] = None
                    else:
                        data_source[column_name] = None

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

        # Chạy tất cả các cổ phiếu và in danh sách các cổ phiếu có MOS <= Value Present / 2
        all_symbols = stock_data.list_all_symbols()
        mos_symbols = []

        for symbol in all_symbols:
            stock_data_result = fetch_stock_data(symbol, num_years)
            if stock_data_result is not None:
                cagr_column_name = f'Tăng trưởng VỐN CHỦ SỞ HỮU (Tỷ đồng) {num_years} năm (%)'
                cagr_future = stock_data_result[cagr_column_name].median() if cagr_column_name in stock_data_result.columns else None
                pe_median = stock_data_result['P/E'].median()
                eps_2023 = stock_data_result[stock_data_result['Năm'] == 2023]['EPS'].iloc[0]
                if not pd.isna(eps_2023) and not pd.isna(cagr_future):
                    eps_future = eps_2023 * ((1 + (cagr_future / 100)) ** 10)
                    value_future = eps_future * pe_median
                    value_present = value_future / ((1 + 0.15) ** 10)
                    mos = value_present / 2
                    if mos <= value_present / 2:
                        mos_symbols.append(symbol)

        st.write("Danh sách các cổ phiếu có MOS <= Value Present / 2:")
        st.write(mos_symbols)
