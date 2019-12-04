########################################## Interface do projeto de Circuitos 2, Industria 4.0 ##################################################
# Criado em 02/08/2019, Atualizado em 21/11/2019 por Denilson Santos
# Projeto disponível em https://github.com/Adroilson/Computador-de-bordo
#
#
# ################ Esse codigo pode ser usado apenas para fins educacionais, por conta e risco de quem usar, ###################################
# ################ podem haver danos caso vc não saiba o que está fazendo, procure entender todas as funções ###################################
# ################ antes de tentar aplicar qualquer metodo no seu programa.                                  ###################################
#
# 
# Integrantes da equipe: 
# Aquimedes Guedes
# Aroldo Kmita
# Danilo Gomes
# Denilson Santos
# Gildásio Chagas
# João Marco
# Paloma Viana
# Sayonara Viana
# 
# Professora: Patricia Lins. https://patricialins.org/
#
# Curso: Engenharia Elétrica, disciplina Circuitos 2
#
#   Materiais utilizados projeto industria 4.0
#   
#   Sensor de temperatura DS18B20 (EF52) Configurado como W1 (conexão one wire)
#   Pinagem no Raspberry:
#   terra= pino 9
#   vcc = pino 1 (3,3V)
#   porta = pino 11 (GPIO 17)
#
#   Sistema do motor de passo
#   Pino de controle = pino 07 (GPIO 04)
#   Terra = Pino 06
#   
#   Relé:
#   Pino de controle = pino 13 (GPIO 27)
#   Terra = pino 14
#   VCC = pino 2 (5V)
#   
#   Sensor óptico TCRT5000:
#   porta = pino 40 (GPIO21)
#   VCC = pino 17 (3,3V)
#   terra = pino 39 

################### Importando todas as bibliotecas usadas #######################
import pygame 
import os
import time
import math
from os import path
from pygame.locals import *
try:
    from read_RPM import reader
except:
    pass

# Configuração do relé
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM) # # As portas serão nomeadas coforme numeração GPIO
    RELAIS_1_GPIO = 27
    GPIO.setup(RELAIS_1_GPIO, GPIO.OUT) # Designa modo da porta GPIO
    GPIO.output(RELAIS_1_GPIO, GPIO.LOW) # Deve iniciar desligado

except:
    pass

# Para o motor de passo e sensor óptico:
try: 
    import pigpio # Biblioteca para auxilio na manipulação  do GPIO
    ESC=4  # Pino de controle do ESC
    pi = pigpio.pi()
    pi.set_servo_pulsewidth(ESC, 0)# Com isso o motor vai sempre começar desligado

    # Configurando o leitor de RPM
    RPM_GPIO = 21 #GPIO do Sensor óptico TCRT5000 
    lerVelocidade = reader(pi, RPM_GPIO) #instancia do leitor de RPM, se lê com lerVelocidade.RPM()
except:
    pass 

try:
    from w1thermsensor import W1ThermSensor # Biblioteca do sensor de temperatura
except:
    pass

# Dados da tela
WIDTH = 800
HEIGHT = 600
FPS = 120

# Buffer de dados, esse dicionario armazena todos os dados usados na interface 
buffer = {"temp": 0,                # Temperatura 
    "tela":'painel_mini',           # 'temperatura' ou 'painel_real' ou 'painel_mini'
    "modo":"n",                     # mudar para 'teste' se quiser testar sem a interface grafica.
    "motor": False,                 # Motor ligado ou desligado
    "speed":0,                      # Frequencia de controle da velocidade
    "resfria":False,                # Estado do sistema de resfriamento
    "escala_temp":(0,100),          # maximo e minimo  para escalas de temperatura
    "escala_RPM" : (0,13000),       # maximo e minimo  para escalas de RPM
    "escala_velocidade" : (0,240),  # maximo e minimo  para escalas de velocidade
    "escala_resfriamento" : (65,50),# maximo e minimo do controle de temperatura, a 80 ativa, a 50 desativa
    "RPM":0,                        # RPM
    "aux_tela": 0,                  # auxilia na mudança de telas  
    "velocidade": 0}                # Velocidade

try:
    sensor = W1ThermSensor() # Instancia que lê o valor da temperatura
except:
    pass

