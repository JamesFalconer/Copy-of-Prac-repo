# Import libraries
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os

# some global variables that need to change as we run the program
end_of_game = None  # set if the user wins or ends the game

current_guess = 0
first_time = 0

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


def display_scores(count, raw_data):
    # print the scores to the screen in the expected format
    count, scores = fetch_scores()
    print("There are {} scores. Here are the top 3!".format(count))
    # print out the scores in the required format
    if count>=3:
        for i in range(3):
            print(str(i+1)+ " - "+ scores[i + 1][0]+ scores[i + 1][1]+ scores[i + 1][2]+ " took "+ scores[i + 1][3]+ " guesses")
    else:
        for i in range(count):
            print(str(i+1)+ " - "+ scores[i + 1][0]+ scores[i + 1][1]+ scores[i + 1][2]+ " took "+ scores[i + 1][3]+ " guesses")
    
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
    ledPWM = GPIO.PWM(LED_accuracy, 1000)
    # Setup debouncing and callbacks
    GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback=btn_increase_pressed, bouncetime=200)
    GPIO.add_event_detect(btn_increase, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=200)

    pass
    
    
# Load high scores
def fetch_scores():
    # get however many scores there are
    score_count = eeprom.read_block(0, 1)
    # Get the scores
    scores = []
    for i in range (1, 4):
        scores[i - 1] = eeprom.read_block(i, 4)
    # convert the codes back to ascii
        for x in 3:
            scores[i - 1][x] = chr(scores[i - 1][x])
    # return back the results
    return score_count, scores


# Save high scores
def save_scores(name):
    # fetch scores
    count, scores = fetch_scores()
    # include new score
    n = list(name)
    n.append(current_guess)
    # sort
    for i in count:
        if current_guess < int(scores[i + 1][3]):
            scores.insert(i + 1, n)
    # update total amount of scores
    count += 1
    # write new scores
    eeprom.write_block(0, count)
    for i in count:
        for x in 3:
            scores[i + 1][x] = orc(scores[i + 1][x])
        eeprom.write_block(i + 1, scores)
        
    pass


# Generate guess number
def generate_number():
    return random.randint(0, pow(2, 3)-1)


# Increase button pressed
def btn_increase_pressed(channel):
    global current_guess
    # Increase the value shown on the LEDs
    # You can choose to have a global variable store the user's current guess, 
    # or just pull the value off the LEDs when a user makes a guess

    if current_guess != 7 :
        current_guess+=1
    else:
        current_guess = 0  
        
    bin = format(current_guess, '03b')

    
    print(bin)
    print(bin[0])
    print(bin[1])
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
    global value
    global current_guess
    # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
    # Compare the actual value with the user value displayed on the LEDs
    # Change the PWM LED
    # if it's close enough, adjust the buzzer
    # if it's an exact guess:
    # - Disable LEDs and Buzzer
    # - tell the user and prompt them for a name
    # - fetch all the scores
    # - add the new score
    # - sort the scores
    # - Store the scores back to the EEPROM, being sure to update the score count
    if current_guess - value != 0:
        trigger_buzzer()
        accuracy_leds()
    else: 
        GPIO.output(LED_value[0], GPIO.LOW)
        GPIO.output(LED_value[1], GPIO.LOW)
        GPIO.output(LED_value[2], GPIO.LOW)
        buzzerPWM.ChangeDutyCycle(0)
        ledPWM.ChangeDutyCycle(0)
        
        print("Congratulations! You have guessed correctly")
        name = input("Please enter a three letter name to immortalise your score: ")
        if len(name) >3:
            name = input("That name is too long. Please enter a three letter name: ")
        
        save_scores(name)
        count, scores = fetch_scores()
        
        
    pass


# LED Brightness
def accuracy_leds():
    global first_time
    # Set the brightness of the LED based on how close the guess is to the answer
    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%
            
    dutyCycle = 100 - abs(value-current_guess)/7*100
    
    if first_time == 1:
        ledPWM.start(dutyCycle)
        first_time = 0
    else:
        ledPWM.ChangeDutyCycle(dutyCycle)
    pass

# Sound Buzzer
def trigger_buzzer():
    # The buzzer operates differently from the LED
    # While we want the brightness of the LED to change(duty cycle), we want the frequency of the buzzer to change
    # The buzzer duty cycle should be left at 50%
    # If the user is off by an absolute value of 3, the buzzer should sound once every second
    # If the user is off by an absolute value of 2, the buzzer should sound twice every second
    # If the user is off by an absolute value of 1, the buzzer should sound 4 times a second
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
