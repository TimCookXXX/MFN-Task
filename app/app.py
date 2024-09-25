import psycopg2
import time
import logging
from datetime import datetime
import random
import string
import os


def create_connection():
    database_url = os.getenv("DATABASE_URL")
    while True:
        try:
            connection = psycopg2.connect(database_url)
            logging.info("Connected to the database successfully")
            return connection
        except psycopg2.OperationalError as e:
            logging.warning("Database is not ready yet, retrying in 5 seconds...")
            time.sleep(5)


def create_table(conn):
    with conn.cursor() as cursor:
        cursor.execute(
            """
           CREATE TABLE IF NOT EXISTS data_table (
               id SERIAL PRIMARY KEY,
               data TEXT NOT NULL,
               date TIMESTAMP NOT NULL
           );
       """
        )
        conn.commit()


def generate_data():
    return "".join(random.choices(string.ascii_lowercase, k=10))


def insert_data(conn, data, date):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO data_table (data, date) 
            VALUES (%s, %s);
            """,
            (data, date),
        )
        conn.commit()


def clear_table_if_full(conn):
    threshold = int(os.getenv("TABLE_CLEAR_THRESHOLD", 30))
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM data_table;")
        count = cursor.fetchone()[0]
        if count >= threshold:
            cursor.execute("DELETE FROM data_table;")
            conn.commit()
            logging.info(f"Table successfully cleared! {count} rows were deleted.")
        else:
            logging.debug(f"Table not cleared. Current row count: {count}")


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main():
    sleep_time = int(os.getenv("DATA_INSERT_INTERVAL", 60))
    conn = create_connection()
    create_table(conn)

    try:
        while True:
            data = generate_data()
            date = datetime.now()
            insert_data(conn, data, date)
            logging.info(f"Inserted: {data} at {date}")
            clear_table_if_full(conn)
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        logging.info("Script interrupted by user")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        conn.close()
        logging.info("Database connection closed")


if __name__ == "__main__":
    main()
