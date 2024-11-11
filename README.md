# Stock Data Analyzer Web App - Streamlit

This is a Streamlit-based web application designed to analyze financial data for Vietnamese stocks. The application allows users to input a specific stock ticker and retrieve calculated financial metrics such as the 10-year compound annual growth rates (CAGR) for revenue, equity, EPS, BVPS, OCPS, as well as other indicators like ROE, ROIC, and debt-to-equity ratio.

## Features
- **Dynamic Stock Data Retrieval**: Users can enter any stock symbol, and the app will retrieve data directly from TCBS.
- **Financial Metrics Calculation**: The app calculates various key financial indicators:
  - **10-Year CAGR** for Revenue, Equity, EPS, BVPS, OCPS.
  - **ROE** for 2023.
  - **ROIC** for 2023.
  - **Debt-to-Equity Ratio** for 2023.
- **Customizable Analysis Duration**: Users can change the number of years to analyze CAGR for up to 10 years (e.g., 10, 9, 8 years, etc.).
- **Excel Download Option**: The app allows users to download the analyzed data in an Excel file for offline use.

## How to Run the Application

1. **Install Dependencies**: Before running the application, install the required libraries. You can do this by executing:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**: To start the Streamlit application, run the following command:
   ```bash
   streamlit run du_lieu_co_phieu_streamlit.py
   ```
   Streamlit will provide a URL where you can access the application.

## Required Packages

The application requires the following Python packages:
- **streamlit**: For creating the web app interface.
- **vnstock3**: To retrieve stock data from TCBS.
- **pandas**: For data manipulation and financial calculations.
- **openpyxl**: For writing the output Excel file.

You can find these dependencies in the `requirements.txt` file, which you can use to set up your environment.

## Application Workflow
- The user inputs a stock ticker.
- The app retrieves stock data, including balance sheet, income statement, and cash flow information.
- Calculated financial metrics are displayed on the Streamlit interface.
- Users can download the results as an Excel file.

## Folder Structure
- **/st_terminal/**: Contains the main Python file (`du_lieu_co_phieu_streamlit.py`) and necessary dependencies.
- **vnstock3/**: Directory for the library used to access stock data.
- **README.md**: Provides information about the project.

## Example Usage
To analyze a specific stock, simply input the ticker symbol (e.g., `MBB`, `VIC`) in the text field. You can also choose the number of years for CAGR analysis from the sidebar.

After running the analysis, the metrics are displayed in the Streamlit app interface. To download the analysis results, click the "Download Excel" button.

## Troubleshooting
- **Missing Packages**: If you encounter a `ModuleNotFoundError`, ensure all required packages in `requirements.txt` are installed.
- **Slow Performance**: If the application takes too long to retrieve data, it might be due to multiple requests to the server. You can try analyzing fewer years or specific tickers to reduce processing time.

## Contribution
Feel free to fork this repository and contribute. Any improvements regarding optimization, additional features, or bug fixes are highly welcome!

## License
This application is provided under the [MIT License](https://opensource.org/licenses/MIT). See the LICENSE file for more information.

**README: Financial Analysis Tool Using Streamlit and Vnstock3**

### Introduction
This Streamlit-based tool provides financial analysis for a selected stock symbol using the `vnstock3` Python library. Users can enter a stock symbol and choose the number of years to analyze financial data, and the tool will fetch, process, and display key financial metrics for the specified stock. The tool is useful for investors seeking insights into a company's financial health and growth potential.

### Prerequisites
- Python installed locally.
- Required Python packages: `streamlit`, `vnstock3`, `pandas`, `numpy`. Install these packages using:
  ```sh
  pip install streamlit vnstock3 pandas numpy
  ```

### Main Features
1. **User Input and Controls**:
   - Users can enter a stock symbol (e.g., "ACB") via a text input field in the sidebar.
   - Users can also specify the number of years (5 to 10 years) for which they wish to analyze data, using a slider.

2. **Fetching Financial Data**:
   - The tool retrieves data from `vnstock3`, which accesses financial data from the `VCI` source.
   - Financial data is fetched for key components such as the balance sheet, income statement, cash flow statement, and financial ratios for the selected time range.

3. **Calculations**:
   - **ROE (Return on Equity)**, **ROIC (Return on Invested Capital)**, **Operating Cash Flow per Share (OCPS)**.
   - **CAGR (Compound Annual Growth Rate)**: Calculated for various metrics like revenue, shareholder equity, EPS (Earnings Per Share), BVPS (Book Value Per Share), and OCPS.
   - **MOS (Margin of Safety)**: Computed using future EPS projections and a discount rate.

4. **Output Tables**:
   - The tool generates several tables, such as "Financial Overview", "Present Value Summary", "MOS Market Cap", and "Pay Back Time".

### Key Data Outputs
- **Tỷ Lệ Tăng Trưởng Hàng Năm (CAGR)**: This table shows the yearly growth rate of key metrics over the selected time frame.
- **Financial Overview**: A summary table providing details on shareholder equity, revenue, EPS, etc.
- **Present Value Calculation**: Estimated value of the stock, considering a median P/E ratio and projected future growth rates.
- **MOS Market Cap**: Market cap based on the margin of safety.
- **Pay Back Time**: Projection for retained earnings over a period of 15 years.

### Tool Flow
1. **Input Stock Information**: The user enters the stock symbol and number of years to analyze.
2. **Fetch Financial Data**: The application fetches financial statements and calculates key indicators using `Vnstock`.
3. **Display Results**: It displays financial metrics, current values, MOS, and payback projections.

### Code Breakdown
1. **Imports and Initialization**: Imports relevant libraries (`streamlit`, `vnstock3`, `pandas`, `numpy`). Initializes a `Vnstock` object to access financial data.
2. **User Input Section**: Using Streamlit's sidebar, users can enter the stock symbol and choose the number of years for analysis.
3. **Data Fetching Function** (`fetch_stock_data`) is defined to retrieve data from balance sheets, income statements, cash flows, and ratios.
4. **Data Processing and Calculation**: Includes filtering data by year, computing important financial ratios, and calculating growth metrics.
5. **Display of Results**: The calculated data is rendered using `st.table()` to display it within the Streamlit app.

### How to Run the Tool
1. Save the code into a Python file (e.g., `financial_analysis_app.py`).
2. Run the file using the Streamlit command:
   ```sh
   streamlit run financial_analysis_app.py
   ```
3. Use the sidebar to input the stock symbol and select the number of years.
4. Click "Lấy dữ liệu" to fetch and analyze the stock data.

### Troubleshooting
- **Error Handling**: The `fetch_stock_data()` function has error handling to manage missing columns or data inconsistencies.
- **Data Availability**: Make sure that the `Vnstock` library has access to updated financial data for the selected stock symbol and years.

### Notes
- **P/E Median and CAGR Calculation**: The median P/E is calculated from historical data, while CAGR helps in estimating future growth. Values are then used to derive the present value and Margin of Safety (MOS).
- **Sources**: Financial data is sourced from `VCI` via the `vnstock3` library.

### Potential Enhancements
- **User Interface**: Add more interactivity such as graph-based visualizations to show trends of key metrics over the years.
- **Data Source Alternatives**: Extend the code to allow users to select from multiple data sources for more comprehensive analysis.
- **Input Validation**: Add validation checks for stock symbols to prevent errors.

### Conclusion
This tool serves as a practical way to perform fundamental analysis on Vietnamese stocks, leveraging a user-friendly Streamlit interface and combining data from different financial statements to provide insightful metrics.

For further customization or improvements, you can extend the calculations or change the analysis focus, based on additional requirements or data sources.



