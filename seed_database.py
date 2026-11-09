import pandas as pd
import os
import psycopg2
from dotenv import load_dotenv

# loading variables from local environment
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

# Checking login gredentials 
print("DB_USER:", os.getenv("DB_USER"))
print("DB_PASSWORD:", os.getenv("DB_PASSWORD"))

def seed_database():
    excel_path = 'raw_data/data.xlsx'
    if not os.path.exists(excel_path):
        print(f"Error: could not find the {excel_path} in the current directory")
        return

    xls = pd.ExcelFile(excel_path)
    print(f"Found Excel file at path: {excel_path}")

    # Establishing database connection securely 
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        print("Creating schema and resetting tables...")
        # Drop and create schemas in correct order 
        cur.execute("""
            DROP TABLE IF EXISTS Astronauts CASCADE;
            DROP TABLE IF EXISTS Habitat CASCADE;
            DROP TABLE IF EXISTS Resources CASCADE;
            DROP TABLE IF EXISTS Nutritional CASCADE;
            DROP TABLE IF EXISTS Logistics CASCADE;
            DROP TABLE IF EXISTS Category CASCADE;
            DROP TABLE IF EXISTS HealthRecords CASCADE;
            DROP TABLE IF EXISTS Psychology CASCADE;
            DROP TABLE IF EXISTS Professions CASCADE;
            DROP TABLE IF EXISTS Family CASCADE;
            DROP TABLE IF EXISTS Trip CASCADE;

            CREATE TABLE Trip (
                Pk INT PRIMARY KEY,
                Departure VARCHAR(100) NOT NULL,
                Arrival VARCHAR(100) NOT NULL,
                DateDeparture TIMESTAMP NOT NULL,
                DateArrival TIMESTAMP NOT NULL,
                SpaceshipName VARCHAR(100) NOT NULL
            );

            CREATE TABLE Family (
                Pk INT PRIMARY KEY,
                NumberMembers INT NOT NULL
            );

            CREATE TABLE Professions (
                Pk INT PRIMARY KEY,
                Description VARCHAR(100) NOT NULL,
                Category VARCHAR(100) NOT NULL,
                Criticality INT NOT NULL
            );

            CREATE TABLE HealthRecords (
                Pk INT PRIMARY KEY,
                NumberInjuries INT NOT NULL,
                PercTotalRecovery INT NOT NULL,
                ExerciseCompliance INT NOT NULL,
                AvgEnergyKj INT NOT NULL,
                AvgDailyCalories INT NOT NULL,
                WeightLbs INT NOT NULL,
                HeightFt FLOAT NOT NULL,
                Gender VARCHAR(10) NOT NULL,
                AvgOxygenConsumptionLbs FLOAT NOT NULL,
                AvgWaterConsumptionLt FLOAT NOT NULL,
                DateBirth VARCHAR(20) NOT NULL,
                DateDeath TIMESTAMP NULL
            );

            CREATE TABLE Psychology (
                Pk INT PRIMARY KEY,
                SleepRank INT NOT NULL,
                Mood INT NOT NULL,
                Socialization INT NOT NULL,
                CognitivePerformance INT NOT NULL,
                NumberOfAggrevatedEvents INT NOT NULL
            );

            CREATE TABLE Astronauts (
                Pk INT PRIMARY KEY,
                FirstName VARCHAR(50) NOT NULL,
                LastName VARCHAR(50) NOT NULL,
                FkTrip INT REFERENCES Trip(Pk),
                FkProfession INT REFERENCES Professions(Pk),
                FkFamily INT REFERENCES Family(Pk),
                FkHealth INT REFERENCES HealthRecords(Pk),
                FkPsychology INT REFERENCES Psychology(Pk),
                FkPrimaryOccupation INT REFERENCES Professions(Pk)
            );

            CREATE TABLE Habitat (
                Pk INT PRIMARY KEY,
                FkFamily INT REFERENCES Family(Pk),
                Location VARCHAR(100) NOT NULL,
                StructuralIntegrity INT NOT NULL,
                SafetyStatus BOOLEAN NOT NULL,
                EnergySupply BOOLEAN NOT NULL,
                OxygenSupply BOOLEAN NOT NULL,
                WaterSupply BOOLEAN NOT NULL
            );

            CREATE TABLE Logistics (
                Pk INT PRIMARY KEY,
                Planet VARCHAR(50) NOT NULL,
                TransitDays INT NOT NULL,
                MinimumQuantity INT NOT NULL,
                TransportationCostPerLbs INT NOT NULL
            );

            CREATE TABLE Category (
                Pk INT PRIMARY KEY,
                Description VARCHAR(100) NOT NULL,
                Classification INT NOT NULL
            );

            CREATE TABLE Resources (
                Pk INT PRIMARY KEY,
                Description VARCHAR(255) NOT NULL,
                Purpose TEXT NOT NULL,
                CurrentStockLbs INT NOT NULL,
                FkLogistics INT REFERENCES Logistics(Pk),
                CostPerUnitUSD INT NOT NULL,
                LbsPerUnit FLOAT NOT NULL,
                FkCategory INT REFERENCES Category(Pk),
                MinimumUnitsFor100People INT NOT NULL
            );

            CREATE TABLE Nutritional (
                Pk INT PRIMARY KEY,
                Description VARCHAR(255) NOT NULL,
                CaloriesPerServing INT NOT NULL,
                FkLogistics INT REFERENCES Logistics(Pk),
                StockLbs INT NOT NULL,
                FkCategory INT REFERENCES Category(Pk),
                WeightPerUnitLbs FLOAT NOT NULL,
                CostPerUnitUSD INT NOT NULL,
                MinimumUnitStock INT NOT NULL
            );
                    
        """)
        conn.commit()
        print("Schema was created successfully")

        # Seed data tables in order of independence 
        sheet_to_table = {
            'Trip': 'Trip',
            'Family': 'Family',
            'Professions': 'Professions',
            'HealthRecords': 'HealthRecords',
            'Psychology': 'Psychology',
            'Habitat': 'Habitat',
            'Logistics': 'Logistics',
            'Category': 'Category',
            'Resources': 'Resources',
            'Nutritional': 'Nutritional',
            'Astronauts': 'Astronauts'
        }

        for sheet_name, table_name in sheet_to_table.items():
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            # Replace all NaN, NaT, or infinite values with None so psycopg2 converts them to SQL NULL
            df = df.where(pd.notnull(df), None)

            # Convert all dataframe column names to lowercase to match PostgreSQL table schema
            df.columns = [c.lower() for c in df.columns]

            cols = list(df.columns)
            cols_str = ", ".join([f'"{c}"' for c in cols])
            placeholders = ", ".join([f"%({c})s" for c in cols])
            
            query = f'INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})'
            
            records = df.to_dict(orient='records')
            
            # Double-check record values to ensure any lingering float NaNs become Python None
            cleaned_records = []
            for record in records:
                cleaned_record = {k: (None if pd.isna(v) else v) for k, v in record.items()}
                cleaned_records.append(cleaned_record)

            cur.executemany(query, cleaned_records)
            conn.commit()
            print(f"Seeded {len(cleaned_records)} rows into table '{table_name}'.")

        print("Database successfully created and seeded securely!")

    except Exception as e:
        conn.rollback()
        print(f"An error occurred during seeding: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_database()

