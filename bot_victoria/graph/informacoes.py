from langchain_core.tools import tool
from langchain_community.document_loaders import TextLoader
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
documento = BASE_DIR/'data/inf_loja.txt'
informacoes = TextLoader(documento, encoding='utf-8').load()[0].page_content


@tool
def informacoes():
    """Retorna informaões sobre a loja. São informações gerais, do tipo: Atende remoto?, Qual o endereço?, Como funciona o serviço?, Quais são os produtos?, Pacotes e Preços?, etc."""
    informacoes = """
[COMO_FUNCIONA]
- Objetivo: ajudar a conquistar resultados de forma eficiente, realista e sustentável.
- Foco: autonomia do paciente (alta planejada quando atingir os objetivos).
- Encontros pontuais podem ser marcados após a alta.
- Suporte contínuo por WhatsApp para dúvidas e ajustes.
- Entrega do planejamento alimentar em até 48h após a consulta.
[/COMO_FUNCIONA]

[CONSULTAS]
### Duração ###
- Presencial: 60 a 90 minutos
- Online (Google Meet ou WhatsApp Vídeo): 60 minutos

### Avaliação corporal ###
- Presencial: bioimpedância, antropometria e fotos
- Online: bioimpedância virtual (IA), medidas de circunferência e fotos
[/CONSULTAS]

[PACOTES_E_PRECOS]
## Consulta Premium (Presencial) ##
Avulsa: R$ 315,00
Pacote 4 consultas: R$ 1.012,00 (R$ 253 cada)
Pacote 7 consultas: R$ 1.505,00 (R$ 215 cada)
Benefícios: avaliações, aplicativo Dietbox, consultoria extra, suporte diário WhatsApp/Meet, e-book de receitas

## Consulta Economic (Online) ##
Avulsa: R$ 235,00
Pacote 4 consultas: R$ 700,00 (R$ 175 cada)
Pacote 7 consultas: R$ 1.085,00 (R$ 155 cada)
Benefícios: bioimpedância virtual, aplicativo Dietbox, suporte diário WhatsApp/Meet

## Consulta Premium Especial (Presencial) ##
Avulsa: R$ 400,00
Benefícios: avaliação antropométrica + calorimetria (fisiologista), Dietbox, acompanhamento por 45 dias
[/PACOTES_E_PRECOS]

[CONTATOS_ENDERECOS]
- WhatsApp: (21) 98068-2353 (resposta até o fim do dia; urgências por ligação)
- E-mail: mnlorena.batista@gmail.com
- Instagram: @minhanutrilorenabatista

## Locais de atendimento presencial ##
- Vespasiano: R. Ver. Dumas Chalita, 16 - Centro
- Belo Horizonte: R. Geralda Cirino Flôr de Maio, 111 - Santa Monica
[/CONTATOS_ENDERECOS]
"""
    return informacoes