import telebot
import subprocess
import re
import random
import string
import time
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np
import requests

sys.stdout.flush()

TOKEN = '' #telegram bot token
YOUR_EOS_ACCOUNT = 'spt'
bot = telebot.TeleBot(TOKEN)
verified_users_file = 'verified_users.txt'


user_verification_codes = {}


if not os.path.exists(verified_users_file):
    open(verified_users_file, 'w').close()


def generate_verification_code(length=6):
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
    code = ''.join(random.choice(characters) for i in range(length))
    return code


def generate_code_image(code):
    image_width = 250
    image_height = 100


    background_color = tuple(np.random.randint(0, 255, size=3))

    image = Image.new('RGB', (image_width, image_height), background_color)
    draw = ImageDraw.Draw(image)


    for _ in range(300):
        x = np.random.randint(0, image_width)
        y = np.random.randint(0, image_height)
        color = tuple(np.random.randint(0, 255, size=3))
        draw.text((x, y), chr(np.random.randint(33, 127)), fill=color)


    font_path = random.choice(["DejaVuSans-Bold.ttf","DejaVuSans.ttf","Dustismo_Roman.ttf"])

    font_size = 40
    font = ImageFont.truetype(font_path, font_size)


    text_x = 30
    text_y = 30
    text_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    draw.text((text_x, text_y), code, font=font, fill=text_color)


    image_buffer = io.BytesIO()
    image.save(image_buffer, format='PNG')
    image_buffer.seek(0)

    return image_buffer


def is_user_verified(user_id):
    with open(verified_users_file, 'r') as file:
        for line in file:
            if str(user_id) == line.strip():
                return True
    return False

@bot.message_handler(func=lambda message: message.chat.type == 'group')
def handle_group_message(message):
    print(message)

# /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    
    if not is_user_verified(chat_id):
        verification_code = generate_verification_code()

        image_buffer = generate_code_image(verification_code)

        bot.send_photo(chat_id, photo=image_buffer)
        bot.send_message(chat_id, "Please enter the code in the image.")

        user_verification_codes[chat_id] = verification_code
    else:
        bot.send_message(chat_id, "You are already verified.")

        with open('support.jpg', 'rb') as photo:
         bot.send_photo(chat_id, photo, caption='https://eossupport.io')
        
         hyperlink_text1 = '<a href="https://help.eossupport.io/en/articles/6636626-how-to-import-a-private-key-into-the-anchor-wallet-after-a-fresh-installation">Import your private key into an EOS Wallet</a>'
         hyperlink_text2 = '<a href="https://help.eossupport.io/en/collections/3131866-use-your-eos">learn here what you can do with it.</a>'
         plain_text = "Welcome to the EOS support account creation service!\n\nPlease send your EOS public key to get a free EOS Account.\n\nIf you don't have a public key, you can create one using the command \"/keypairs\".\n\nAfter obtaining your public key, use the command \"/powerup <your account name>\" to power up your EOS account for free.\n\nWe created an account ending in .spt. If you want a customized account, please send <custom fields>.spt-<public key>\n\nIt's simple and easy!\n\nIf you need help, go to https://eossupport.io\n\n"

         message_text = f"After account creation, {hyperlink_text1} and {hyperlink_text2}\n"

         bot.send_message(chat_id, text = plain_text )
         bot.send_message(chat_id, text=message_text, parse_mode='HTML')

@bot.message_handler(commands=['keypairs'])
def send_keypairs(message):
    chat_id = message.chat.id
    cmd = f'cleos create key --to-console'
    output = subprocess.check_output(cmd, shell=True)

    bot.send_message(chat_id, f"Please register with the Public Key and keep the Private Key safely！\n\n{output.decode('utf-8')}")
    private_key, public_key = extract_keys(output.decode('utf-8'))

    bot.send_message(chat_id, f"Use the Public Key to get an EOS account, Copy the Public Key below and send it in in the chat.")
    bot.send_message(chat_id, f"{public_key}")
    
    hyperlink_text = '<a href="https://help.eossupport.io/en/articles/5955271-how-to-change-your-keypairs-for-your-eos-account">the step-by-step link</a>'
    message_text = f"SECURITY WARNING: Revealing Private Keys in Telegram poses a high risk. Please CHANGE YOUR KEYPAIRS after account creation. Here is a step-by-step tutorial on how to change KEYPAIRS after account creation.{hyperlink_text}"
    
    bot.send_message(chat_id, text=message_text, parse_mode='HTML')
    
