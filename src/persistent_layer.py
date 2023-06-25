import psycopg2
import json

from rabbitmq_handler import RabbitMQHandler
from config.rabbitmq_config import QUEUES


def transform_data(data):
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


def main():
    db_conn = None
    try:
        db_conn = psycopg2.connect(
            host="localhost",
            database="rt_crypto",
            user="postgres",
            password="postgres",
            port=5432,
        )
        cur = db_conn.cursor()

        queue_name = QUEUES.get("marquet_information_queue")
        consumer = RabbitMQHandler("localhost", queue_name)

        def handle_queue_message(ch, method, properties, body):
            data = json.loads(body)
            data_to_be_persisted = transform_data(data)

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
                data_to_be_persisted["instrument_name"],
                data_to_be_persisted["currency"],
                data_to_be_persisted["maturity"],
                data_to_be_persisted["strike"],
                data_to_be_persisted["type"],
                data_to_be_persisted["underlying_price"],
                data_to_be_persisted["timestamp"],
                data_to_be_persisted["settlement_price"],
                data_to_be_persisted["open_interest"],
                data_to_be_persisted["min_price"],
                data_to_be_persisted["max_price"],
                data_to_be_persisted["mark_price"],
                data_to_be_persisted["mark_iv"],
                data_to_be_persisted["last_price"],
                data_to_be_persisted["interest_rate"],
                data_to_be_persisted["index_price"],
                data_to_be_persisted["bid_iv"],
                data_to_be_persisted["best_bid_price"],
                data_to_be_persisted["best_bid_amount"],
                data_to_be_persisted["best_ask_price"],
                data_to_be_persisted["best_ask_amount"],
                data_to_be_persisted["ask_iv"],
            )

            cur.execute(insert_script, insert_value)
            db_conn.commit()

            print(f"instered data")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        print("Listening for incoming messages...")
        consumer.consume_messages(handle_queue_message)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if db_conn is not None:
            db_conn.close()
            print("db connection closed.")


if __name__ == "__main__":
    main()
