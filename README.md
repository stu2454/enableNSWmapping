# EnableNSW to NDIS Crosswalk Analysis Tool

A comprehensive Streamlit application for automated crosswalk analysis between EnableNSW categories and NDIS Assistive Technology categories using rule-based and fuzzy matching algorithms.

## Features

- **Automated Mapping**: Rule-based and fuzzy string matching for EnableNSW to NDIS crosswalk
- **Interactive UI**: User-friendly Streamlit interface for data upload and analysis
- **Comprehensive Reporting**: Excel export with methodology, crosswalk table, and pivot summaries
- **Configurable Matching**: Adjustable confidence thresholds and matching parameters
- **Docker Support**: Easy deployment with Docker and docker-compose

## File Structure

```
enablensw-ndis-crosswalk/
│
├── app.py                 # Main Streamlit application
├── crosswalk.py          # Core crosswalk analysis logic
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker container configuration
├── docker-compose.yml   # Docker Compose setup
├── README.md           # This file
├── uploads/            # Directory for uploaded files (created automatically)
└── logs/              # Directory for application logs (created automatically)
```

## Data Format Requirements

### EnableNSW Categories File

Your EnableNSW categories file should be a CSV or Excel file with the following columns:

- `Category`: Main EnableNSW category (e.g., "Personal Mobility")
- `Subcategory`: Specific subcategory (e.g., "Manual Wheelchairs")
- `Description`: Optional detailed description

**Example:**

```csv
Category,Subcategory,Description
Personal Mobility,Manual Wheelchairs,Standard manual wheelchairs for indoor/outdoor use
Personal Mobility,Power Wheelchairs,Electric powered wheelchairs with joystick control
Communication,Speech Devices,Electronic speech generating devices and communication aids
```

### NDIS Code Guide File

Your NDIS Code Guide can be provided in CSV, Excel, or Word (DOCX) format with the following information:

**Required columns** (exact names may vary - the application will automatically detect):

- `Support_Item_Number` or `Item Number` or `Code`: NDIS support item code
- `Support_Item_Name` or `Item Name` or `Description`: Name of the support item

**Optional columns:**

- `Category`: NDIS category
- `Description`: Detailed description
- `Unit_Price` or `Price`: Price per unit

**Example CSV/Excel:**

```csv
Support_Item_Number,Support_Item_Name,Category,Description,Unit_Price
05_221336811_0113_1_2,Manual wheelchair - standard,Personal Mobility,Standard manual wheelchair for daily use,1500.00
05_221336811_0113_1_3,Power wheelchair - basic,Personal Mobility,Basic electric wheelchair with standard features,8500.00
```

**For DOCX files:**

- The document should contain one or more tables with support item information
- The first row of each table should contain column headers
- The application will automatically detect and extract the largest table
- Column names can vary (e.g., "Item Number" instead of "Support_Item_Number")
- The application will attempt to identify columns by analyzing content patterns

## Installation and Usage

### Option 1: Local Python Installation

1. **Clone or download the application files**

   ```bash
   mkdir enablensw-ndis-crosswalk
   cd enablensw-ndis-crosswalk
   # Copy all application files to this directory
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python -m venv crosswalk-env
   source crosswalk-env/bin/activate  # On Windows: crosswalk-env\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   streamlit run app.py
   ```

5. **Access the application**
   - Open your web browser and go to `http://localhost:8501`

### Option 2: Docker Installation

1. **Prerequisites**

   - Docker and Docker Compose installed on your system

2. **Build and run with Docker Compose**

   ```bash
   # In the directory containing docker-compose.yml
   docker-compose up --build
   ```

3. **Access the application**

   - Open your web browser and go to `http://localhost:8501`

4. **Stop the application**
   ```bash
   docker-compose down
   ```

### Option 3: Docker without Compose

1. **Build the Docker image**

   ```bash
   docker build -t enablensw-ndis-crosswalk .
   ```

2. **Run the container**
   ```bash
   docker run -p 8501:8501 enablensw-ndis-crosswalk
   ```

## How to Use the Application