# define cores usadas no programa no modelo RGB
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

#Nome das imagens usadas
BIG_DIAL = "nude_meter.png"
PONTEIRO_VERMELHO = "nedlered.png"
PONTEIRO_PRETO ="nedleblack.png"
FUEL = "ecofuel.png"
TERMOMETRO = "thermometer.png"
PAINEL = "painel.jpg"

# Inicializando biblioteca pygame
pygame.init()

if buffer['modo'] == 'teste':
    pass
else:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Circuitos II")
clock = pygame.time.Clock()
img_dir = path.join(path.dirname(__file__),'Sprite')

class Ponteiro(pygame.sprite.Sprite):
    """ Classe que carrega o ponteiro
            Esta classe cria os objetos dos ponteiros que são capazes de girar segundo seu tipo."""
    def __init__(self,tipo,imagem,tamanhox,tamanhoy,centerx,centery):
        super(Ponteiro,self).__init__()
        # original e cópia necessários para otimizar rotação de imagem
        self.image_G = pygame.image.load(path.join(img_dir,imagem)).convert()
        self.image_orig = pygame.transform.scale(self.image_G,(tamanhox,tamanhoy))
        self.image_orig.set_colorkey(WHITE)
        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect()
        self.tipo = tipo
        self.rect.centerx = centerx
        self.rect.centery = centery
        self.last_update = pygame.time.get_ticks()

    def grau_temp(self):
        """Essa função calcula o angulo de inclinação do ponteiro em função da escala de temperatura considerando
             o angulo de rotação de -135 a 135 graus. """
        try:
            temperatura = buffer['temp']
            angulo = (((temperatura - buffer['escala_temp'][0])/(buffer['escala_temp'][1]-buffer['escala_temp'][0]))*270) - 135
            return angulo
        except:
            return 135

    def grau_temp_R(self):
        """Essa função calcula o angulo de inclinação do ponteiro em função da escala de temperatura considerando o angulo de 
            rotação de -90 a 0 graus. """
        try:
            temperatura = buffer['temp']
            angulo = (((temperatura - buffer['escala_temp'][0])/(buffer['escala_temp'][1]-buffer['escala_temp'][0]))*-90) + 90
            return angulo
        except:
            return 135

    def grau_RPM(self):
        """Essa função calcula o angulo de inclinação do ponteiro em função da escala de RPM considerando o angulo de 
            rotação de -135 a 135 graus. """
        try:
            rot = buffer['RPM']
            angulo = (((rot - buffer['escala_RPM'][0])/(buffer['escala_RPM'][1]-buffer['escala_RPM'][0]))*270) - 135
            return angulo
        except:
            return 135

    def grau_RPM_R(self):
        """Essa função calcula o angulo de inclinação do ponteiro em função da escala de RPM considerando o angulo de 
            rotação de -100 a 100 graus. """
        try:
            rot = buffer['RPM']
            angulo = (((rot - buffer['escala_RPM'][0])/(buffer['escala_RPM'][1]-buffer['escala_RPM'][0]))*-200) + 100
            return angulo
        except:
            return 100

    def grau_vel(self):
        """Essa função calcula o angulo de inclinação do ponteiro em função da escala de velocidade considerando o angulo de 
            rotação de -135 a 135 graus. """
        try:
            velo = buffer['velocidade']
            angulo = (((velo - buffer['escala_velocidade'][0])/(buffer['escala_velocidade'][1]-buffer['escala_velocidade'][0]))*270) - 135
            return angulo
        except:
            return 135

    def grau_vel_R(self):
        """Essa função calcula o angulo de inclinação do ponteiro em função da escala de velocidade considerando o angulo de 
             de -100 a 100 graus. """
        try:
            velo = buffer['velocidade']
            angulo = (((velo - buffer['escala_velocidade'][0])/(buffer['escala_velocidade'][1]-buffer['escala_velocidade'][0]))*-200) + 100
            return angulo
        except:
            return 100

    def grau_gas(self): # não implementado
        return 0
        

    def rotacionar(self):
        """ Esse método rotaciona a imagem do ponteiro segundo o seu tipo. """
        now = pygame.time.get_ticks()
        if now - self.last_update > 50: #pygame.time.get_tics() pega o tempo atual 
            self.last_update = now
            #new_image = pygame.transform.rotate(self.image_orig, self.rot)# método que rotaciona imagem
            if self.tipo == "RPM":
                new_image = pygame.transform.rotate(self.image_orig,self.grau_RPM())# método que rotaciona imagem
            if self.tipo == "temp":
                new_image = pygame.transform.rotate(self.image_orig,self.grau_temp())# método que rotaciona imagem
            if self.tipo == "R_temp":
                new_image = pygame.transform.rotate(self.image_orig,self.grau_temp_R())# método que rotaciona imagem
            if self.tipo == "vel":
                new_image = pygame.transform.rotate(self.image_orig,self.grau_vel())# método que rotaciona imagem
            if self.tipo == "gas":
                new_image = pygame.transform.rotate(self.image_orig,self.grau_gas())# método que rotaciona imagem
            if self.tipo == "R_RPM":
                new_image = pygame.transform.rotate(self.image_orig,self.grau_RPM_R())# método que rotaciona imagem
            if self.tipo == "R_vel":
                new_image = pygame.transform.rotate(self.image_orig,self.grau_vel_R())# método que rotaciona imagem
            old_center = self.rect.center
            self.image = new_image
            self.rect = self.image.get_rect()
            self.rect.center = old_center
    def update(self):
        " Método que chama a atualização das imagens deste sprite"
        self.rotacionar()

