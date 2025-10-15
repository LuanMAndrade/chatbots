# 1. Usar uma imagem oficial do Python como base
FROM python:3.13

# 2. Definir variáveis de ambiente para o Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Criar e definir o diretório de trabalho dentro do container
WORKDIR /app

# 4. Instalar as dependências do sistema necessárias
# --- ADICIONADO: iputils-ping para diagnóstico de rede ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# 5. Instalar as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar o restante do código do seu projeto para o diretório de trabalho
COPY . .

# 7. Expor a porta que o container vai usar
EXPOSE 8000

# 8. O comando para iniciar a aplicação quando o container for executado
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]