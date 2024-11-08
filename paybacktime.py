import streamlit as st
from vnstock3 import Vnstock
import pandas as pd
import numpy as np

# Khởi tạo đối tượng Vnstock để lấy danh sách cổ phiếu
stock_data = Vnstock()

# Nhập mã cổ phiếu từ người dùng thông qua Streamlit
st.title("Phân tích tài chính cổ phiếu")
symbol = st.text_input("Nhập mã cổ phiếu:")

# Tạo danh sách để lưu các DataFrame dữ liệu tài chính của mã cổ phiếu
all_data = []

# Hàm để lấy dữ liệu tài chính cho một mã cổ phiếu
def fetch_stock_data(symbol):
    try:
        # Khởi tạo đối tượng cho mã cổ phiếu hiện tại
        stock = stock_data.stock(symbol=symbol, source='VCI')

        # Lấy các chỉ số từ Bảng cân đối kế toán
        balance_sheet = stock.finance.balance_sheet(period='year', lang='vi', dropna=True)
        if 'Năm' in balance_sheet.columns and 'VỐN CHỦ SỞ HỮU (Tỷ đồng)' in balance_sheet.columns and 'NỢ PHẢI TRẢ (Tỷ đồng)' in balance_sheet.columns:
            balance_sheet_filtered = balance_sheet[['Năm', 'VỐN CHỦ SỞ HỮU (Tỷ đồng)', 'NỢ PHẢI TRẢ (Tỷ đồng)']].copy()
            if 'Nợ dài hạn (Tỷ đồng)' in balance_sheet.columns:
                balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'] = balance_sheet['Nợ dài hạn (Tỷ đồng)']
            else:
                balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'] = 0
        else:
            raise ValueError("Thiếu cột cần thiết trong bảng cân đối kế toán")

        # Lấy các chỉ số từ Báo cáo lãi lỗ
        income_statement = stock.finance.income_statement(period='year', lang='vi', dropna=True)
        if 'Năm' in income_statement.columns and 'Doanh thu (Tỷ đồng)' in income_statement.columns and 'Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)' in income_statement.columns:
            income_statement_filtered = income_statement[['Năm', 'Doanh thu (Tỷ đồng)', 'Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)']].copy()
        else:
            raise ValueError("Thiếu cột cần thiết trong báo cáo lãi lỗ")

        # Lấy các chỉ số từ Báo cáo lưu chuyển tiền tệ
        cash_flow = stock.finance.cash_flow(period='year', dropna=True)
        if 'yearReport' in cash_flow.columns and 'Net cash inflows/outflows from operating activities' in cash_flow.columns:
            cash_flow_filtered = cash_flow[['yearReport', 'Net cash inflows/outflows from operating activities']].copy()
            cash_flow_filtered.rename(columns={'yearReport': 'Năm'}, inplace=True)
        else:
            raise ValueError("Thiếu cột cần thiết trong báo cáo lưu chuyển tiền tệ")

        # Lấy các chỉ số từ Chỉ số tài chính
        financial_ratios = stock.finance.ratio(period='year', lang='vi', dropna=True)
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

        # Tính OCPS (Operating Cashflow Per Share)
        if 'Số CP lưu hành' in financial_ratios_filtered.columns and 'Net cash inflows/outflows from operating activities' in cash_flow_filtered.columns:
            cash_flow_filtered['OCPS'] = cash_flow_filtered['Net cash inflows/outflows from operating activities'] / financial_ratios_filtered['Số CP lưu hành']
        else:
            cash_flow_filtered['OCPS'] = None

        # Tính tỷ lệ tăng trưởng hàng năm trong 10 năm của doanh thu, vốn chủ sở hữu, EPS, BVPS, OCPS
        metrics_info = {
            'Doanh thu (Tỷ đồng)': income_statement_filtered,
            'VỐN CHỦ SỞ HỮU (Tỷ đồng)': balance_sheet_filtered,
            'EPS': financial_ratios_filtered,
            'BVPS': financial_ratios_filtered,
            'OCPS': cash_flow_filtered
        }

        for metric, data_source in metrics_info.items():
            final_year = 2023
            initial_year = final_year - 9

            if (initial_year in data_source['Năm'].values) and (final_year in data_source['Năm'].values):
                initial_value = data_source.loc[data_source['Năm'] == initial_year, metric].values[0]
                final_value = data_source.loc[data_source['Năm'] == final_year, metric].values[0]
                
                threshold = 0.001
                if abs(initial_value) > threshold:
                    nper = 9
                    cagr_10_years = ((final_value / initial_value) ** (1 / nper)) - 1
                    data_source[f'Tăng trưởng {metric} 10 năm (%)'] = cagr_10_years * 100
                else:
                    data_source[f'Tăng trưởng {metric} 10 năm (%)'] = None
            else:
                data_source[f'Tăng trưởng {metric} 10 năm (%)'] = None

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
if symbol:
    stock_data_result = fetch_stock_data(symbol)

    # Nếu có dữ liệu, tiếp tục thực hiện các bước tính toán
    if stock_data_result is not None:
        filtered_data = stock_data_result[stock_data_result['ROE (%)'] > 15]

        # Tính Median của P/E trong 10 năm gần nhất cho mã cổ phiếu
        filtered_data['P/E Median'] = filtered_data['P/E'].dropna().median() if len(filtered_data['P/E'].dropna()) > 0 else None

        # Tính CAGR Future
        filtered_data['CAGR Vốn Chủ Sở Hữu'] = filtered_data['Tăng trưởng VỐN CHỦ SỞ HỮU (Tỷ đồng) 10 năm (%)']
        filtered_data['CAGR Doanh Thu'] = filtered_data['Tăng trưởng Doanh thu (Tỷ đồng) 10 năm (%)']
        filtered_data['CAGR Future (%)'] = filtered_data[['CAGR Vốn Chủ Sở Hữu', 'CAGR Doanh Thu']].min(axis=1)

        # Tính EPS Future sau 10 năm
        filtered_data['EPS 2023'] = filtered_data.loc[filtered_data['Năm'] == 2023, 'EPS']
        filtered_data['EPS Future'] = filtered_data['EPS 2023'] * ((1 + filtered_data['CAGR Future (%)'] / 100) ** 10)

        # Tính Value Future sau 10 năm
        filtered_data['Value Future'] = filtered_data['EPS Future'] * filtered_data['P/E Median']

        # Tính Value Present với r = 15% và số năm là 10
        discount_rate = 0.15
        filtered_data['Value Present'] = filtered_data['Value Future'] / ((1 + discount_rate) ** 10)

        # Tính MOS (Margin of Safety)
        filtered_data['MOS'] = filtered_data['Value Present'] / 2

        # Tạo bảng Present Value
        present_value_df = filtered_data[['Mã cổ phiếu', 'Value Present', 'MOS']]
        st.write("### Present Value", present_value_df)

        # Lấy số lượng cổ phiếu lưu hành năm 2023
        filtered_data['Outstanding Shares 2023'] = filtered_data.loc[filtered_data['Năm'] == 2023, 'Số CP lưu hành']

        # Tính MOS Market Cap
        filtered_data['MOS Market Cap'] = filtered_data['MOS'] * filtered_data['Outstanding Shares 2023']

        # Tạo bảng MOS Market Cap
        mos_market_cap_df = filtered_data[['Mã cổ phiếu', 'MOS', 'Outstanding Shares 2023', 'MOS Market Cap']]
        st.write("### MOS Market Cap", mos_market_cap_df)

        # Tạo bảng Pay Back Time
        payback_time_list = []

        eps_2023 = filtered_data['EPS 2023'].values[0]
        shares_2023 = filtered_data['Outstanding Shares 2023'].values[0]
        cagr_future = filtered_data['CAGR Future (%)'].values[0] / 100

        years = list(range(16))
        retained_earning = []
        retained_earning_year_0 = eps_2023 * shares_2023
        retained_earning.append(retained_earning_year_0)
        
        for year in range(1, 16):
            retained_earning_year = retained_earning[-1] * (1 + cagr_future) + retained_earning[-1]
            retained_earning.append(retained_earning_year)

        payback_time_df = pd.DataFrame({'Mã cổ phiếu': symbol, 'Years': years, 'Retained Earning': retained_earning})
        payback_time_list.append(payback_time_df)

        payback_time_final_df = pd.concat(payback_time_list, ignore_index=True)
        st.write("### Pay Back Time", payback_time_final_df)

    else:
        st.warning("Không có dữ liệu nào để kết hợp.")