class Figura(pygame.sprite.Sprite):
    """classe que carrega as figuras estaticas da interface """
    def __init__(self,imagem,tamanhox,tamanhoy,centrox,centroy):
        super(Figura,self).__init__()
        # original e cópia necessários para otimizar rotação de imagem
        self.image = pygame.image.load(path.join(img_dir,imagem)).convert()
        self.image = pygame.transform.scale(self.image,(tamanhox,tamanhoy))
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.rect.centerx = centrox
        self.rect.centery = centroy

################################### Funções Auxiliares #######################################
        
def calcula_velocidade():
    """Considerando a rotação de um eixo de 5cm """
    V = 2*math.pi*(buffer["RPM"]*60*5*10**-5)
    buffer['velocidade'] = V

def draw_text(text, size, color, x, y):
    if buffer['modo'] == 'teste':
        pass
    else:
        # essa função define os passos para se desenhar textos na tela...
        font = pygame.font.Font(pygame.font.match_font('arial'), size)
        text_surface = font.render(text, True,color)
        text_rect = text_surface.get_rect()
        text_rect.centerx = x
        text_rect.centery = y
        screen.blit(text_surface, text_rect)

def draw_livre(text, size, color, x, y):
    if buffer['modo'] == 'teste':
        pass
    else:
        # essa função define os passos para se desenhar textos na tela...
        font = pygame.font.Font(pygame.font.match_font('arial'), size)
        #font = pg.font.Font(self.font_name, size)
        text_surface = font.render(text, True,color)
        text_rect = text_surface.get_rect()
        text_rect.x = x
        text_rect.y = y
        screen.blit(text_surface, text_rect) 

def draw_ajuda():
    """desenha os comandos da interface"""
    h = 30
    #help_outline = pygame.draw.rect(screen, WHITE, (315, 400, 200,160) ,2)
    draw_text("Pressione:",30,WHITE,400,410+h)
    draw_livre("(y) ligar o motor ",20,WHITE,320,430+h)
    draw_livre("(o) desligar o motor ",20,WHITE,320,460+h)
    draw_livre("(w) aumentar RPM",20,WHITE,320,490+h)
    draw_livre("(s) reduzir RPM",20,WHITE,320,520+h)

def draw_legenda():
    """desenha a legenda na tela"""
    critico  = pygame.draw.rect(screen, RED, (670+1, 480+1, 32,32))
    moderado  = pygame.draw.rect(screen, YELLOW, (670+1, 480+2+32, 32,32))
    normal  = pygame.draw.rect(screen, GREEN, (670+1, 480+3+64, 32,32))
    draw_text("Crítico",20,RED,670+80,480+20)
    draw_text("Moderado",15,YELLOW,670+80,480+50)
    draw_text("Normal",20,GREEN,670+80,480+80)

