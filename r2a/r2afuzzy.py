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
        self.responseTime = time.perf_counter()     
        #  lista p/ armazenar o tempo de cada requisicao,  Ti = [T0, T1, T2...]
        self.time_list = list()

        # armazenar a posicao em qi da qualidade atual.
        self.current_quality_index = 8

        #   Três variáveis ​​linguísticas [short (S), close (C) e longo (L)]
        # são adotados para o tempo de buffer para descrever a distância do tempo de buffer atual de um tempo de buffering alvo
        # 

        #   Além disso, uma vez que para o diferencial do buffer
        # entrada de tempo Δti precisamos descrever o comportamento da taxa
        # entre tempos de buffer subsequentes, as seguintes linguísticas
        # são consideradas as variáveis: falling (F), steady (S) e rising (R).

        # linguistic variables:
        


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
        self.request_time = time.perf_counter() - self.request_time
        # print("xml req time", self.request_time)

   
        # print('xml response parseid_dict', self.parsed_mpd.__dict__)
        self.qi = self.parsed_mpd.get_qi()
        print(self.qi)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        # time to define the segment quality choose to make the request

        quality_id = self.fuzzy_controller()
        msg.add_quality_id(quality_id)
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        print("> Handle Segment Size Response:", msg.__dict__)
        self.send_up(msg)


    def fuzzy_controller(self):
        """Controle Fuzzy -> Retorna a qualidade de bitrate a ser adicionado no request"""
        output = self.defuzzification()
        print('self.qi[self.current_quality_index]', self.qi[self.current_quality_index])
        print('output', output)
        if (self.current_quality_index + output) >= 19:
            self.current_quality_index = 19
            return self.qi[self.current_quality_index]     
        elif (self.current_quality_index + output) <= 0:
            self.current_quality_index = 0
            return self.qi[self.current_quality_index]
            
        self.current_quality_index = self.current_quality_index + output
        return self.qi[self.current_quality_index]



# Controller phases:


# # fuzzification:
#    During this process, each element of input
# data is converted to degrees of membership by a lookup
# in one or several membership functions


    def fuzzyfication_buffering(self):
        """
        #   Três variáveis ​​linguísticas [short (S), close (C) e longo (L)]
        # são adotados para o tempo de buffer para descrever a distância do tempo de buffer atual de um tempo de buffering alvo
        # 
        """
        return 'L'
    def fuzzyfication_difference(self):
        """     #  Para o diferencial do buffer entrada de tempo Δti precisamos descrever o comportamento da taxa
        # entre tempos de buffer subsequentes, as seguintes linguísticas
        # são consideradas as variáveis: falling (F), steady (S) e rising (R)."""
        return 'R'
    
    def fuzzy_rules(self):
        # R1
        if self.fuzzyfication_buffering() == 'S' and self.fuzzyfication_difference() == 'F':
            return 'R'
        
        if self.fuzzyfication_buffering() == 'C' and self.fuzzyfication_difference() == 'F':
            return 'SR' 
        
        if self.fuzzyfication_buffering() == 'L' and self.fuzzyfication_difference() == 'F':
            return 'NC'
        
        if self.fuzzyfication_buffering() == 'S' and self.fuzzyfication_difference() == 'S':
            return 'SR'
        
        if self.fuzzyfication_buffering() == 'C' and self.fuzzyfication_difference() == 'S':
            return 'NC'
        
        if self.fuzzyfication_buffering() == 'L' and self.fuzzyfication_difference() == 'S':
            return 'SI'
        
        if self.fuzzyfication_buffering() == 'S' and self.fuzzyfication_difference() == 'R':
            return 'NC'
        
        if self.fuzzyfication_buffering() == 'C' and self.fuzzyfication_difference() == 'R':
            return 'SI'
        
        if self.fuzzyfication_buffering() == 'L' and self.fuzzyfication_difference() == 'R':
            return 'I'

    def fuzzy_inference_engine(self):
        pass
    def defuzzification(self):

        """The output of the FLC f represents an increase/decrease factor of the resolution of the next segment.
           Thus, the linguistic variables of the output are described as
        reduce (R), small reduce (SR), no change (NC), small increase
        (SI), and increase (I). """
        if self.fuzzy_rules() == "R":
            return  -2
        if self.fuzzy_rules() == "SR":
            return  -1
        if self.fuzzy_rules() == "NC":
            return  0
        if self.fuzzy_rules() == "SI":
            return  1
        if self.fuzzy_rules() == "I":
            return  2



    def initialize(self):
        pass
     
    def finalization(self):
        pass
