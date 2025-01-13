from dotenv import load_dotenv
import os
import json
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

# Histórico de usuários
user_history = {}

# Função para carregar o histórico de um arquivo JSON
def load_history_from_file():
    global user_history
    try:
        with open("user_history.json", "r", encoding='utf-8') as file:
            user_history = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        user_history = {}

# Função para salvar o histórico em um arquivo JSON
def save_history_to_file():
    try:
        with open("user_history.json", "w", encoding='utf-8') as file:
            json.dump(user_history, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar o histórico: {e}")

# Carrega o histórico ao iniciar o bot
load_history_from_file()

# Dicionário para armazenar matrículas temporariamente durante o registro
pending_registrations = {}

# Contexto restrito para matemática do ensino fundamental
MATH_CONTEXT = """
Você é um tutor de matemática especializado no ensino fundamental (1º ao 9º ano).
Responda apenas a perguntas relacionadas a matemática desse nível educacional.
Se a pergunta não for relacionada a matemática ou estiver fora do escopo, responda:
"Desculpe, só posso ajudar com matemática do ensino fundamental."
"""

# Primeiro passo: Solicita a matrícula ao usuário
@bot.message_handler(commands=['start'])
def request_matricula(message):
    msg = bot.reply_to(message, "Olá! Para começar, por favor, digite sua matrícula:")
    bot.register_next_step_handler(msg, verify_matricula)

# Verifica se a matrícula existe no histórico
def verify_matricula(message):
    chat_id = message.chat.id
    matricula = message.text.strip()

    if matricula in user_history:
        user_data = user_history[matricula]
        bot.reply_to(message, f"Bem-vindo de volta, {user_data['nome']}! Como posso ajudá-lo hoje?")
        
        # ⚡ Armazena a matrícula corretamente para futuras interações
        pending_registrations[chat_id] = matricula  
    else:
        bot.reply_to(message, "Matrícula não encontrada. Vamos fazer seu registro.")
        pending_registrations[chat_id] = matricula  # Armazena a matrícula para continuar o registro
        msg = bot.reply_to(message, "Por favor, digite seu nome:")
        bot.register_next_step_handler(msg, process_name)

# Processo de registro de novo usuário
def process_name(message):
    chat_id = message.chat.id
    nome = message.text.strip()
    matricula = pending_registrations.get(chat_id)

    if not matricula:
        bot.reply_to(message, "Erro ao recuperar a matrícula. Tente novamente usando /start.")
        return

    user_history[matricula] = {"nome": nome, "turma": None, "professor": None, "interacoes": []}
    
    msg = bot.reply_to(message, f"Obrigado, {nome}! Agora, envie o nome da sua turma:")
    bot.register_next_step_handler(msg, process_class, matricula)

def process_class(message, matricula):
    turma = message.text.strip()
    user_history[matricula]["turma"] = turma

    msg = bot.reply_to(message, f"Entendido! Agora, envie o nome do(a) professor(a):")
    bot.register_next_step_handler(msg, process_teacher, matricula)

def process_teacher(message, matricula):
    professor = message.text.strip()
    user_history[matricula]["professor"] = professor

    bot.reply_to(message, f"Registro completo! Bem-vindo(a), {user_history[matricula]['nome']}!")
    
    # Salva o histórico após o registro
    save_history_to_file()

# Manipulador de mensagens para interação normal após o login
@bot.message_handler(func=lambda message: True)
def respond_to_message(message):
    chat_id = message.chat.id

    # Verifica se temos a matrícula salva para esse chat_id
    if chat_id not in pending_registrations:
        msg = bot.reply_to(message, "Antes de prosseguirmos, por favor, informe sua matrícula:")
        bot.register_next_step_handler(msg, verify_matricula)
        return

    # Recupera a matrícula salva para esse usuário
    matricula = pending_registrations[chat_id]

    # ⚡ Verifica corretamente se a matrícula existe no histórico
    if matricula in user_history:
        user_data = user_history[matricula]

        # Adiciona a interação ao histórico
        user_data["interacoes"].append({"role": "user", "text": message.text})

        try:
            # Envia o prompt com contexto para a IA
            response = model.generate_content(MATH_CONTEXT + "\nUsuário: " + message.text + "\nIA:")

            # Adiciona a resposta ao histórico
            user_data["interacoes"].append({"role": "bot", "text": response.text})

            # Envia a resposta ao usuário
            bot.reply_to(message, response.text)

        except Exception as e:
            bot.reply_to(message, "Houve um problema ao processar sua solicitação. Tente novamente mais tarde.")

        # Salva o histórico após a interação
        save_history_to_file()
    else:
        bot.reply_to(message, "Matrícula não reconhecida. Por favor, inicie novamente com /start.")

# Inicia o bot
bot.polling()