@bot.message_handler(commands=['powerup'])
def send_powerup(message):
    print (message.text)
    account_name = message.text[8:].strip()
    print("Power Up: ",account_name)
    chat_id = message.chat.id
    print("Chat ID: ",chat_id)

    if (chat_id == ""): #admin id
       cmd = f'cat support.pass|cleos wallet unlock -n support'
       output = subprocess.run(cmd, shell=True)
    
       cmd = f'cleos push action eosio powerup \'["spt","{account_name}","1","31428741","157143707","0.0050 EOS"]\' -p spt@create'

       try:
    
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        if result.returncode == 0:
         print("Command executed successfully.")
         print("Command output:", result.stdout)
         bot.send_message(chat_id, f"Success Dear")
        else:
         print("Error executing command.")
         print("Error output:", result.stderr)
         bot.send_message(chat_id, f"Fail Dear")
        
         if (result.stderr.find("3080004") != -1 or result.stderr.find("3080002") != -1):
                print("Error code 3080004 detected. Proceeding with next code.")
                cmd = f'cleos push action eosio powerup \'["spt","spt","1","31428741","257143707","0.0100 EOS"]\' -p spt@create'
                result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

                if result.returncode == 0:
                      print("Command executed successfully.")
                      print("Command output:", result.stdout)
                      bot.send_message(chat_id, f"Power Up spt Success Dear")
                else:
                      print("Error executing command.")
                      print("Error output:", result.stderr)
                      bot.send_message(chat_id, f"Power Up spt Fail  Dear")
 
              
         else:
              print("Error code 3080004 or 3080002  not found.")
              bot.send_message(chat_id, f"Not 3080004 error  Dear")

       except Exception as e:
        print("An error occurred:", str(e))
        bot.send_message(chat_id, f"Error Dear:{e}") 
       return

    exists = is_account_exist(account_name)
    if exists:
       print(f"account {account_name} exist")
       # update_user_time(chat_id)
       # update_account_time(account_name)

       if (update_user_time(chat_id)  and update_account_time(account_name) ):
          print ("P")
          cmd = f'cat support.pass|cleos wallet unlock -n support '
          output = subprocess.run(cmd, shell=True)

          cmd = f'cleos push action eosio powerup \'["spt","{account_name}","1","31428741","157143707","0.0050 EOS"]\' -p spt@create'
   
          try:
    
             result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

             if result.returncode == 0:
                print("Command executed successfully.")
                print("Command output:", result.stdout)
                bot.send_message(chat_id, f"Success Power Up")
             else:
                print("Error executing command.")
                print("Error output:", result.stderr)

                if (result.stderr.find("3080004") != -1):
                   print("Error code 3080004 detected. Proceeding with next code.")
                   cmd = f'cleos push action eosio powerup \'["spt","spt","1","31428741","257143707","0.0050 EOS"]\' -p spt@create '
                   result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                                  
                   if result.returncode == 0:
                     print("Command executed successfully.")
                     print("Command output:", result.stdout)
                     time.sleep(3) 
                     if(power_up_account(account_name)):
                       bot.send_message(chat_id, f"Power Up Success.")
                     else:
                       bot.send_message(chat_id, f"Power Up Error.")

                   else:
                     print("Error executing command.")
                     print("Error output:", result.stderr)
                
                elif (result.stderr.find("3080001") != -1):
                   print("Error code 3080001 detected. Proceeding with next code.")
                   cmd = f'cleos system buyram spt spt --kbytes 1  -p spt@create '
                   result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

                   if result.returncode == 0:
                     print("Command executed successfully.")
                     print("Command output:", result.stdout)
                     time.sleep(3)
                     if(power_up_account(account_name)):
                        bot.send_message(chat_id, f"Power Up Success.")
                     else:
                       bot.send_message(chat_id, f"Power Up Error.")

                   else:
                     print("Error executing command.")
                     print("Error output:", result.stderr)


                else:
                  print("Error code 3080004 3080001 not found.")


          except Exception as e:
            print("An error occurred:", str(e))
            
       else:
        bot.send_message(chat_id, f"Telegram account or EOS account reach time limit try 24 hour later after your last power up")

    else:
       print(f"account {account_name} not exist")
       bot.send_message(chat_id, f"Empty input or EOS Account not exists.\nsend me /powerup <your eos account name>")