def seleciona_telas():
    """Use as setas do teclado para mudar de tela"""
    if buffer['aux_tela'] < 0:
        buffer['aux_tela'] = 0

    if buffer['aux_tela'] > 2:
        buffer['aux_tela'] = 2

    if buffer['aux_tela'] == 0:
        buffer['tela'] = 'painel_mini'

    if buffer['aux_tela'] == 1:
        buffer['tela'] = 'temperatura'

    if buffer['aux_tela'] == 2:
        buffer['tela'] = 'painel_real' 



def testador(): # lembre de mim pra testar, estarei no main loop se precisar
    """usado para fins de teste para criar dados falsos na interface, use se precisar testar fora do Raspberry 
        Não use os comandos do motor se estiver testando em um desktop ou o programa irá parar """
    buffer["temp"] += 1
    buffer["RPM"] += 100
    #buffer['velocidade'] += 1

def resfria():
    """liga e desliga o resfriamento com base na temperatura"""
    if buffer['modo'] == 'teste':
        pass
    else:
        if buffer['temp'] > buffer['escala_resfriamento'][0]:
            GPIO.output(RELAIS_1_GPIO, GPIO.HIGH) # on
            buffer["resfria"] = True
        if buffer['temp'] < buffer['escala_resfriamento'][1] and buffer["resfria"] == True:
            GPIO.output(RELAIS_1_GPIO, GPIO.LOW) # off
            buffer["resfria"] = False

#######################################################################################################
################################ Função de Limite de rotação #########################################
def limita():
    if buffer['motor']:
        if buffer["speed"] > 2000:
            buffer["speed"] = 2000
        if buffer["speed"] < 1200:
            buffer["speed"] = 1200
#######################################################################################################        

##### Criando os grupos de Sprites ######
sprites_principal_real = pygame.sprite.Group()
sprites_principal_mini = pygame.sprite.Group()
sprites_temperatura = pygame.sprite.Group()


if buffer['modo'] == 'teste':
    pass
