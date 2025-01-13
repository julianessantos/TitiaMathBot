from dotenv import load_dotenv
import os
import json
import google.generativeai as genai
import telebot
import time

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

# Função para verificar se o ID já foi registrado
def get_user_history(user_id):
    global user_history
    if user_id not in user_history:
        return None  # Usuário não registrado
    return user_history[user_id]  # Retorna o histórico do usuário

# Carrega o histórico ao iniciar o bot
load_history_from_file()

# Define o comando de registro
@bot.message_handler(commands=['registrar'])
def register_user(message):
    user_id = message.chat.id

    # Verifica se o usuário já está registrado
    if get_user_history(user_id):
        bot.reply_to(message, "Você já está registrado!")
        return

    # Solicita informações do usuário
    msg = bot.reply_to(message, "Olá! Para começar, por favor, envie seu nome:")
    bot.register_next_step_handler(msg, process_name)

def process_name(message):
    user_id = message.chat.id
    user_name = message.text

    # Inicializa o histórico do usuário com as informações básicas
    user_history[user_id] = {
        "nome": user_name,
        "turma": None,
        "professor": None,
        "interacoes": []
    }

    msg = bot.reply_to(message, "Obrigado, {0}! Agora, envie o nome da sua turma:".format(user_name))
    bot.register_next_step_handler(msg, process_class)

def process_class(message):
    user_id = message.chat.id
    class_name = message.text

    user_history[user_id]["turma"] = class_name

    msg = bot.reply_to(message, "Entendido! Agora, envie o nome do(a) professor(a):")
    bot.register_next_step_handler(msg, process_teacher)

def process_teacher(message):
    user_id = message.chat.id
    teacher_name = message.text

    user_history[user_id]["professor"] = teacher_name

    bot.reply_to(message, "Registro completo! Bem-vindo(a), {0}!".format(user_history[user_id]["nome"]))

    # Salva o histórico após o registro
    save_history_to_file()

# Função para gerar uma resposta padrão educativa
def generate_generic_educational_response():
    return (
        "Parece que sua pergunta não está diretamente relacionada à matemática do ensino fundamental. "
        "Aqui estão algumas coisas que você pode perguntar:\n"
        "- Como resolver uma equação?\n"
        "- O que é uma fração?\n"
        "- Qual é a fórmula da área de um círculo?\n"
        "Tente perguntar algo relacionado a números ou cálculos!"
    )

# Função para enviar respostas grandes em partes
def send_large_message(bot, chat_id, text, chunk_size=4096):
    for i in range(0, len(text), chunk_size):
        bot.send_message(chat_id, text[i:i+chunk_size])
        time.sleep(1)  # Para evitar problemas com muitas mensagens rápidas

# Define o manipulador para mensagens de texto
@bot.message_handler(func=lambda message: True)
def respond_to_message(message):
    user_id = message.chat.id
    user_text = message.text

    # Verifica se o usuário está registrado
    user_data = get_user_history(user_id)
    if not user_data:
        bot.reply_to(message, "Por favor, registre-se usando o comando /registrar antes de continuar.")
        return

    # Adiciona a interação ao histórico
    user_data["interacoes"].append({"role": "user", "text": user_text})

    try:
        # Gera uma resposta com base no texto da mensagem recebida
        response = model.generate_content(user_text)

        # Adiciona a resposta ao histórico
        user_data["interacoes"].append({"role": "bot", "text": response.text})

        # Envia a resposta ao usuário, verificando se a resposta é grande
        send_large_message(bot, user_id, response.text)

    except Exception as e:
        error_message = f"Erro ao gerar resposta: {e}"
        print(error_message)
        bot.reply_to(message, "Houve um problema ao processar sua solicitação. Por favor, tente novamente mais tarde.")

    # Salva o histórico após a interação
    save_history_to_file()

    # Exemplo de log do histórico no terminal (opcional)
    print(f"Histórico do usuário {user_id}: {user_data}")

# Define o comando para exportar o histórico
@bot.message_handler(commands=['exportar'])
def export_history(message):
    try:
        save_history_to_file()
        bot.reply_to(message, "Histórico exportado com sucesso para 'user_history.json'.")
    except Exception as e:
        bot.reply_to(message, f"Erro ao exportar o histórico: {e}")

# Inicia o bot
bot.polling()