@bot.message_handler(func=lambda message: True)
def handle_public_key(message):
 print (message.text)

 user_input_code = message.text.strip()
 chat_id = message.chat.id

    
 if chat_id in user_verification_codes:
        
        correct_code = user_verification_codes[chat_id]

        
        if user_input_code == correct_code:
           
            bot.send_message(chat_id, "Verification successful! Click /start begin.")

            with open(verified_users_file, 'a') as file:
                file.write(f"{chat_id}\n")

            del user_verification_codes[chat_id]
        else:
            bot.send_message(chat_id, "Verification failed. Please try again.")
 else:
    parts=message.text.split('-', 1)

    if len(parts) == 2:
        before_hyphen = parts[0]
        after_hyphen = parts[1]
        public_key = after_hyphen
    else:
        public_key = message.text
    
    print (public_key)
    print (chat_id)
    if is_valid_eos_public_key(public_key):
       if not check_user_exist(chat_id):
         cmd = f'cat support.pass|cleos wallet unlock -n support '
         output = subprocess.run(cmd, shell=True)
         
         if len(parts) == 2:
          account_name = before_hyphen
          exists = is_account_exist(account_name)
          
          if exists:
           bot.send_message(chat_id, f"Account exist,try another please")
           return
          else:
           if not is_string_ends_with_dot_spt(account_name):
             account_name = account_name + ".spt"
         else:   
          account_name = "spt"
           
          while is_account_exist(account_name):
           random_string = generate_random_string()
           print(random_string)
          
           account_name = random_string + ".spt"
             
         cmd = f'cleos system newaccount spt {account_name} {public_key} {public_key} --buy-ram-bytes 3072 --stake-net "0.0000 EOS" --stake-cpu "0.0000 EOS" -p spt@create'
         try:
    
             result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
   
             if result.returncode == 0:
                  print("Command executed successfully.")
                  print("Command output:", result.stdout)
                  
                  hyperlink_text1 = '<a href="https://help.eossupport.io/en/articles/5955271-how-to-change-your-keypairs-for-your-eos-account">this guide</a>'
                  hyperlink_text2 = '<a href="https://help.eossupport.io/en/articles/8304360-eos-support-proxy-delegate-your-voting-power-and-earn-4-apy-rex-rewards">Proxy Offer</a>'
                  hyperlink_text3 = '<a href="https://help.eossupport.io/en/articles/6292189-how-to-install-and-use-the-anchor-wallet">import your EOS Account Private_Key into your EOS Wallet</a>'

                  bot.send_message(chat_id, f"Account creation is successful!\n\nPlease import {hyperlink_text3} (such as Anchor Wallet or Wombat) - Do not share private_key in this Telegram Chat. \n\nAfter importing, your new account’s permissions (Active and Owner) will appear. Follow {hyperlink_text1} to secure your new account with a fresh Owner Key.\n\nThank you for using the EOS Support Account Creation Bot! Enjoy the benefits of your EOS Account and explore our {hyperlink_text2} to earn a secure and passive 4% APY with your EOS." ,parse_mode='HTML')
                  
                 # bot.send_message(chat_id, f"Account creation is successful!\n\nPlease import your EOS Account Private_Key into your EOS Wallet (such as Anchor Wallet or Wombat) - Do not share private_key in this Telegram Chat. \n\nAfter importing, your new account’s permissions (Active and Owner) will appear. Follow {hyperlink_text1} to secure your new account with a fresh Owner Key.\n\nThank you for using the EOS Support Account Creation Bot! Enjoy the benefits of your EOS Account and explore our {hyperlink_text2} to earn a secure and passive 4% APY with your EOS." ,parse_mode='HTML')
                  
                  
                  #bot.send_message(chat_id, text=message_text, parse_mode='HTML')
                  save_user_id(chat_id)
             else:
                  print("Error executing command.")
                  print("Error output:", result.stderr)

                  if (result.stderr.find("3080004") != -1):
                    print("Error code 3080004 detected. Proceeding with next code.")
                    cmd = f'cleos push action eosio powerup \'["spt","spt","1","31428741","257143707","0.0050 EOS"]\' -p spt@create'
                    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                
                #
                    if result.returncode == 0:
                     print("Command executed successfully.")
                     print("Command output:", result.stdout)
                     time.sleep(3)
                     if (create_new_account(account_name,public_key)):
                       bot.send_message(chat_id, f"Create Success\nInput your privite_key to EOS wallet you will see your account.")
                       save_user_id(chat_id)
                     else:
                       bot.send_message(chat_id, f"Create Error,contact Administror or try later.")

                    else:
                     print("Error executing command.")
                     print("Error output:", result.stderr)
                     bot.send_message(chat_id, f"Create Error,contact Administror or try later.")

                  else:
                   print("Error code 3080004 not found.")
                   bot.send_message(chat_id, f"Create Error,contact Administror or try later.")

         except Exception as e:
           print("An error occurred:", str(e))
           bot.send_message(chat_id, f"Create Error,contact Administror or try later.")
       else: 
         bot.send_message(chat_id, "Each telegram can only create one EOS Account")
    else:
      bot.send_message(chat_id, "Public key is not compliant")

