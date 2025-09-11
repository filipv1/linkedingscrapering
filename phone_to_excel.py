import pandas as pd
import csv

def csv_to_excel(csv_file):
    """Convert CSV to Excel with proper Czech encoding"""
    
    # Read CSV with UTF-8
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
    except:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
        except:
            df = pd.read_csv(csv_file, encoding='cp1250')
    
    # Output Excel file
    excel_file = csv_file.replace('.csv', '.xlsx')
    
    print(f"Converting {csv_file} → {excel_file}")
    print(f"Rows: {len(df)}")
    
    # Save to Excel with proper formatting
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Telefony', index=False)
        
        # Format worksheet
        worksheet = writer.sheets['Telefony']
        
        # Auto-width columns
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
                    
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Format header
        for cell in worksheet[1]:
            cell.font = cell.font.copy(bold=True)
            
    print(f"✅ Excel saved: {excel_file}")
    print("Czech characters should display correctly in Excel!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python phone_to_excel.py <csv_file>")
        print("Example: python phone_to_excel.py ckait_stavbyvedouci_manual_phones_parallel.csv")
    else:
        csv_to_excel(sys.argv[1])