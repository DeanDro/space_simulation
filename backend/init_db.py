import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def reset_colony_resources():
    # The purpose of this function is to update the database to its original resources

    conn = psycopg2.connect(
        dbname = os.getenv("DB_NAME", "mars_colony").strip(" '\"()"),
        user = os.getenv("DB_USER", "postgres").strip(" '\"()"),
        password = os.getenv("DB_PASSWORD", "").strip(" \"()"),
        host = os.getenv("DB_HOST", "localhost").strip(" \"()"),
        port = int(os.getenv("DB_PORT", "5432")).strip(" \"()")
    )
    cur = conn.cursor()

    try:
        print("Reseting Mars colony resources baselined on enough resources for 100 people for 6 months....")

        cur.execute(
            """
            UPDATE Resources 
            SET currentstocklbs = CASE
                WHEN description ILIKE '%water%' THEN 25000.0
                WHEN description ILIKE '%Oxygen%' THEN 12500.0
                ELSE 500.0
            END;
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