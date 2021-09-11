# Import libraries
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os
import time

end_of_game = None  # set if the user wins or ends the game

current_guess = 0
first_time = 1
num_guess = 0

# DEFINE THE PINS USED HERE
LED_value = [11, 13, 15]
LED_accuracy = 32
btn_submit = 16
btn_increase = 18
buzzer = 33
eeprom = ES2EEPROMUtils.ES2EEPROM()


# Print the game banner
def welcome():
    os.system('clear')
    print("  _   _                 _                  _____ _            __  __ _")
    print("| \ | |               | |                / ____| |          / _|/ _| |")
    print("|  \| |_   _ _ __ ___ | |__   ___ _ __  | (___ | |__  _   _| |_| |_| | ___ ")
    print("| . ` | | | | '_ ` _ \| '_ \ / _ \ '__|  \___ \| '_ \| | | |  _|  _| |/ _ \\")
    print("| |\  | |_| | | | | | | |_) |  __/ |     ____) | | | | |_| | | | | | |  __/")
    print("|_| \_|\__,_|_| |_| |_|_.__/ \___|_|    |_____/|_| |_|\__,_|_| |_| |_|\___|")
    print("")
    print("Guess the number and immortalise your name in the High Score Hall of Fame!")


# Print the game menu
def menu():
    global end_of_game
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
        menu()
    elif option == "P":
        os.system('clear')
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        global value
        value = generate_number()
        while not end_of_game:
            pass
    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")


def display_scores(count, scores):
    # print the scores to the screen in the expected format
    print("There are {} scores. Here are the top 3!".format(count))
    # print out the scores in the required format
    if count>=3:
        for i in range(3):
            print(str(i+1)+ " - "+ scores[i + 1][0]+ scores[i + 1][1]+ scores[i + 1][2]+ " took "+ str(scores[i + 1][3])+ " guesses")
    else:
        for i in range(int(count)):
            print(str(i+1)+ " - "+ scores[i + 1][0]+ scores[i + 1][1]+ scores[i + 1][2]+ " took "+ str(scores[i + 1][3])+ " guesses")
    
    pass


# Setup Pins
def setup():
    # Setup board mode
    GPIO.setmode(GPIO.BOARD)
    # Setup regular GPIO
    GPIO.setup(LED_value[0], GPIO.OUT)
    GPIO.setup(LED_value[1], GPIO.OUT)
    GPIO.setup(LED_value[2], GPIO.OUT)

    GPIO.setup(btn_submit, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(btn_increase, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Setup PWM channels
    
    GPIO.setup(buzzer, GPIO.OUT)
    GPIO.setup(LED_accuracy, GPIO.OUT)
    global buzzerPWM
    global ledPWM
    buzzerPWM = GPIO.PWM(buzzer, 1)
    ledPWM = GPIO.PWM(LED_accuracy, 50)
    #set all used pins to low
    GPIO.output(LED_value[0], GPIO.LOW)
    GPIO.output(LED_value[1], GPIO.LOW)
    GPIO.output(LED_value[2], GPIO.LOW)
    buzzerPWM.ChangeDutyCycle(0)
    ledPWM.ChangeDutyCycle(0)
    # Setup debouncing and callbacks
    GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback=btn_increase_pressed, bouncetime=200)
    GPIO.add_event_detect(btn_increase, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=200)

    pass
    
    
# Load high scores
def fetch_scores():
    # get however many scores there are
    score_count = eeprom.read_byte(0)
    # Get the scores
    scores = []
    if score_count > 0:
        for i in range(score_count):
            scores.append(eeprom.read_block(i + 1, 4))
            time.sleep(0.01)
    # convert the codes back to ascii
            for x in range(3):
                scores[i][x] = chr(scores[i][x])
    # return back the results
    return score_count, scores


# Save high scores
def save_scores(name):
    # fetch scores
    count, scores = fetch_scores()
    # include new score
    n = list(name)
    n.append(num_guess)
    # sort
    for i in range(int(count)):
        if num_guess < int(scores[i][3]):
            scores.insert(i, n)
            break
    # update total amount of scores
    count += 1
    # write new scores
    eeprom.write_byte(0, count)
    time.sleep(0.01)
    
    for i in range(int(count)):
        for x in range(3):
            scores[i][x] = ord(scores[i][x])
        eeprom.write_block(i + 1, scores[i])
        time.sleep(0.01)
        
    pass


# Generate guess number
def generate_number():
    return random.randint(0, pow(2, 3)-1)


# Increase button pressed
def btn_increase_pressed(channel):
    global current_guess
    if current_guess != 7 :
        current_guess+=1
    else:
        current_guess = 0  
        
    bin = format(current_guess, '03b')

    if int(bin[0]) == 1:
       GPIO.output(LED_value[0], GPIO.HIGH) 
    else:
       GPIO.output(LED_value[0], GPIO.LOW) 
    if int(bin[1]) == 1:
       GPIO.output(LED_value[1], GPIO.HIGH) 
    else:
       GPIO.output(LED_value[1], GPIO.LOW) 
    if int(bin[2]) == 1:
       GPIO.output(LED_value[2], GPIO.HIGH) 
    else:
       GPIO.output(LED_value[2], GPIO.LOW) 

    pass


# Guess button
def btn_guess_pressed(channel):
    global value, current_guess, num_guess
    start_time = time.time()
    while GPIO.input(channel) == 0:
        pass
    button_time = time.time() - start_time
    
    if button_time < 0.65:
        num_guess+=1
        if current_guess - value != 0:
            trigger_buzzer()
            accuracy_leds()
        else: 
            GPIO.output(LED_value[0], GPIO.LOW)
            GPIO.output(LED_value[1], GPIO.LOW)
            GPIO.output(LED_value[2], GPIO.LOW)
            buzzerPWM.ChangeDutyCycle(0)
            ledPWM.ChangeDutyCycle(0)
            current_guess = 0

            print("Congratulations! You have guessed correctly")
            name = input("Please enter a three letter name to immortalise your score: ")
            name_length = 0
            while name_length !=1:
                if len(name) >3:
                    name = input("That name is too long. Please enter a three letter name: ")
                elif len(name)<3:
                    name = input("That name is too short. Please enter a three letter name: ")
                else:
                    name_length = 1
        
            save_scores(name)
            count, scores = fetch_scores()
            menu()
    else:
        GPIO.output(LED_value[0], GPIO.LOW)
        GPIO.output(LED_value[1], GPIO.LOW)
        GPIO.output(LED_value[2], GPIO.LOW)
        buzzerPWM.ChangeDutyCycle(0)
        ledPWM.ChangeDutyCycle(0)
        current_guess = 0
        menu()
        
    pass


# LED Brightness
def accuracy_leds():
    global first_time, value, current_guess
            
    dutyCycle = 100 - abs(value-current_guess)/7*100

    if first_time == 1:
        ledPWM.ChangeFrequency(50)
        ledPWM.start(dutyCycle)
        first_time = 0

    else:
        ledPWM.ChangeDutyCycle(dutyCycle)
    pass

# Sound Buzzer
def trigger_buzzer():
    if abs(value - current_guess) >= 3:
        buzzerPWM.start(50)
    elif abs(value - current_guess) == 2:
        buzzerPWM.ChangeFrequency(2)
        buzzerPWM.start(50)
    elif abs(value - current_guess) == 1:
        buzzerPWM.ChangeFrequency(4)
        buzzerPWM.start(50)    
    pass

if __name__ == "__main__":
    try:
        # Call setup function
        setup()
        welcome()
        while True:
            menu()
            pass
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
