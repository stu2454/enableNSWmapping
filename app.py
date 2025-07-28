import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os
from crosswalk import CrosswalkAnalyzer

# Configure Streamlit page
st.set_page_config(
    page_title="EnableNSW to NDIS Crosswalk Analysis",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🔗 EnableNSW to NDIS Crosswalk Analysis")
    st.markdown("""
    This application performs automated crosswalk analysis between EnableNSW categories 
    and NDIS Assistive Technology categories using rule-based and fuzzy matching algorithms.
    """)
    
    # Initialize session state
    if 'crosswalk_results' not in st.session_state:
        st.session_state.crosswalk_results = None
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = CrosswalkAnalyzer()
    
    # Sidebar for file uploads
    st.sidebar.header("📁 Data Input")
    
    # EnableNSW categories upload
    st.sidebar.subheader("1. EnableNSW Categories")
    enable_nsw_file = st.sidebar.file_uploader(
        "Upload EnableNSW categories file",
        type=['csv', 'xlsx'],
        help="CSV or Excel file containing EnableNSW categories and subcategories"
    )
    
    # NDIS Code Guide upload
    st.sidebar.subheader("2. NDIS Code Guide")
    ndis_file = st.sidebar.file_uploader(
        "Upload NDIS AT Code Guide",
        type=['csv', 'xlsx', 'docx'],
        help="NDIS Assistive Technology Code Guide 2025-26 v1.0 (CSV, Excel, or Word document)"
    )
    
    # Configuration options
    st.sidebar.header("⚙️ Configuration")
    
    confidence_threshold = st.sidebar.slider(
        "Fuzzy Match Confidence Threshold",
        min_value=60,
        max_value=95,
        value=80,
        help="Minimum confidence score for fuzzy matching (lower = more matches)"
    )
    
    include_repair_codes = st.sidebar.checkbox(
        "Include Repair/Maintenance Codes",
        value=True,
        help="Include repair and maintenance codes in the mapping"
    )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📊 Analysis Results")
        
        # Check if both files are uploaded
        if enable_nsw_file and ndis_file:
            
            # Run analysis button
            if st.button("🚀 Run Crosswalk Analysis", type="primary"):
                with st.spinner("Processing crosswalk analysis..."):
                    try:
                        # Load data
                        enable_nsw_df = load_file(enable_nsw_file)
                        ndis_df = load_file(ndis_file)
                        
                        # Validate data
                        if validate_data(enable_nsw_df, ndis_df):
                            # Configure analyzer
                            st.session_state.analyzer.confidence_threshold = confidence_threshold
                            st.session_state.analyzer.include_repair_codes = include_repair_codes
                            
                            # Run crosswalk
                            results = st.session_state.analyzer.run_crosswalk(
                                enable_nsw_df, 
                                ndis_df
                            )
                            
                            st.session_state.crosswalk_results = results
                            st.success("✅ Crosswalk analysis completed successfully!")
                            
                    except Exception as e:
                        st.error(f"❌ Error during analysis: {str(e)}")
            
            # Display results if available
            if st.session_state.crosswalk_results:
                display_results(st.session_state.crosswalk_results)
                
        else:
            st.info("👆 Please upload both EnableNSW categories and NDIS Code Guide files to begin analysis.")
            
            # Show sample data format
            with st.expander("📋 Expected Data Format"):
                st.subheader("EnableNSW Categories Format")
                st.code("""
Category,Subcategory,Description
Personal Mobility,Manual Wheelchairs,Standard manual wheelchairs
Personal Mobility,Power Wheelchairs,Electric powered wheelchairs
Communication,Speech Devices,Electronic speech generating devices
                """)
                
                st.subheader("NDIS Code Guide Format")
                st.code("""
Support_Item_Number,Support_Item_Name,Category,Description,Unit_Price
05_221336811_0113_1_2,Manual wheelchair - standard,Personal Mobility,Standard manual wheelchair,1500.00

OR for DOCX files:
- Document should contain tables with support item information
- First row should be headers
- Application will automatically detect and extract table data
                """)
    
    with col2:
        st.header("📈 Statistics")
        
        if st.session_state.crosswalk_results:
            show_statistics(st.session_state.crosswalk_results)
        else:
            st.info("Statistics will appear after running the analysis.")

def load_file(uploaded_file):
    """Load CSV, Excel, or DOCX file into DataFrame"""
    try:
        if uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.docx'):
            return load_docx_file(uploaded_file)
        else:
            st.error(f"Unsupported file format: {uploaded_file.name}")
            return None
    except Exception as e:
        st.error(f"Error loading file {uploaded_file.name}: {str(e)}")
        return None

def load_docx_file(uploaded_file):
    """Extract and combine all table data from DOCX file"""
    from docx import Document
    
    # Save uploaded file temporarily
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    
    try:
        # Load the document
        doc = Document(tmp_file_path)
        
        # Find all tables in the document
        all_tables_data = []
        combined_data = []
        
        for table_idx, table in enumerate(doc.tables):
            # Extract table data
            table_data = []
            
            for row_idx, row in enumerate(table.rows):
                row_data = []
                for cell in row.cells:
                    # Clean cell text
                    cell_text = cell.text.strip().replace('\n', ' ').replace('\r', '')
                    row_data.append(cell_text)
                
                table_data.append(row_data)
            
            if table_data and len(table_data) > 1:  # Need at least header + 1 data row
                # Use first row as headers
                headers = [col.strip() for col in table_data[0]]
                data_rows = table_data[1:]
                
                # Filter out empty rows
                data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]
                
                if data_rows:  # Only add if we have actual data
                    # Create DataFrame for this table
                    df = pd.DataFrame(data_rows, columns=headers)
                    
                    # Clean empty columns
                    df = df.loc[:, df.columns != '']  # Remove columns with empty names
                    df = df.dropna(how='all', axis=1)  # Remove columns that are all NaN
                    
                    all_tables_data.append({
                        'table_index': table_idx,
                        'dataframe': df,
                        'row_count': len(df),
                        'headers': headers
                    })
                    
                    # Add table identifier column to track source
                    df['Source_Table'] = f"Table_{table_idx + 1}"
                    combined_data.append(df)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        if not all_tables_data:
            st.error("No valid tables found in the DOCX file")
            return None
        
        # Combine all tables
        try:
            # Filter tables that contain NDIS codes
            valid_tables = []
            for table_data in all_tables_data:
                df = table_data['dataframe']
                # Check if any column contains NDIS code patterns (e.g., XX_XXXXXXXX_XXXX_X_X)
                has_ndis_codes = any(
                    df[col].astype(str).str.match(r'^\d+_\d+.*').any() 
                    for col in df.columns
                )
                if has_ndis_codes:
                    valid_tables.append(table_data)
            
            if not valid_tables:
                # Fallback: return the largest table
                largest_table = max(all_tables_data, key=lambda x: x['row_count'])
                st.warning(f"No tables with NDIS codes found. Using largest table (Table {largest_table['table_index'] + 1}) with {largest_table['row_count']} rows")
                return largest_table['dataframe']
            
            all_tables_data = valid_tables
            
            # Find common columns across valid tables
            all_columns = set()
            for table_data in valid_tables:
                all_columns.update(table_data['dataframe'].columns)
            
            # Remove Source_Table from common columns check
            common_columns = all_columns.copy()
            common_columns.discard('Source_Table')
            
            # Try to standardize column names across tables
            standardized_tables = []
            for table_data in all_tables_data:
                df = table_data['dataframe'].copy()
                
                # Add missing columns with empty values
                for col in common_columns:
                    if col not in df.columns:
                        df[col] = ''
                
                # Reorder columns consistently
                column_order = sorted(common_columns) + ['Source_Table']
                df = df.reindex(columns=column_order, fill_value='')
                
                standardized_tables.append(df)
            
            # Combine all tables
            combined_df = pd.concat(standardized_tables, ignore_index=True, sort=False)
            
            # Show summary to user
            with st.expander(f"📋 DOCX Tables Summary - Combined {len(all_tables_data)} tables"):
                st.write(f"**Total Tables Found:** {len(all_tables_data)}")
                st.write(f"**Total Combined Rows:** {len(combined_df)}")
                st.write(f"**Combined Columns:** {list(combined_df.columns)}")
                
                # Show individual table info
                for i, table_data in enumerate(all_tables_data):
                    st.write(f"**Table {i + 1}:** {table_data['row_count']} rows, Columns: {table_data['headers']}")
                
                # Show preview of combined data
                st.write("**Combined Data Preview:**")
                st.dataframe(combined_df.head(10), use_container_width=True)
            
            return combined_df
            
        except Exception as e:
            st.error(f"Error combining tables: {str(e)}")
            # Fallback: return the largest table
            largest_table = max(all_tables_data, key=lambda x: x['row_count'])
            st.warning(f"Falling back to largest table (Table {largest_table['table_index'] + 1}) with {largest_table['row_count']} rows")
            return largest_table['dataframe']
        
    except Exception as e:
        # Clean up temporary file
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        raise e

