#!/bin/bash
# Script de teste local para validar a automação antes de executar no CodeBuild
# 
# Usage:
#   ./test_local.sh [--skip-zip] [--skip-upload]

set -e  # Exit on error

echo "=========================================="
echo "Teste Local - Automação de Documentação"
echo "=========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se .env existe
if [ ! -f .env ]; then
    log_error "Arquivo .env não encontrado!"
    log_info "Copie .env.example para .env e configure suas credenciais:"
    log_info "  cp .env.example .env"
    log_info "  # Edite .env com suas credenciais"
    exit 1
fi

# Carregar variáveis de ambiente
log_info "Carregando variáveis de ambiente do .env..."
export $(cat .env | grep -v '^#' | xargs)

# Verificar variáveis obrigatórias
log_info "Verificando variáveis de ambiente obrigatórias..."

if [ -z "$MODERNIZATION_API_KEY" ] || [ "$MODERNIZATION_API_KEY" = "your-api-key-here" ]; then
    log_error "MODERNIZATION_API_KEY não configurada no .env"
    exit 1
fi

if [ -z "$MODERNIZATION_ORG_ID" ]; then
    log_error "MODERNIZATION_ORG_ID não configurada no .env"
    exit 1
fi

if [ -z "$MODERNIZATION_API_URL" ]; then
    log_error "MODERNIZATION_API_URL não configurada no .env"
    exit 1
fi

log_info "✓ Variáveis de ambiente configuradas"
echo ""

# Verificar Python
log_info "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 não encontrado. Instale Python 3.11 ou superior."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
log_info "✓ Python $PYTHON_VERSION encontrado"
echo ""

# Verificar dependências Python
log_info "Verificando dependências Python..."
MISSING_DEPS=()

if ! python3 -c "import mcp" 2>/dev/null; then
    MISSING_DEPS+=("mcp")
fi

if ! python3 -c "import requests" 2>/dev/null; then
    MISSING_DEPS+=("requests")
fi

if ! python3 -c "import yaml" 2>/dev/null; then
    MISSING_DEPS+=("pyyaml")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    log_warn "Dependências faltando: ${MISSING_DEPS[*]}"
    log_info "Instalando dependências..."
    pip install "${MISSING_DEPS[@]}"
    echo ""
fi

log_info "✓ Todas as dependências instaladas"
echo ""

# Verificar buildspec.yml
log_info "Verificando buildspec.yml..."
if [ ! -f buildspec.yml ]; then
    log_error "buildspec.yml não encontrado!"
    exit 1
fi

log_info "✓ buildspec.yml encontrado"
echo ""

# Verificar PROJECT_PATH no buildspec
log_info "Extraindo PROJECT_PATH do buildspec.yml..."
PROJECT_PATH=$(python3 -c "import yaml; print(yaml.safe_load(open('buildspec.yml'))['env']['variables']['PROJECT_PATH'])" 2>/dev/null || echo "")

if [ -z "$PROJECT_PATH" ]; then
    log_error "PROJECT_PATH não encontrado no buildspec.yml"
    exit 1
fi

log_info "✓ PROJECT_PATH: $PROJECT_PATH"
echo ""

# Verificar se o diretório do projeto existe
log_info "Verificando diretório do projeto..."
if [ ! -d "$PROJECT_PATH" ]; then
    log_error "Diretório não encontrado: $PROJECT_PATH"
    exit 1
fi

FILE_COUNT=$(find "$PROJECT_PATH" -type f | wc -l)
log_info "✓ Diretório encontrado com $FILE_COUNT arquivos"
echo ""

# Executar o script de automação
log_info "Executando automação..."
echo "=========================================="
echo ""

python3 automate_from_buildspec.py "$@"

EXIT_CODE=$?

echo ""
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    log_info "✓ Teste concluído com sucesso!"
    echo ""
    log_info "Próximos passos:"
    log_info "1. Verifique os resultados em ./output/"
    log_info "2. Se tudo estiver correto, faça commit e push"
    log_info "3. Execute o build no CodeBuild"
else
    log_error "✗ Teste falhou com código de saída $EXIT_CODE"
    echo ""
    log_info "Verifique os logs acima para detalhes do erro"
fi

echo "=========================================="
exit $EXIT_CODE