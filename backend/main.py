import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv


# loading the .env file with environment variables
load_dotenv()

app = FastAPI(
    title="Mars Colony Simulation API",
    version="1.0.0",
    description="Backend engine for tracking colony information"
)

# Enabling CORS so frontend can talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_db_connection():

    db_name=os.getenv("DB_NAME").strip(" '\"()")
    db_user=os.getenv("DB_USER").strip(" '\"()")
    db_password=os.getenv("DB_PASSWORD").strip(" '\"()")
    db_host=os.getenv("DB_HOST", "localhost").strip(" '\"()")
    db_port=os.getenv("DB_PORT", "5432").strip(" '\"()")

    if not all([db_name, db_user, db_password]):
        raise HTTPException(
            status_code= 500,
            detail= "Database environment variables are missing or are wrong"
        )

    try:
        conn = psycopg2.connect(
            dbname = db_name,
            user = db_user,
            password = db_password,
            host = db_host,
            port = int(db_port),
            cursor_factory= RealDictCursor
        )

        return conn 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error {str(e)}")


@app.get("/")
def read_root():
    return {"message": "Mars Colony Simulation API is online"}

@app.get("/api/colony/status")
def get_colony_status():
    conn = get_db_connection()
    curr = conn.cursor()

    # Get some general status updates for the colony
    try:
        curr.execute("SELECT COUNT(*) AS total_crew FROM Astronauts;")
        crew_count = curr.fetchone()["total_crew"]

        curr.execute("SELECT * FROM Habitat;")
        habitats = curr.fetchall()

        curr.execute("SELECT SUM(stocklbs) as total_food_stock FROM Nutritional;")
        food_stock = curr.fetchone()["total_food_stock"]

        curr.execute("SELECT description, currentstocklbs, purpose FROM Resources;")
        resources = curr.fetchall()

        return {
            "colony_status": "Operational",
            "active_crew_members": crew_count,
            "habitats": habitats,
            "total_food_stock_lbs": food_stock,
            "resources": resources
        }

    finally:
        curr.close()
        conn.close()

@app.post("/api/colony/simulation-tick")
def simulate_tick(days: int=1):
    """
    This function simulates the passing of time by 1 day, it calculates resources consumption 
    and updates inventory
    """

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # aggregate total daily consumption
        cur.execute("""
            SELECT 
                SUM(h.avgwaterconsumptionlt) as total_daily_water,
                SUM(h.avgoxygenconsumptionlbs) as total_daily_oxygen,
                SUM(h.avgdailycalories) as total_daily_calories,
                COUNT(a.pk) as total_crew
            FROM Astronauts a
            JOIN HealthRecords h ON a.fkhealth = h.pk; 
        """)
        metrics = cur.fetchone()

        if not metrics or metrics["total_crew"] == 0:
            raise HTTPException(status_code=400, detail="No active crew found")

        # Daily consumption of resources 
        consumed_water = float(metrics["total_daily_water"] or 0) * days
        consumed_oxygen = float(metrics["total_daily_oxygen"] or 0) * days
        consumed_calories = float(metrics["total_daily_calories"] or 0) * days

        # deduct calculated consumed resources from available resources 
        food_depletion_lbs = consumed_calories * 0.0005 # weight factor per calories
        cur.execute("""
            UPDATE Nutritional
            SET stocklbs = GREATEST(0, stocklbs - %s);
        """, (food_depletion_lbs,))

        # Fetch updated inventory
        cur.execute("SELECT SUM(stocklbs) AS total_food_stock FROM Nutritional;")
        updated_food = cur.fetchone()["total_food_stock"]

        conn.commit()

        # Return report 
        return {
            "status": "Success",
            "message": f"Simulation advanced by {days} Sol(s).",
            "telemetry": {
                "active_crew": metrics["total_crew"],
                "sols_advanced": days,
                "consumption": {
                    "water_liters": round(consumed_water, 2),
                    "oxygen_lbs": round(consumed_oxygen, 2),
                    "calories_burned": round(consumed_calories, 2)
                },
                "inventory": {
                    "total_food_stock_lbs": round(updated_food, 2) if updated_food else 0
                },
                "colony_alert": "WARNING: Low food reserves detected!" if updated_food and updated_food < 5000 else "All systems nominal."
            }
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Simulation tick failed: {str(e)}")
    finally:
        cur.close()
        conn.close()