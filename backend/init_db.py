import os
import psycopg2
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

def reset_colony_resources():
    # The purpose of this function is to update the database to its original resources using the source file

    data_file_path = os.getenv("COLONY_DATA_FILE", "raw_data/data.xlsx")
    print(f"Reading resources from {data_file_path}")

    conn = psycopg2.connect(
        dbname = os.getenv("DB_NAME", "mars_colony").strip(" '\"()"),
        user = os.getenv("DB_USER", "postgres").strip(" '\"()"),
        password = os.getenv("DB_PASSWORD", "").strip(" \"()"),
        host = os.getenv("DB_HOST", "localhost").strip(" \"()"),
        port = int(os.getenv("DB_PORT", "5432").strip(" \"()"))
    )
    cur = conn.cursor()

    try:

        excel_file = pd.ExcelFile(data_file_path)

    except Exception as e:
        print(f"Could not read file {e}. Falling back to baseline")


    try:

        print("Reseting Mars colony resources")

        if 'Resources' in excel_file.sheet_names:
            df_res = pd.read_excel(excel_file, sheet_name="Resources")

            if "Description" in df_res.columns and "MinimumUnitsFor100People" in df_res.columns:

                for _, row in df_res.iterrows():
                    description = str(row['Description']).strip()
                    min_units = float(row['MinimumUnitsFor100People'])

                    cur.execute(
                        """
                            UPDATE Resources 
                            SET currentstocklbs = %s
                            WHERE description ILIKE %s;
                        """, (min_units, f"%{description}%")
                    )
                print("Resources have been updated succesffuly!")

        if "Nutritional" in excel_file.sheet_names:

            df_nut = pd.read_excel(excel_file, sheet_name="Nutritional")

            desc_col = next((c for c in df_nut.columns if 'desc' in c.lower()), 'Description')
            stock_col = next((c for c in df_nut.columns if 'stock' in c.lower() or 'lbs' in c.lower()), 'StockLbs')

            if desc_col in df_nut.columns and stock_col in df_nut.columns:
                for _, row in df_nut.iterrows():
                    desc = str(row[desc_col]).strip()
                    stock_lbs = float(row[stock_col])

                    cur.execute("""
                        UPDATE Nutritional 
                        SET stocklbs = %s 
                        WHERE description ILIKE %s;
                    """, (stock_lbs, f"%{desc}%"))
                print("Nutritionals have been updated successfully!")

        else: 
            cur.execute("UPDATE Resources SET currentstocklbs = 1000.0;")

            cur.execute(
                """
                UPDATE Nutritional 
                SET stocklbs = 11000.0
                """
            )

        conn.commit()
        print("Colony resources have been updated!")

    except Exception as e:
        conn.rollback()
        print(f"Failed to update resources: {e}")

    finally: 
        cur.close()
        conn.close()


if __name__=="__main__":
    reset_colony_resources() 