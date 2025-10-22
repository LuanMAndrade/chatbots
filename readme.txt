Funcionalidades do robô
•	Recebe mensagens fracionadas
•	Envia mensagens fracionadas
•	Entende áudio
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
•	Faz agendamento

Apresentação
•	1 Semana grátis pra Testar
•	Pedir numero backup
•	Criar o cal.com


Mudar para novo projeto
•	Mudar nome da pasta "bot_nome"
•	Criar usuario no django
•	Criar usuario evolution com o mesmo nome da pasta
•	Configurar evolution
•	Preencher portas no readme.txt
•	Criar os services do bot e agendador no systemd
•	Usar os comandos no terminal para ativar: sudo systemctl daemon-reload -> sudo systemctl enable {bot_model} -> sudo systemctl start {bot_model}
•	Para o agendador tambem
•	.env
•	Testar agendador, uma mensagem e o consumo
•	Pedir numero de backup
•	Criar o cal.com
•	Reiniciar os serviços
•	Mudar o billing day


sudo systemctl restart bot_
sudo journalctl -u bot_ -f

sudo systemctl daemon-reload
sudo systemctl enable {bot_model}
sudo systemctl start {bot_model}

docker compose restart django_app

Portas:

bot_sejasua = 8001
bot_model = 8002
bot_lorena = 8003