import psycopg2
import json
import time
import sys

from rabbitmq_handler import RabbitMQHandler
from config.rabbitmq_config import QUEUES

class MarketDataProcessor:
    def __init__(self, queue_name: str) -> None:
        self.db_conn = None
        self.queue_name = queue_name

    def connect_to_db(self):
        retry_delay = 1
        attempt = 0

        while True:
            try:
                self.db_conn = psycopg2.connect(
                    host="db",
                    database="rt_crypto",
                    user="postgres",
                    password="postgres",
                    port=5432,
                )
                print("connected to db successfully..")
                return "connected"
            except (Exception, psycopg2.DatabaseError):
                print(f"error while connecting to the db")
                attempt += 1

            current_delay = retry_delay * (2**attempt)
            print(f"retrying to connect to the db....")
            time.sleep(current_delay)


    def disconnect_from_db(self):
        if self.db_conn is not None:
            self.db_conn.close()

    def transform_data(self, data):
        newData = {
            key: value
            for key, value in data.items()
            if key
            not in (
                "state",
                "stats",
                "underlying_index",
                "greeks",
                "estimated_delivery_price",
            )
        }

        instrument_name_data = newData["instrument_name"].split("-")

        newData["currency"] = instrument_name_data[0]
        newData["maturity"] = instrument_name_data[1]
        newData["strike"] = instrument_name_data[2]
        newData["type"] = instrument_name_data[3]

        return newData

    def insert_data_to_db(self, data):
        insert_script = """
            INSERT INTO market_informations 
            (
            instrument_name, currency, maturity, strike, type,underlying_price, timestamp, settlement_price, 
            open_interest, min_price, max_price, mark_price, mark_iv, last_price, interest_rate, index_price, bid_iv, best_bid_price, 
            best_bid_amount, best_ask_price, best_ask_amount, ask_iv
            ) 
            VALUES 
            (
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )
        """

        insert_value = (
            data["instrument_name"],
            data["currency"],
            data["maturity"],
            data["strike"],
            data["type"],
            data["underlying_price"],
            data["timestamp"],
            data["settlement_price"],
            data["open_interest"],
            data["min_price"],
            data["max_price"],
            data["mark_price"],
            data["mark_iv"],
            data["last_price"],
            data["interest_rate"],
            data["index_price"],
            data["bid_iv"],
            data["best_bid_price"],
            data["best_bid_amount"],
            data["best_ask_price"],
            data["best_ask_amount"],
            data["ask_iv"],
        )

        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute(insert_script, insert_value)
                self.db_conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            if error == "connection already closed" or self.db_conn.closed == 2:
                response = self.connect_to_db()
                if response == "connected":
                    return self.insert_data_to_db(data)
            else:
                sys.exit(0)

    def handle_queue_message_insertion(self, channel, method, properties, body):
        try:
            data = json.loads(body)
            print("received data")
            data_to_be_persisted = self.transform_data(data)
            print("data transformed succesfully")
            self.insert_data_to_db(data_to_be_persisted)
            print("data persisted succesfully")
            print("-------------------------------")
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as error:
            print(f"error occured while processing data {error}")

    def init_etl_process(self):
        self.connect_to_db()
        try:
            rabbitmq_consumer = RabbitMQHandler("rabbitmq", self.queue_name)
            print("start listening for incoming messages...")
            rabbitmq_consumer.consume_messages(
                callback=self.handle_queue_message_insertion
            )
        finally:
            self.disconnect_from_db()


if __name__ == "__main__":
    try:
        queue_name = QUEUES.get("marquet_information_queue")
        MarketDataProcessor(queue_name).init_etl_process()
    except KeyboardInterrupt:
        pass
