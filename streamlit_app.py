import streamlit as st
import pandas as pd
from vnstock3 import Vnstock
from concurrent.futures import ThreadPoolExecutor

# Khởi tạo đối tượng Vnstock để lấy danh sách cổ phiếu
stock_data = Vnstock()

# Lấy danh sách tất cả các mã chứng khoán tự động từ TCBS
symbols = stock_data.stock(symbol='ACB', source='VCI').listing.all_symbols()['ticker'].tolist()  # Lấy tất cả các mã cổ phiếu

# Hàm để lấy dữ liệu tài chính cho một mã cổ phiếu
def fetch_stock_data(symbol):
    try:
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

        # Kết hợp tất cả các chỉ số của mã cổ phiếu hiện tại
        merged_data = balance_sheet_filtered.merge(income_statement_filtered, on='Năm', how='inner')
        merged_data = merged_data.merge(cash_flow_filtered, on='Năm', how='inner')
        merged_data = merged_data.merge(financial_ratios_filtered, on='Năm', how='inner')

        # Thêm cột mã cổ phiếu vào DataFrame
        merged_data.insert(0, 'Mã cổ phiếu', symbol)

        return merged_data
    except Exception as e:
        # Nếu có lỗi, in ra mã cổ phiếu và lỗi đó
        st.warning(f"Lỗi xảy ra với mã cổ phiếu {symbol}: {e}")
        return None

# Sử dụng ThreadPoolExecutor để chạy song song các yêu cầu
with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(fetch_stock_data, symbols))

# Lọc ra các kết quả không phải là None
all_data = [data for data in results if data is not None]

# Bước 3: Kết hợp tất cả dữ liệu từ các cổ phiếu thành một DataFrame duy nhất
if all_data:
    final_data = pd.concat(all_data, ignore_index=True)

    # Lọc kết quả với các điều kiện: ROE > 15%, ROIC > 10%, Nợ dài hạn/Vốn chủ sở hữu < 3
    filtered_data = final_data[(final_data['ROE (%)'] > 15) &
                               (final_data['ROIC (%)'] > 10) &
                               (final_data['Nợ dài hạn/Vốn chủ sở hữu (%)'] < 3)]

    # Giao diện Streamlit
    st.title('Ứng dụng phân tích tài chính cổ phiếu')
    st.write("Danh sách mã cổ phiếu đạt điều kiện lọc:")

    # Hiển thị kết quả
    st.dataframe(filtered_data)

    # Tải xuống kết quả
    st.download_button(label="Tải xuống kết quả", data=filtered_data.to_csv(index=False), file_name='filtered_stocks.csv', mime='text/csv')
else:
    st.write("Không có dữ liệu nào để kết hợp.")
