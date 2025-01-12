import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes



# Configure suas chaves
TELEGRAM_TOKEN = "7924722785:AAERaO9FClK171l6y2h3mKkh6hae5GVyGqU"
OPENAI_API_KEY = "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"  # Coloque sua chave da OpenAI aqui

openai.api_key = OPENAI_API_KEY

# Função para processar as respostas do chatbot
def chatbot_response(message):
    try:
        # Usando o modelo gpt-3.5-turbo
        response = openai.Completion.create(
            model="gpt-3.5-turbo",  # Modelo mais atual para chat
            prompt=message,
            max_tokens=150
        )
        return response['choices'][0]['text']  # Retorna a resposta
    except Exception as e:
        print("Erro:", e)  # Exibe o erro no console
        return "Desculpe, algo deu errado. Tente novamente mais tarde."

# Função para responder ao comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Olá! Sou o Tutor de Matemática. Envie sua dúvida!")

# Função para lidar com mensagens de texto
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    bot_response = chatbot_response(user_message)
    await update.message.reply_text(bot_response)

# Função principal
def main():
    # Configurar o bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Adicionar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Iniciar o bot
    print("Bot está rodando no Telegram...")
    application.run_polling()

if __name__ == "__main__":
    main()
