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
    """Extract table data from DOCX file"""
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
        
        # Find tables in the document
        tables_data = []
        
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
            
            if table_data:
                # Convert to DataFrame
                if len(table_data) > 1:
                    # Use first row as headers
                    headers = table_data[0]
                    data_rows = table_data[1:]
                    
                    # Create DataFrame
                    df = pd.DataFrame(data_rows, columns=headers)
                    
                    # Clean column names
                    df.columns = [col.strip() for col in df.columns]
                    
                    tables_data.append({
                        'table_index': table_idx,
                        'dataframe': df,
                        'row_count': len(df)
                    })
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        if not tables_data:
            st.error("No tables found in the DOCX file")
            return None
        
        # If multiple tables found, let user choose or use the largest one
        if len(tables_data) > 1:
            st.info(f"Found {len(tables_data)} tables in the DOCX file. Using the largest table.")
            # Use the table with the most rows
            selected_table = max(tables_data, key=lambda x: x['row_count'])
        else:
            selected_table = tables_data[0]
        
        df = selected_table['dataframe']
        
        # Show preview to user
        with st.expander(f"📋 DOCX Table Preview (Table {selected_table['table_index'] + 1})"):
            st.write(f"**Rows:** {len(df)}, **Columns:** {len(df.columns)}")
            st.write("**Column Names:**", list(df.columns))
            st.dataframe(df.head(), use_container_width=True)
        
        return df
        
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