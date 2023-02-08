from socket_connection_manager import Client
LOCALHOST = "127.0.0.1"

if __name__ == '__main__':
    import time
    import swp_message_03 as swp

    client = Client(LOCALHOST)
    while not client.status:
        pass

    while True:
        client.send_message(swp.Connect(1, 10, 0, 0))
        timestamp, received = client.get_received_message()
        if received:
            print(timestamp, received)

        time.sleep(1)