def is_valid_eos_public_key(public_key):
    # 
    if len(public_key) != 53:
        return False
    
    # 
    if not public_key.startswith('EOS'):
        return False
    
    # 
    pattern = re.compile('^[A-Za-z0-9]{50}$')
    if not pattern.match(public_key[3:]):
        return False
    
    return True

def is_string_ends_with_dot_spt(input_string):
    cleaned_string = input_string.rstrip()
    return cleaned_string.endswith(".spt")

def generate_random_string():
    characters = string.ascii_lowercase + "12345"
    random_string = ''.join(random.choice(characters) for _ in range(8))
    return random_string

def check_user_exist(user_id):
    if str(user_id) == str("1985996990"):
        return False
    
    open('user_ids.txt', 'a+') 
    with open('user_ids.txt', 'r') as file:
      
        for line in file:
        
            if line.rstrip() == str(user_id):
                return True
    return False

def save_user_id(user_id):
    
    with open('user_ids.txt', 'a+') as file:
        
        file.write(str(user_id) + '\n')

def update_user_time(user_id):
    file_path = "user_records.txt"
    current_time = int (time.time())

    if os.path.exists(file_path):
        with open(file_path, "r+") as file:
            lines = file.readlines()
            file.seek(0)
            found = False

            for line in lines:
                data = line.strip().split(",")
                if int (data[0]) == user_id:
                    found = True
                    last_time = int(data[1])
                    if current_time - last_time > 24*60*60:
                        file.write(f"{user_id},{current_time}\n")
                        return True
                    else:
                        file.write(f"{user_id},{last_time}\n")
                        return False
                else:
                    file.write(line)

            if not found:
                file.write(f"{user_id},{current_time}\n")
                return True
    else:
        with open(file_path, "w") as file:
            file.write(f"{user_id},{current_time}\n")
            return True

    return False

def update_account_time(eos_account):

    file_path = "eosaccount_records.txt"
    current_time = int (time.time())

    if os.path.exists(file_path):
        with open(file_path, "r+") as file:
            lines = file.readlines()
            file.seek(0)
            found = False

            for line in lines:
                data = line.strip().split(",")
                eos_account = eos_account.strip()
                if str (data[0]) == str(eos_account):
                    found = True
                    last_time = int(data[1])
                    if current_time - last_time > 24*60*60:
                        file.write(f"{eos_account},{current_time}\n")
                        return True
                    else:
                        file.write(f"{eos_account},{last_time}\n")
                        return False
                else:
                    file.write(line)

            if not found:
                file.write(f"{eos_account},{current_time}\n")
                return True
    else:
        with open(file_path, "w") as file:
            file.write(f"{eos_account},{current_time}\n")
            return True

    return False

def is_account_exist(account_name):
    try:
        result = subprocess.run(['cleos', 'get', 'account', account_name], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        return False

def power_up_account(account_name):
    cmd = f'cleos push action eosio powerup \'["spt","{account_name}","1","31428741","157143707","0.0050 EOS"]\' -p spt@create'

    try:
    # 
       result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    
    # 
       if result.returncode == 0:
         print("Command executed successfully.")
         print("Command output:", result.stdout)
         return True
       else:
         print("Error executing command.")
         print("Error output:", result.stderr)
         return False

    except Exception as e:
      print("An error occurred:", str(e))
      return False

def create_new_account(account_name,public_key):
    cmd = f'cleos system newaccount spt {account_name} {public_key} {public_key} --buy-ram-bytes 3072 --stake-net "0.0000 EOS" --stake-cpu "0.0000 EOS" -p spt@create'

    try:
    # 
       result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    # 
       if result.returncode == 0:
         print("Command executed successfully.")
         print("Command output:", result.stdout)
         return True
       else:
         print("Error executing command.")
         print("Error output:", result.stderr)
         return False

    except Exception as e:
      print("An error occurred:", str(e))
      return False

def extract_keys(text):
    private_key_start = text.find("Private key:")
    public_key_start = text.find("Public key:")
    
    if private_key_start != -1:
        private_key_start += len("Private key:")
        private_key = text[private_key_start:].strip()
    else:
        private_key = None

    if public_key_start != -1:
        public_key_start += len("Public key:")
        public_key = text[public_key_start:].strip()
    else:
        public_key = None

    return private_key, public_key
   
# 
while True:
    try:
        bot.polling()
    except requests.exceptions.ReadTimeout as e:
        print('ReadTimeout exception occurred. Retrying polling...')
        continue
    except Exception as e:
        print('An exception occurred:', str(e)) 
        continue
       # break  