else:
    ##################### Imagens da tela principal minimalista ###################################
    #          imagem, tamanhox, tamanhoy, centerx, centery
    dial_velocidade = Figura(BIG_DIAL,300,300,225,200) # Odometro Velocidade
    ponteiro_velocidade = Ponteiro("vel",PONTEIRO_PRETO,10,200,225,200)
    dial_gas = Figura(BIG_DIAL,150,150,225,450)
    ponteiro_gas = Figura(PONTEIRO_PRETO,5,100,225,450)
    gasolina = Figura(FUEL,80,80,225,450)
    gasolina.image.set_colorkey(BLACK)
    dial_RPM = Figura(BIG_DIAL,300,300,575,200)
    ponteiro_M_PM = Ponteiro('RPM',PONTEIRO_PRETO,10,200,575,200)
    dial_temp = Figura(BIG_DIAL,100,100,575,450)
    ponteiro_temperatura = Ponteiro('temp',PONTEIRO_PRETO,5,70,575,450)
    termometro = Figura(TERMOMETRO,50,50,575,450)
    
    ################################# Painel Realista ########################################
    #                       imagem, tamanhox, tamanhoy, centerx, centery
    painel_realista = Figura(PAINEL,806,454,WIDTH//2,HEIGHT//2) # Odometro Velocidade
    ponteiro_R_RPM = Ponteiro('R_RPM',PONTEIRO_VERMELHO,20,170,250,390)
    ponteiro_R_vel = Ponteiro('R_vel',PONTEIRO_VERMELHO,20,170,534,393)
    ponteiro_R_gas = Ponteiro('gas',PONTEIRO_VERMELHO,10,100,715,391)
    ponteiro_R_temp  = Ponteiro('R_temp',PONTEIRO_VERMELHO,10,100,87,395)
                   
   # imagens da tela só temperatura
    dial_tela_temp = Figura(BIG_DIAL,400,400,400,300)
    ponteiro_tela_temp = Ponteiro('temp',PONTEIRO_PRETO,5,300,400,300)
    termometro2 = Figura(TERMOMETRO,100,100,400,300)

    # adiciona os sprites em grupos diferentes, permite ter várias exibições diferentes de tela.
    sprites_temperatura.add(dial_tela_temp)
    sprites_temperatura.add(ponteiro_tela_temp)
    sprites_temperatura.add(termometro2)

    sprites_principal_real.add(painel_realista)
    sprites_principal_real.add(ponteiro_R_RPM)
    sprites_principal_real.add(ponteiro_R_vel)
    sprites_principal_real.add(ponteiro_R_gas)
    sprites_principal_real.add(ponteiro_R_temp)
    
    sprites_principal_mini.add(dial_velocidade)
    sprites_principal_mini.add(dial_gas)
    sprites_principal_mini.add(gasolina)
    sprites_principal_mini.add(ponteiro_gas)
    sprites_principal_mini.add(dial_RPM)
    sprites_principal_mini.add(ponteiro_M_PM)
    sprites_principal_mini.add(dial_temp)
    sprites_principal_mini.add(termometro)
    sprites_principal_mini.add(ponteiro_velocidade)
    sprites_principal_mini.add(ponteiro_temperatura)
     
# Loop principal (main loop)
running = True
while running:
    clock.tick(FPS)
    #testador() # Lembra de mim? Pra fazer rodar como teste tire o # do começo dessa linha
    calcula_velocidade()
    # Pega a leitura do sensor a cada ciclo
    try:
        buffer['temp'] = sensor.get_temperature() # Armazena leitura da temperatura no buffer
        buffer['RPM'] = lerVelocidade.RPM()       # Armazena leitura do RPM no buffer
        calcula_velocidade()
        resfria()
    except:
        pass
    # Processa os  input (events)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # trocar de tela
        if event.type == KEYDOWN:
            if event.key == K_LEFT:
                buffer['aux_tela'] -= 1
                seleciona_telas()
            if event.key == K_RIGHT:
                buffer['aux_tela'] += 1
                seleciona_telas()

            if event.key == K_y: # Liga o motor 
                buffer['motor'] = True
                buffer["speed"] = 1200
                pi.set_servo_pulsewidth(ESC, buffer["speed"])

            if buffer['motor']:
                if event.key == K_w:
                    buffer["speed"] += 10 
                    limita()
                    pi.set_servo_pulsewidth(ESC, buffer["speed"])
                if event.key == K_s:
                    buffer["speed"] -= 10
                    limita()
                    pi.set_servo_pulsewidth(ESC, buffer["speed"])
                if event.key == K_o:
                    buffer["speed"] = 0
                    pi.set_servo_pulsewidth(ESC, buffer["speed"])
                    buffer['motor'] = False
                    
    # Update
    if buffer['modo'] == 'teste':
        pass
    else:
        if buffer['tela'] == "temperatura":
            sprites_temperatura.update()
                # Draw / render
            screen.fill(BLACK)
            sprites_temperatura.draw(screen)
            draw_legenda()
            draw_text(str(buffer['temp'])[:5]+"ºC",40,WHITE,dial_tela_temp.rect.midbottom[0],dial_tela_temp.rect.midbottom[1]- 50)
            pygame.display.flip()
        elif buffer['tela'] == "painel_real":
            sprites_principal_real.update()

            # Draw / render
            screen.fill(BLACK)
            sprites_principal_real.draw(screen)
            draw_ajuda()
            pygame.display.flip()

        elif buffer['tela'] == "painel_mini":
            sprites_principal_mini.update()
            # Draw / render
            screen.fill(BLACK)
            sprites_principal_mini.draw(screen)
            draw_text(str(buffer['RPM'])[:5],40,WHITE,dial_RPM.rect.midbottom[0],dial_RPM.rect.midbottom[1]- 50)
            draw_text(str(buffer['temp'])[:4],20,WHITE,dial_temp.rect.midbottom[0],dial_temp.rect.midbottom[1]- 15)
            draw_text("RPM",50,WHITE,dial_RPM.rect.centerx,dial_RPM.rect.centery)
            draw_text(str(buffer['velocidade'])[:5],40,WHITE,dial_velocidade.rect.midbottom[0],dial_velocidade.rect.midbottom[1]- 50)
            draw_text("KM/H",50,WHITE,dial_velocidade.rect.centerx,dial_velocidade.rect.centery)
            draw_ajuda()
            draw_legenda()
            pygame.display.flip()

pygame.quit()