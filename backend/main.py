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

    db_name=os.getenv("DB_NAME"),
    db_user=os.getenv("DB_USER"),
    db_password=os.getenv("DB_PASSWORD"),
    db_host=os.getenv("DB_HOST", "localhost"),
    db_port=os.getenv("DB_PORT", "5432")

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
            port = db_port,
            cursor_factory= RealDictCursor
        )

        return conn 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error {str(e)}")


@app.get("/")
def read_root():
    return {"message": "Mars Colony Simulation API is online"}

@app.get("api/colony/status")
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