1. **Upload Data Files**

   - Use the sidebar to upload your EnableNSW categories file (CSV or Excel)
   - Upload your NDIS Code Guide file (CSV, Excel, or Word DOCX)

2. **Configure Settings**

   - Adjust the fuzzy match confidence threshold (60-95%)
   - Choose whether to include repair/maintenance codes

3. **Run Analysis**

   - Click "🚀 Run Crosswalk Analysis" to start the automated mapping process
   - Wait for the analysis to complete (usually takes a few seconds to minutes depending on data size)

4. **Review Results**

   - **Crosswalk Table**: View detailed mappings with filters by category and confidence level
   - **Pivot Summary**: See summary statistics and mapping success rates
   - **Download**: Generate and download comprehensive Excel report

5. **Download Excel Report**
   - Click "📥 Generate Excel Report" to create a comprehensive report
   - The Excel file contains three sheets:
     - **Introduction**: Methodology and analysis metadata
     - **Crosswalk Table**: Complete mapping results
     - **Pivot Summary**: Summary statistics by category

## Understanding the Results

### Confidence Levels

- **Direct line item (High confidence)**: Exact matches or rule-based mappings with high certainty
- **Best-fit (Functional equivalent)**: Good fuzzy matches that are functionally similar
- **No clear equivalent (Review required)**: Low confidence matches that need manual review

### Matching Methods

- **Rule-based**: Uses predefined mapping rules for known equipment categories
- **Fuzzy matching**: Uses approximate string matching algorithms for similarity detection

## Configuration Options

### Confidence Threshold

- Range: 60-95%
- Default: 80%
- Lower values = more matches but potentially less accurate
- Higher values = fewer matches but higher accuracy

### Repair/Maintenance Codes

- When enabled, the system attempts to find associated repair and maintenance codes for each mapped item
- Useful for comprehensive cost planning

## Troubleshooting

### Common Issues

1. **File Format Issues**

   - Ensure files are in CSV, Excel, or DOCX format
   - For EnableNSW: Check that required columns exist (Category, Subcategory)
   - For NDIS: The application will automatically detect column variations, but ensure tables contain support item codes and names
   - For DOCX files: Ensure data is in table format (not just text)
   - Verify file size is under the upload limit (200MB by default)

2. **Low Mapping Success Rate**

   - Try lowering the confidence threshold
   - Check data quality and consistency
   - Review the mapping rules in `crosswalk.py` to add custom rules for your data

3. **Docker Issues**

   - Ensure Docker and Docker Compose are properly installed
   - Check that port 8501 is not already in use
   - Review Docker logs: `docker-compose logs`

4. **Performance Issues**
   - Large datasets may take longer to process
   - Consider reducing the dataset size for testing
   - Monitor system resources during analysis

### Getting Help

For technical issues or questions:

1. Check the application logs in the Streamlit interface
2. Review the console output when running locally
3. For Docker deployments, check container logs: `docker logs enablensw-ndis-crosswalk`

## Advanced Configuration

### Customizing Mapping Rules

To add custom mapping rules, edit the `mapping_rules` dictionary in `crosswalk.py`:

```python
self.mapping_rules = {
    'custom_equipment': {
        'keywords': ['keyword1', 'keyword2'],
        'ndis_category': 'Target NDIS Category',
        'confidence': 'Direct line item (High confidence)'
    }
}
```

### Environment Variables

For Docker deployments, you can customize the following environment variables in `docker-compose.yml`:

- `STREAMLIT_SERVER_PORT`: Port for the Streamlit server (default: 8501)
- `STREAMLIT_SERVER_MAX_UPLOAD_SIZE`: Maximum file upload size in MB (default: 200)

## Security Considerations

- This application is designed for internal use and should not be exposed directly to the internet without proper security measures
- Uploaded files are processed in memory and not permanently stored by default
- Consider implementing authentication if deploying in a multi-user environment

## License and Disclaimer

This tool is provided for government policy analysis purposes. Users are responsible for:

- Verifying the accuracy of automated mappings
- Conducting manual review of "Review required" items
- Ensuring compliance with relevant policies and procedures
- Validating NDIS pricing and availability independently

The automated matching is intended to assist human analysis, not replace professional judgment.
