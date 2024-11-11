import streamlit as st
from vnstock3 import Vnstock
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import io

# Khởi tạo đối tượng Vnstock để lấy danh sách cổ phiếu
stock_data = Vnstock()

# Hàm để lấy dữ liệu tài chính cho một mã cổ phiếu
def fetch_stock_data(symbol, num_years):
    try:
        # Khởi tạo đối tượng cho mã cổ phiếu hiện tại
        stock = stock_data.stock(symbol=symbol, source='VCI')

        # Lấy các chỉ số từ Bảng cân đối kế toán
        balance_sheet = stock.finance.balance_sheet(period='year', lang='vi', dropna=True)
        if 'Năm' in balance_sheet.columns and 'VỐN CHỦ SỞ Hữu (Tỷ đồng)' in balance_sheet.columns and 'NỢ PHẢI TRẢ (Tỷ đồng)' in balance_sheet.columns:
            balance_sheet_filtered = balance_sheet[['Năm', 'VỐN CHỦ Sữu (Tỷ đồng)', 'NỢ PHẢI TRẢ (Tỷ đồng)']].copy()
            # Kiểm tra nếu cột "Nợ dài hạn (Tỷ đồng)" không tồn tại, thêm cột này với giá trị mặc định là 0
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
            cash_flow_filtered.rename(columns={'yearReport': 'Năm'}, inplace=True)  # Đổi tên cột 'yearReport' thành 'Năm'
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
        balance_sheet_filtered['ROE (%)'] = (income_statement_filtered['Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)'] / balance_sheet_filtered['VỐN CHỦ Sữu (Tỷ đồng)']) * 100
        balance_sheet_filtered['Nợ dài hạn/Vốn chủ sữu (%)'] = (balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'] / balance_sheet_filtered['VỐN CHỦ Sữu (Tỷ đồng)']) * 100
        balance_sheet_filtered['ROIC (%)'] = (income_statement_filtered['Lợi nhuận sau thuế của Cổ đông công ty mẹ (Tỷ đồng)'] / (balance_sheet_filtered['VỐN CHỦ Sữu (Tỷ đồng)'] + balance_sheet_filtered['Nợ dài hạn (Tỷ đồng)'])) * 100

        # Tính OCPS (Operating Cashflow Per Share)
        if 'Số CP lưu hành' in financial_ratios_filtered.columns and 'Net cash inflows/outflows from operating activities' in cash_flow_filtered.columns:
            cash_flow_filtered['OCPS'] = cash_flow_filtered['Net cash inflows/outflows from operating activities'] / financial_ratios_filtered['Số CP lưu hành']  # Không đổi Số CP lưu hành từ triệu sang đơn vị cổ phiếu
        else:
            cash_flow_filtered['OCPS'] = None

        # Tính tỷ lệ tăng trưởng hàng năm trong num_years của doanh thu, vốn chủ sữu, EPS, BVPS, OCPS
        metrics_info = {
            'Doanh thu (Tỷ đồng)': income_statement_filtered,
            'VỐN CHỦ Sữu (Tỷ đồng)': balance_sheet_filtered,
            'EPS': financial_ratios_filtered,
            'BVPS': financial_ratios_filtered,
            'OCPS': cash_flow_filtered
        }

        for metric, data_source in metrics_info.items():
            final_year = 2023
            initial_year = final_year - (num_years - 1)  # Lấy giá trị của năm bắt đầu cách num_years - 1 từ năm cuối

            # Kiểm tra nếu cả năm cuối và năm bắt đầu đều có trong dữ liệu
            if (initial_year in data_source['Năm'].values) and (final_year in data_source['Năm'].values):
                initial_value = data_source.loc[data_source['Năm'] == initial_year, metric].values[0]
                final_value = data_source.loc[data_source['Năm'] == final_year, metric].values[0]
                
                # Kiểm tra nếu initial_value lớn hơn threshold để tránh lỗi tính toán
                threshold = 0.001
                if abs(initial_value) > threshold:
                    nper = num_years - 1  # Số kỳ là num_years - 1 năm (từ năm bắt đầu đến năm cuối)
                    cagr_years = ((final_value / initial_value) ** (1 / nper)) - 1
                    data_source[f'Tăng trưởng {metric} {num_years} năm (%)'] = cagr_years * 100
                else:
                    data_source[f'Tăng trưởng {metric} {num_years} năm (%)'] = None
            else:
                # Nếu không đủ dữ liệu cho cả hai năm, không tính tỷ lệ tăng trưởng
                data_source[f'Tăng trưởng {metric} {num_years} năm (%)'] = None

        # Kết hợp tất cả các chỉ số của mã cổ phiếu hiện tại
        merged_data = balance_sheet_filtered.merge(income_statement_filtered, on='Năm', how='inner')
        merged_data = merged_data.merge(cash_flow_filtered, on='Năm', how='inner')
        merged_data = merged_data.merge(financial_ratios_filtered, on='Năm', how='inner')

        # Thêm cột mã cổ phiếu vào DataFrame
        merged_data.insert(0, 'Mã cổ phiếu', symbol)

        return merged_data
    except Exception as e:
        # Nếu có lỗi, in ra mã cổ phiếu và lỗi đó
        print(f"Lỗi xảy ra với mã cổ phiếu {symbol}: {e}")
        return None

# Streamlit App cải tiến
st.title("Stock Data Analyzer")
st.sidebar.header("Tùy chọn")

# Nhập mã cổ phiếu, cho phép nhiều mã
symbols_input = st.sidebar.text_area("Nhập mã cổ phiếu (cách nhau bởi dấu phẩy):", "ACB, FPT, VCB")
symbols = [symbol.strip().upper() for symbol in symbols_input.split(",") if symbol.strip()]

# Nhập số năm muốn phân tích
num_years = st.sidebar.slider("Chọn số năm phân tích:", min_value=5, max_value=10, value=10)

if st.sidebar.button("Lấy dữ liệu"):
    with st.spinner('Đang lấy dữ liệu...'):
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_stock_data, symbol, num_years) for symbol in symbols]
            for future in futures:
                result = future.result()
                if result is not None:
                    results.append(result)

        if results:
            # Kết hợp tất cả các kết quả thành một bảng duy nhất
            final_data = pd.concat(results, ignore_index=True)
            st.success("Dữ liệu đã sẵn sàng!")

            # Hiển thị dữ liệu
            st.write(final_data)

            # Tải về file Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_data.to_excel(writer, index=False, sheet_name="Stock Data")
            st.download_button(label="Tải về file Excel", data=output.getvalue(), file_name="stock_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("Không tìm thấy dữ liệu cho các mã cổ phiếu đã nhập.")
