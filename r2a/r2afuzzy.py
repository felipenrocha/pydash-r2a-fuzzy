# -*- coding: utf-8 -*-
"""
@author: Felipe Nascimento Rocha - 17/0050084

@description: PyDash Project



the quality list is obtained with the parameter of handle_xml_response() method and the choice
is made inside of handle_segment_size_request(), before sending the message down.



Based on algorithm described in: FDASH: A Fuzzy-Based MPEG/DASH Adaptation Algorithm.  Dimitrios J. Vergados, Angelos Michalas, 
Aggeliki Sgora, Dimitrios D. Vergado, and Periklis Chatzimisios



"""

from player.parser import *
from r2a.ir2a import IR2A
import time

class R2AFuzzy(IR2A):

    def __init__(self, id, buffering_time=0, buffering_time_difference=0):

        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        self.qi = []
   
    #         In our controller, the input variables are the buffering time
    # denoting the time ti that the last received segment i waits at the
    # client until it starts playing and the difference Δti = ti − ti−1
    # of the last buffering time from the previous one.~


    #   Em nosso controlador, as variáveis ​​de entrada são o tempo de buffer
    # denotando o tempo ti que o último segmento recebido i espera no
    # cliente até que ele comece a rodar e a diferença Δti = ti − ti−1
    # do último tempo de buffer do anterior.

        # variables of algorithm:
        # tempo de buffer
        self.buffering_time = buffering_time
        self.buffering_time_difference = buffering_time_difference



        # used to store the req and resp time of each segment downloaded
        self.requestTime = 0
      


        # algorithm constants
        #  self.target_buffering_time = tempo de buffer alvo (in seconds)
        self.target_buffering_time = 35
        # d = periodo de tempo estimando a taxa de transferência (throughput) da conexão (in seconds)
        self.d = 60
        # pesos das funções de associacao de saída (defuzzificacao)
        self.factors_membership = {
            "N2": .25,
            "N1": .5,
            "Z": 1,
            "P1": 1.5,
            "P2": 2
        }

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()

        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())

   
        # print('xml response parseid_dict', self.parsed_mpd.__dict__)
        self.qi = self.parsed_mpd.get_qi()

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        # time to define the segment quality choose to make the request
        msg.add_quality_id(self.qi[19])
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        print("> Handle Sagment Size Response Dictionary ", msg.__dict__)
        self.send_up(msg)

    def initialize(self):
        pass
     
    def finalization(self):
        pass
