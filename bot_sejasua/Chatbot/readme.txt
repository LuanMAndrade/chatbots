A fazer:

Congelamento --> melhorar codigo
Audio --> acertar
Deixar codigo automatizado


Funcionalidades do robô
•	Recebe mensagens fracionadas
•	Envia mensagens fracionadas
•	Recebe áudio
•	Entende quando uma mensagem anterior é referenciada
•	Pausa quando humano assumir o atendimento
•	Aparece o “digitando” antes de enviar a mensagem
•	Sabe todas as informações do estoque e responde baseada nele
•	Atualiza o estoque em tempo real
•	Monta carrinho de desejos enquanto atende
•	Faz sugestões de produtos baseado no interesse do cliente
•	Tem conhecimento das informações da empresa (Horarios, endereço, formas de pagamento, etc)
•	Atendimento humanizado
•	Envia imagens
•	Quando não souber responder envia mensagem no whatsapp pessoal do dono para que este assuma o atendimento
•	Quando identifica intenção de pagamento envia mensagem no whatsapp pessoal do dono para finalizar

O que pedir ao cliente
•	Informações da loja
•	Informações do estoque
•	Número para backup


O que mudar na implementação de um chatbot novo
•	Arquivo .env
•	Documentos em (data)
•	Rodar o arquivo memória
•	Rodar o requirements.txt
•	Copiar a pasta bot-model e renomear
•	Criar um repositório github
•	Entrar no http://31.97.92.54:8081/manager/
•	Instanciar




Deixar rodando full no servidor

COMANDO: 
sudo nano /etc/systemd/system/chatbot.service

COPIE E COLE LÁ:
Description=Chatbot com Uvicorn
After=network.target

[Service]
User=root
WorkingDirectory=/root/chatbots/bot_sejasua/Chatbot
ExecStart=/root/chatbots/bot_sejasua/Chatbot/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always
[Install]
WantedBy=multi-user.target

CTRL + O, ENTER, CTRL X


COMANDO:  sudo systemctl daemon-reload
COMANDO:  sudo systemctl restart chatbot
COMANDO:  sudo systemctl status chatbot

Ver os logs
COMANDO:  sudo journalctl -u chatbot -f

Parar o bot
COMANDO:  sudo systemctl stop chatbot

COMANDO:  Startar depois de parar:
sudo systemctl start chatbot

Restartar o bot:
COMANDO:  sudo systemctl restart chatbot

Ver os status
COMANDO:  sudo systemctl status chatbot




sudo nano /etc/nginx/sites-available/chatbotslmas

server {
    listen 80;
    server_name chatbotslmas.shop;

    location /webhook {
        proxy_pass http://127.0.0.1:8001/;
    }

    location /chatbot2/ {
        proxy_pass http://127.0.0.1:8002/;
    }

    location /chatbot3/ {
        proxy_pass http://127.0.0.1:8003/;
    }
}


