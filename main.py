from machine
import Pin, Timer
import time
import dht
import network
import urequests
import ntptime


# Définition des broches BCD (connectées au CD4511BE)
BCD_A = Pin(0, Pin.OUT)  # IA
BCD_B = Pin(3, Pin.OUT)  # IB
BCD_C = Pin(2, Pin.OUT)  # IC
BCD_D = Pin(1, Pin.OUT)  # ID

# Transistors pour sélectionner les digits
digit_tens = Pin(14, Pin.OUT)   # Q1
digit_units = Pin(15, Pin.OUT)  # Q2

# Capteur DHT11 connecté à GP2 (sur ton schéma c’est "TEMP")
sensor = dht.DHT11(Pin(16))

# Initialisation du timer
timer = Timer()

# Initialisation des ADC (GP26 pour capteur 1 et GP27 pour capteur 2)
adc1 = machine.ADC(26)  # Capteur 1 sur GP26
adc2 = machine.ADC(27)  # Capteur 2 sur GP27

# Variables globales
tens = 0
units = 0
counter = 0

# Wifi config
#SSID = "le nom du wifi"
#PASSWORD = "mot_de_passe"

# Firebase Realtime Database URL (à adapter avec la bdd)
FIREBASE_URL = "https://robot-7779f-default-rtdb.europe-west1.firebasedatabase.app/temperature.json"


# Table de conversion BCD
def display_digit(value):
    bcd_values = [
        (0, 0, 0, 0), (0, 0, 0, 1), (0, 0, 1, 0), (0, 0, 1, 1),
        (0, 1, 0, 0), (0, 1, 0, 1), (0, 1, 1, 0), (0, 1, 1, 1),
        (1, 0, 0, 0), (1, 0, 0, 1)
    ]
    if 0 <= value <= 9:
        BCD_D.value(bcd_values[value][0])
        BCD_C.value(bcd_values[value][1])
        BCD_B.value(bcd_values[value][2])
        BCD_A.value(bcd_values[value][3])

# Multiplexage
def timer_interrupt(timer):
    global counter
    if counter % 2 == 0:
        digit_tens.value(1)
        digit_units.value(0)
        display_digit(tens)
    else:
        digit_tens.value(0)
        digit_units.value(1)
        display_digit(units)
    counter += 1

# Affichage d'un nombre à 2 chiffres
def display_number(value):
    global tens, units
    value = max(0, min(99, value))  # Clamping 0-99
    tens = value // 10
    units = value % 10

# Initialiser le timer
def init_timer():
    timer.init(freq=100, mode=Timer.PERIODIC, callback=timer_interrupt)

# Connecte la Pico au WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connexion WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            pass
    print("Connecté au WiFi avec IP :", wlan.ifconfig()[0])

# Envoie température à Firebase via PUT
def send_to_firebase(temp):
    try:
        data = {"value": temp}
        response = urequests.put(FIREBASE_URL, json=data)
        print("Donnée envoyée à Firebase:", response.text)
        response.close()
    except Exception as e:
        print("Erreur envoi Firebase:", e)

init_timer()

# Connexion WiFi
#connect_wifi()
# Fonction pour lire la tension du capteur
def read_voltage(adc):
    return adc.read_u16() * 3.3 / 65535  # Convertir l'ADC en volts

# Nouvelle fonction améliorée pour convertir la tension en distance (cm)
def voltage_to_distance(voltage):
    if voltage < 0.45:  # En dessous de 0.45V, hors plage (>80 cm)
        return ">80 cm"
    
    # Nouvelle formule calibrée
    distance = 26.86 * (voltage ** -1.15)
    return round(distance, 1)  # Arrondi à 1 chiffre après la virgule

# Boucle principale
while True:
    try :
        
        t = time.localtime(time.time())
        sensor.measure()  # Lecture des données
        temp = sensor.temperature()  # Température en °C
        humidity = sensor.humidity()  # Humidité en %
       
        voltage1 = read_voltage(adc1)  # Lire tension capteur 1
        voltage2 = read_voltage(adc2)  # Lire tension capteur 2
        
        distance1 = voltage_to_distance(voltage1)  # Conversion distance capteur 1
        distance2 = voltage_to_distance(voltage2)  # Conversion distance capteur 2
        display_number(temp)
        #display_number(humidity)
        
        print("-" * 60)  # Séparateur visuel
        print("{:02d}:{:02d}".format(t[3], t[4]))
        print(f"Capteur 1 - Tension: {voltage1:.2f}V - Distance: {distance1} cm")
        print(f"Capteur 2 - Tension: {voltage2:.2f}V - Distance: {distance2} cm -" )
        print("Température: {}°C   Humidité: {:.0f}% ".format(temp, humidity))
        print("-" * 60)  # Séparateur visuel

        time.sleep(1)  # Pause 500 ms
    
    except OSError as e:
        print("Erreur de lecture du capteur DHT11, réessai...")


