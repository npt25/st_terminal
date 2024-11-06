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

