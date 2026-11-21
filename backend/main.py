import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load .env before importing init_db so DB env vars are ready
load_dotenv()

from .init_db import reset_colony_resources


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically reset resources to baseline on startup
    try:
        reset_colony_resources()
    except Exception as e:
        print(f"Failed to reset resources: {e}")
    yield


app = FastAPI(
    title="Mars Colony Simulation API",
    version="1.0.0",
    description="Backend engine for tracking colony information",
    lifespan=lifespan,
)

# Enable CORS so frontend can talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    db_name = (os.getenv("DB_NAME") or "").strip(" '\"()")
    db_user = (os.getenv("DB_USER") or "").strip(" '\"()")
    db_password = (os.getenv("DB_PASSWORD") or "").strip(" '\"()")
    db_host = (os.getenv("DB_HOST") or "localhost").strip(" '\"()")
    db_port = (os.getenv("DB_PORT") or "5432").strip(" '\"()")

    if not all([db_name, db_user, db_password]):
        raise HTTPException(
            status_code=500,
            detail="Database environment variables are missing or wrong",
        )

    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=int(db_port),
            cursor_factory=RealDictCursor,
        )
        return conn
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection error: {str(e)}"
        )


@app.get("/")
def read_root():
    return {"message": "Mars Colony Simulation API is online"}


@app.get("/api/colony/status")
def get_colony_status():
    conn = get_db_connection()
    curr = conn.cursor()

    try:
        curr.execute("SELECT COUNT(*) AS total_crew FROM Astronauts;")
        crew_row = curr.fetchone()
        crew_count = crew_row["total_crew"] if crew_row else 0

        curr.execute("SELECT * FROM Habitat;")
        habitats = curr.fetchall()

        # Fetch all astronauts with health and profession details
        curr.execute(
            """
            SELECT a.pk, a.firstname, a.lastname, p.description, a.fkfamily,
                   h.avgwaterconsumptionlt, h.avgoxygenconsumptionlbs, h.avgdailycalories
            FROM Astronauts a
            LEFT JOIN HealthRecords h ON a.fkhealth = h.pk
            LEFT JOIN Professions p ON a.fkprofession = p.pk;
            """
        )
        astronauts = curr.fetchall()

        curr.execute("SELECT SUM(stocklbs) AS total_food_stock FROM Nutritional;")
        food_row = curr.fetchone()
        food_stock = food_row["total_food_stock"] if food_row else 0

        # Population per habitat (using dictionary keys from RealDictCursor)
        curr.execute(
            """
            SELECT fkfamily AS habitat_id, COUNT(*) AS crew_count
            FROM Astronauts
            GROUP BY fkfamily;
            """
        )
        crew_by_habitat = {
            r["habitat_id"]: r["crew_count"] for r in curr.fetchall()
        }

        curr.execute("SELECT description, currentstocklbs, purpose FROM Resources;")
        resources = curr.fetchall()

        return {
            "colony_status": "Operational",
            "active_crew_members": crew_count,
            "total_population": crew_count,
            "habitats": habitats,
            "astronauts": astronauts,
            "total_food_stock_lbs": food_stock,
            "resources": resources,
            "crew_by_habitat": crew_by_habitat,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch colony status: {str(e)}"
        )
    finally:
        curr.close()
        conn.close()


@app.post("/api/colony/simulation-tick")
def simulate_tick(days: int = 1):
    """
    Simulate the pass of 18 months in the colony which is the time for the next mission from earth.
    Assumptions: 
    - For the first 3 years after the first colony, each mission will have 100 people, 
    - Between the first 3 and 5 years, each mission will have 1000 people, 
    - After first 5 years, each mission will send 10000 people, 
    - Average birth rate at 0.06
    - Average death rate at 0.01
    - Average marriage rate at 0.14
    - Only first 2 missions will only include couples, after that only half of people will be couples
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                SUM(h.avgwaterconsumptionlt) AS total_daily_water,
                SUM(h.avgoxygenconsumptionlbs) AS total_daily_oxygen,
                SUM(h.avgdailycalories) AS total_daily_calories,
                COUNT(a.pk) AS total_crew
            FROM Astronauts a
            JOIN HealthRecords h ON a.fkhealth = h.pk;
            """
        )
        metrics = cur.fetchone()

        if not metrics or metrics["total_crew"] == 0:
            raise HTTPException(status_code=400, detail="No active crew found")

        consumed_water = float(metrics["total_daily_water"] or 0) * days
        consumed_oxygen = float(metrics["total_daily_oxygen"] or 0) * days
        consumed_calories = float(metrics["total_daily_calories"] or 0) * days
        food_depletion_lbs = consumed_calories * 0.0005

        cur.execute(
            """
            UPDATE Nutritional
            SET stocklbs = GREATEST(0, stocklbs - %s);
            """,
            (food_depletion_lbs,),
        )

        cur.execute("SELECT SUM(stocklbs) AS total_food_stock FROM Nutritional;")
        updated_food = cur.fetchone()["total_food_stock"]

        conn.commit()

        return {
            "status": "Success",
            "message": f"Simulation advanced by {days} Sol(s).",
            "telemetry": {
                "active_crew": metrics["total_crew"],
                "sols_advanced": days,
                "consumption": {
                    "water_liters": round(consumed_water, 2),
                    "oxygen_lbs": round(consumed_oxygen, 2),
                    "calories_burned": round(consumed_calories, 2),
                },
                "inventory": {
                    "total_food_stock_lbs": round(updated_food, 2) if updated_food else 0
                },
                "colony_alert": (
                    "WARNING: Low food reserves detected!"
                    if updated_food and updated_food < 5000
                    else "All systems nominal."
                ),
            },
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500, detail=f"Simulation tick failed: {str(e)}"
        )
    finally:
        cur.close()
        conn.close()