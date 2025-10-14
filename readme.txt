Mudar:
- Dados do negócio no .env
- Mudar os dados no dashboard evolution
- Criar um arquivo novo em etc>systemd>system com o nome_do_projeto.service

**Mudar o que tiver entre chaves**
porta e nome da pasta

[Unit]
Description=Chatbot Model com Uvicorn
After=network.target

[Service]
User=root
WorkingDirectory=/root/chatbots/{bot_model}
ExecStart=/root/chatbots/{bot_model}/venv/bin/uvicorn main:app --host 0.0.0.0 --port {8002}
Restart=always

[Install]
WantedBy=multi-user.target

- Comando no terminal: 
sudo systemctl daemon-reload
sudo systemctl enable {bot_model}
sudo systemctl start {bot_model}


