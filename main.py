from dotenv import load_dotenv
import os
import google.generativeai as genai
import telebot

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Obtém a variável de ambiente 'APIKEY' para o Google Generative AI
api_key = os.getenv('APIKEY')

# Verifica se a chave da API foi carregada corretamente
if not api_key:
    print("Erro: a chave APIKEY não foi encontrada no arquivo .env")
else:
    print("API key do Google Generative AI carregada com sucesso")

# Configura o modelo com a chave da API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# Configuração do bot do Telegram
API_KEY_TELEGRAM = os.getenv('TELEGRAMKEY')  # A chave de API do Telegram

if not API_KEY_TELEGRAM:
    print("Erro: a chave TELEGRAMKEY não foi encontrada no arquivo .env")
else:
    print("Chave do Telegram carregada com sucesso")
    
bot = telebot.TeleBot(API_KEY_TELEGRAM)

# Define o manipulador para mensagens de texto
@bot.message_handler(func=lambda message: True)
def respond_to_message(message):
    # Gera uma resposta com base no texto da mensagem recebida
    response = model.generate_content(message.text)  
    bot.reply_to(message, response.text)  # Envia a resposta ao usuário

# Inicia o bot
bot.polling()
