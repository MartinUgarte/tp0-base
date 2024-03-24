import socket
import logging
import signal

from .connection import ClientConnection

from .utils import load_bets, has_won

BET_SEPARATOR = "\t"
ALL_BETS_ACK = "ALL_BETS_ACK"
AGENCIES = 5

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._client_conns = []
        self.active = True

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
    
        signal.signal(signal.SIGTERM, self.__handle_sigterm)

        while self.active:
            client_sock = self.__accept_new_connection()
            if self.active:
                client_conn = ClientConnection(client_sock, client_sock.getpeername())
                self._client_conns.append(client_conn)
                self.__handle_client_connection(client_conn)
        
    def __handle_sigterm(self, signal, frame):
        """
        Handles a SIGTERM signal by stopping the server loop and closing its socket
        """
        logging.info("Signal SIGTERM received")
        self.active = False
        self._server_socket.close()

    def __receive_bets(self, client_conn):
        try:
            client_conn.receive_messages()    
            logging.info(f'action: receive_all_bets | result: success | ip: {client_conn.client_addr[0]}')   

            if not client_conn.send_message(ALL_BETS_ACK): return   
            logging.info(f'action: send_all_bets_ack | result: succes | ip: {client_conn.client_addr[0]}')

            if len(self._client_conns) == AGENCIES:
                return True

        except OSError as e:
            logging.error(f'action: receive_message | result: fail | error: {e}')
            client_conn.close()
            return False

    def __find_winners(self):
        winners = []
        for bet in load_bets():
            if has_won(bet):
                winners.append(bet)
        for winner in winners:
            logging.info(f"action: get_winners | result: success | winner: {winner.first_name} {winner.last_name}")

    def __handle_client_connection(self, client_conn):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """

        if not self.__receive_bets(client_conn):
            return
        
        self.__find_winners()
            
    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        try:
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except:
            logging.error('Error reading server socket')
            return None
        