def validate_data(enable_nsw_df, ndis_df):
    """Validate that required columns exist in the data"""
    
    # Check EnableNSW data
    required_enable_cols = ['Category', 'Subcategory']
    missing_enable_cols = [col for col in required_enable_cols if col not in enable_nsw_df.columns]
    
    if missing_enable_cols:
        st.error(f"❌ EnableNSW file missing required columns: {missing_enable_cols}")
        return False
    
    # For NDIS data, validation is now handled in crosswalk.py
    # Just check that we have some data
    if ndis_df is None or len(ndis_df) == 0:
        st.error("❌ NDIS file appears to be empty or invalid")
        return False
    
    return True

def display_results(results):
    """Display crosswalk results in tabs"""
    
    tab1, tab2, tab3 = st.tabs(["🔗 Crosswalk Table", "📊 Pivot Summary", "📥 Download"])
    
    with tab1:
        st.subheader("Crosswalk Mapping Results")
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            categories = ['All'] + list(results['crosswalk']['EnableNSW_Category'].unique())
            selected_category = st.selectbox("Filter by EnableNSW Category", categories)
        
        with col2:
            confidence_levels = ['All'] + list(results['crosswalk']['Mapping_Confidence'].unique())
            selected_confidence = st.selectbox("Filter by Confidence Level", confidence_levels)
        
        with col3:
            has_mapping = st.selectbox("Show mappings", ['All', 'With NDIS mapping', 'Without NDIS mapping'])
        
        # Apply filters
        filtered_df = results['crosswalk'].copy()
        
        if selected_category != 'All':
            filtered_df = filtered_df[filtered_df['EnableNSW_Category'] == selected_category]
        
        if selected_confidence != 'All':
            filtered_df = filtered_df[filtered_df['Mapping_Confidence'] == selected_confidence]
        
        if has_mapping == 'With NDIS mapping':
            filtered_df = filtered_df[filtered_df['NDIS_Support_Item_Number'].notna()]
        elif has_mapping == 'Without NDIS mapping':
            filtered_df = filtered_df[filtered_df['NDIS_Support_Item_Number'].isna()]
        
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )
        
        st.info(f"Showing {len(filtered_df)} of {len(results['crosswalk'])} mappings")
    
    with tab2:
        st.subheader("Summary Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Mapping by EnableNSW Category**")
            st.dataframe(
                results['pivot_summary'],
                use_container_width=True
            )
        
        with col2:
            st.write("**Confidence Level Distribution**")
            confidence_dist = results['crosswalk']['Mapping_Confidence'].value_counts()
            st.bar_chart(confidence_dist)
    
    with tab3:
        st.subheader("Download Results")
        
        if st.button("📥 Generate Excel Report", type="primary"):
            with st.spinner("Generating Excel report..."):
                try:
                    # Generate Excel file
                    excel_buffer = st.session_state.analyzer.generate_excel_report(results)
                    
                    # Prepare download
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"EnableNSW_NDIS_Crosswalk_{timestamp}.xlsx"
                    
                    st.download_button(
                        label=f"📥 Download {filename}",
                        data=excel_buffer.getvalue(),
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    st.success("✅ Excel report generated successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error generating Excel report: {str(e)}")

def show_statistics(results):
    """Display key statistics in the sidebar"""
    
    total_subcategories = len(results['crosswalk'])
    mapped_items = len(results['crosswalk'][results['crosswalk']['NDIS_Support_Item_Number'].notna()])
    
    st.metric("Total EnableNSW Subcategories", total_subcategories)
    st.metric("Successfully Mapped", mapped_items)
    st.metric("Mapping Success Rate", f"{mapped_items/total_subcategories*100:.1f}%")
    
    # Confidence level breakdown
    st.subheader("Confidence Levels")
    confidence_counts = results['crosswalk']['Mapping_Confidence'].value_counts()
    
    for confidence, count in confidence_counts.items():
        percentage = count / total_subcategories * 100
        st.write(f"**{confidence}**: {count} ({percentage:.1f}%)")

if __name__ == "__main__":
    main()