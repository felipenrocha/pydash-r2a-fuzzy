# -*- coding: utf-8 -*-
"""
@author: Felipe Nascimento Rocha - 17/0050084

@description: PyDash Project


Based on algorithm described in: FDASH: A Fuzzy-Based MPEG/DASH Adaptation Algorithm.  Dimitrios J. Vergados, Angelos Michalas, 
Aggeliki Sgora, Dimitrios D. Vergado, and Periklis Chatzimisios



"""

from player.parser import *
from r2a.ir2a import IR2A
import time, json

from math import floor




# TODO: make it dynamic:
segment_size = 1






class R2AFuzzy(IR2A):

    def __init__(self, id):

        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        self.qi = []

   
    #         In our controller, the input variables are the buffering time
    # denoting the time ti that the last received segment i waits at the
    # client until it starts playing and the difference Δti = ti − ti−1
    # of the last buffering time from the previous one.~


    #   Em nosso controlador, as variáveis ​​de entrada são o tempo de buffer
    # denotando o tempo ti que o último segmento recebido i espera no
    # cliente até que ele comece a rodar e a diferença 
    # do último tempo de buffer do anterior.

        # used to store the req and resp time of each segment downloaded
        self.request_time = time.perf_counter()

        self.response_time = 0     
        #  lista p/ armazenar o tempo de cada requisicao,  Ti = [T0, T1, T2...]
        self.buffering_time_list = list()
        # armazenar a posicao em qi da qualidade atual.
        self.current_quality_index = 0

        # algorithm constants
        #  self.target_buffering_time = tempo de buffer alvo (in seconds)
        self.target_buffering_time = 20
        # d = periodo de tempo estimando a taxa de transferência (throughput) da conexão (in seconds)
        # pesos das funções de associacao de saída (defuzzificacao)
        self.factors_membership = {
            "low": .5,
            "high":1,
            "N1": -2,
            "Z": 1,
            "P1": 1.5,
            "P2": 2
        }




# algorithm variables:

# tempo de buffer
    @property
    def buffering_time(self):
        """
        Representacao da variavel t_i do algoritmo.
        Veja que ti pode ser expressada como o tempo que o segmento i espera até começar a rodar.
        Quando um segmento i é baixado, ele irá esperar:  
        1) a quantidade de elementos que tem no buffer * duracao em segundos de cada segmento  - dessa forma temos o tempo em segundos que o buffer tem em cache
        2) O tempo de download do segmento i = uma vez que se demoramos muito para baixar cada segmento, nosso buffer diminui cada vez mais.,
        """
        buffer_size = 0
        if len(self.whiteboard.get_playback_buffer_size())> 0 :
            # getting buffer size from whiteboard data:
            buffer_size = self.whiteboard.get_playback_buffer_size()[-1][1]
        # donwload time is defined when we get response
        download_time = self.response_time
        # podemos calcular o ti do algoritmo da seguinte forma:
        # ti = (tamanho do buffer - tempo de download do segmento) * tamanho do segmento i.
        t_i =  buffer_size - download_time
        return t_i

    @property
    def buffering_difference(self):
        if len(self.buffering_time_list) > 1:
            # Δti = ti − ti−1

            return  self.buffering_time_list[-1] - self.buffering_time_list[-2]

        elif len(self.buffering_time_list) == 1:
            # t = 1 -> Δt1 = t1 - 0
            return  self.buffering_time_list[-1]
        return 0

    def handle_xml_request(self, msg):

        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list

        self.parsed_mpd = parse_mpd(msg.get_payload())
        
        

        self.qi = self.parsed_mpd.get_qi()

        self.send_up(msg)




    def handle_segment_size_request(self, msg):
        self.buffering_time_list.append(self.buffering_time)

        # time to define the segment quality choose to make the request
        
        quality_id = self.fuzzy_controller()
        self.request_time = time.perf_counter()
        
        print("Buffering_time_list : ", self.buffering_time_list)                
        print("FUZZYFICATION buffering: ", self.fuzzyfication_buffering())
        print("FUZZYFICATION DIFFERENCE: ", self.fuzzyfication_difference())
        print("Fuzzy Rules ", self.fuzzy_rules())
        print("Fuzzy controller", self.fuzzy_controller())
        print("Buffering Time: ", self.buffering_time)
        print("Buffering Time Difference: ", self.buffering_difference)

        msg.add_quality_id(quality_id)
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.response_time = time.perf_counter() - self.request_time



        self.send_up(msg)



    def fuzzy_controller(self):
        """Controle Fuzzy -> Retorna a qualidade de bitrate a ser adicionado no request"""
        output = self.defuzzification()
        self.current_quality_index = self.current_quality_index + output

        if  self.current_quality_index >= 19:
            self.current_quality_index = 19
            return self.qi[self.current_quality_index]     
        elif  self.current_quality_index <= 0:
            self.current_quality_index = 0
            return self.qi[self.current_quality_index]        
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
        # tempo do segmento para ser assistido é menor que  do tempo alvo * n2 (buffer pequeno (short))
        if self.buffering_time < (self.target_buffering_time * self.factors_membership['low']):
            return 'S'
        # tempo do segmento para ser assistido  maior que o tempo alvo * n2 e < tempo de dbuffer perto do tempo alvo
        if (self.buffering_time > (self.target_buffering_time * self.factors_membership['low'])) \
         and (self.buffering_time < self.target_buffering_time*self.factors_membership['high']):
            return 'C'
        # buffer maior que tempo alvo
        return 'L'
    def fuzzyfication_difference(self):
        """     #  Para o diferencial do buffer entrada de tempo Δti precisamos descrever o comportamento da taxa
        # entre tempos de buffer subsequentes, as seguintes linguísticas
        # são consideradas as variáveis: falling (F), steady (S) e rising (R)."""
        
        # Diferenca entre os ti  < funcao associada => conexao está caindo
        if self.buffering_difference < -1:
            return 'F'
        # Diferenca entre os ti grande => conexao estavel
        if self.buffering_difference > 1:
            return 'S'
        # diferenca entre os t1 proximo de 0 => conexao crescendo ( n1 <= ti <= p2)
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
            return 1
        if self.fuzzy_rules() == "I":
            return  2



    def initialize(self):
        pass
     
    def finalization(self):
        pass
