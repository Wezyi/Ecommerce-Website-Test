#!/usr/bin/env bash
# Sair se der erro
set -o errexit

# 1. Instalar as dependências
pip install -r requirements.txt

# 2. Recolher os ficheiros estáticos (CSS/Imagens)
python manage.py collectstatic --no-input

# 3. Criar as tabelas na base de dados nova (Postgres)
python manage.py migrate

# 4. CRIAR O ADMIN AUTOMATICAMENTE (LINHA NOVA)
python setup/criar_admin.py