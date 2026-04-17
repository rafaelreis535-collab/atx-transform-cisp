# Configuração do CodeBuild para Geração de Documentação

Este guia explica como configurar o AWS CodeBuild para executar a geração automática de documentação usando a API de Modernização do AI Cockpit.

## Visão Geral da Solução

A solução corrige o erro **"MCP tools were not available as external tools"** implementando:

1. ✅ Script [`automate_from_buildspec.py`](automate_from_buildspec.py:1) que lê configurações do [`buildspec.yml`](buildspec.yml:1)
2. ✅ Instalação automática de dependências Python (mcp, requests, pyyaml)
3. ✅ Integração com AWS Secrets Manager para credenciais seguras
4. ✅ Geração automática de documentação após transformação ATX

## Pré-requisitos

### 1. AWS Secrets Manager

Você precisa criar um secret no AWS Secrets Manager com as credenciais da API:

```bash
# Criar o secret com as credenciais
aws secretsmanager create-secret \
  --name aic-modernization \
  --description "Credenciais para AI Cockpit Modernization API" \
  --secret-string '{
    "api-key": "sua-chave-api-aqui",
    "org-id": "686"
  }'
```

### 2. IAM Role do CodeBuild

O IAM Role usado pelo CodeBuild precisa ter permissão para acessar o secret:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:aic-modernization-*"
      ]
    }
  ]
}
```

**Substitua:**
- `REGION` pela região AWS (ex: `us-east-1`)
- `ACCOUNT_ID` pelo ID da sua conta AWS

## Estrutura do Buildspec

O [`buildspec.yml`](buildspec.yml:1) atualizado inclui:

### Variáveis de Ambiente

```yaml
env:
  variables:
    PROJECT_PATH: "./banking-example"
    MODERNIZATION_API_URL: "https://aic-modernization-api.compass.uol/"
    MODERNIZATION_OUTPUT_LANGUAGE: "en_US"
  secrets-manager:
    MODERNIZATION_API_KEY: "aic-modernization:api-key"
    MODERNIZATION_ORG_ID: "aic-modernization:org-id"
```

### Fases de Build

1. **install**: Instala Node.js, Python e dependências
2. **pre_build**: Valida estrutura do projeto
3. **build**: Executa transformação ATX
4. **post_build**: Gera documentação e prepara artefatos

## Fluxo de Execução

```
┌─────────────────────────────────────┐
│ 1. Install Phase                    │
│    - Install Python 3.11            │
│    - Install pip packages           │
│    - Setup ATX runtime              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 2. Pre-Build Phase                  │
│    - Validate project structure     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 3. Build Phase                      │
│    - Run ATX transformation         │
│    - Convert COBOL to Java          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 4. Post-Build Phase                 │
│    - Read buildspec.yml             │
│    - Extract PROJECT_PATH           │
│    - Create project ZIP             │
│    - Upload to API                  │
│    - Generate documentation         │
│    - Download results               │
└─────────────────────────────────────┘
```

## Configuração do Projeto CodeBuild

### Via Console AWS

1. Acesse **AWS CodeBuild** → **Build projects** → **Create project**

2. **Project configuration:**
   - Project name: `atx-transform-cisp-docs`
   - Description: `ATX transformation with documentation generation`

3. **Source:**
   - Source provider: Seu repositório (GitHub, CodeCommit, etc.)
   - Repository: Selecione seu repositório

4. **Environment:**
   - Environment image: `Managed image`
   - Operating system: `Amazon Linux 2`
   - Runtime: `Standard`
   - Image: `aws/codebuild/amazonlinux2-x86_64-standard:5.0`
   - Service role: Selecione ou crie uma role com as permissões necessárias

5. **Buildspec:**
   - Build specifications: `Use a buildspec file`
   - Buildspec name: `buildspec.yml`

6. **Artifacts:**
   - Type: `Amazon S3` (opcional)
   - Bucket name: Seu bucket S3
   - Path: `atx-transform-output/`

### Via AWS CLI

```bash
aws codebuild create-project \
  --name atx-transform-cisp-docs \
  --source type=GITHUB,location=https://github.com/seu-usuario/seu-repo.git \
  --artifacts type=S3,location=seu-bucket-s3 \
  --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux2-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL \
  --service-role arn:aws:iam::ACCOUNT_ID:role/CodeBuildServiceRole
```

## Testando Localmente

Para testar o script localmente antes de executar no CodeBuild:

### 1. Configurar Variáveis de Ambiente

```bash
export MODERNIZATION_API_URL="https://aic-modernization-api.compass.uol/"
export MODERNIZATION_API_KEY="sua-chave-api-aqui"
export MODERNIZATION_ORG_ID="686"
export MODERNIZATION_OUTPUT_LANGUAGE="en_US"
```

### 2. Instalar Dependências

```bash
pip install mcp requests pyyaml
```

### 3. Executar o Script

```bash
python automate_from_buildspec.py
```

## Verificando os Resultados

### Durante a Execução

No console do CodeBuild, você verá logs como:

```
[2024-01-15 10:30:00] [INFO] Starting buildspec-based automation workflow
[2024-01-15 10:30:01] [INFO] Reading buildspec from: ./buildspec.yml
[2024-01-15 10:30:01] [INFO] Found PROJECT_PATH: ./banking-example
[2024-01-15 10:30:01] [INFO] Derived project name: banking-example
[2024-01-15 10:30:02] [INFO] Creating ZIP file from: ./banking-example
[2024-01-15 10:30:03] [INFO] ZIP file created: banking-example.zip (12,345 bytes)
[2024-01-15 10:30:04] [INFO] Uploading ZIP file: banking-example.zip
[2024-01-15 10:30:07] [INFO] Upload status: indexed
[2024-01-15 10:30:17] [INFO] Project indexed successfully!
[2024-01-15 10:30:18] [INFO] Task created: task123
[2024-01-15 10:45:30] [INFO] Task completed successfully!
[2024-01-15 10:45:35] [INFO] Download completed: ./output/task_task123_results.zip
```

### Artefatos Gerados

Os artefatos incluirão:

```
output/
├── banking-example/          # Código transformado
│   ├── BKACCOUN.cpy
│   ├── BKCONTRL.cpy
│   └── ...
└── task_xxx_results.zip      # Documentação gerada
```

## Solução de Problemas

### Erro: "MODERNIZATION_API_KEY environment variable not set"

**Causa:** O secret não está configurado corretamente no Secrets Manager ou a IAM role não tem permissão.

**Solução:**
1. Verifique se o secret existe: `aws secretsmanager describe-secret --secret-id aic-modernization`
2. Verifique as permissões da IAM role do CodeBuild
3. Confirme que o nome do secret no [`buildspec.yml`](buildspec.yml:1) está correto

### Erro: "PROJECT_PATH not found in buildspec.yml"

**Causa:** A variável `PROJECT_PATH` não está definida em `env.variables`.

**Solução:**
Adicione ao [`buildspec.yml`](buildspec.yml:1):
```yaml
env:
  variables:
    PROJECT_PATH: "./seu-projeto"
```

### Erro: "Source directory not found"

**Causa:** O diretório especificado em `PROJECT_PATH` não existe.

**Solução:**
1. Verifique se o diretório existe no repositório
2. Confirme que o caminho está correto (relativo à raiz do repositório)

### Erro: "Upload failed" ou "Indexing failed"

**Causa:** Problemas de conectividade ou credenciais inválidas.

**Solução:**
1. Verifique se a API_KEY está correta
2. Confirme que a URL da API está acessível
3. Verifique os logs detalhados no CodeBuild

### Erro: "Task failed or timed out"

**Causa:** A geração de documentação falhou ou demorou muito.

**Solução:**
1. Verifique os logs da API para detalhes do erro
2. Aumente o timeout no script se necessário
3. Verifique se o projeto foi indexado corretamente

## Customizações Opcionais

### Usar LLM Provider/Model Específico

Adicione ao [`buildspec.yml`](buildspec.yml:1):

```yaml
env:
  variables:
    MODERNIZATION_LLM_PROVIDER: "anthropic"
    MODERNIZATION_LLM_MODEL: "us.anthropic.claude-haiku-4-5-20251001-v1:0"
```

### Mudar Idioma da Documentação

```yaml
env:
  variables:
    MODERNIZATION_OUTPUT_LANGUAGE: "pt_BR"  # ou es_ES
```

### Pular Upload (Projeto Já Indexado)

```bash
python automate_from_buildspec.py --skip-upload
```

### Usar ZIP Existente

```bash
python automate_from_buildspec.py --skip-zip
```

## Monitoramento e Logs

### CloudWatch Logs

Os logs do CodeBuild são automaticamente enviados para CloudWatch Logs:

```
Log Group: /aws/codebuild/atx-transform-cisp-docs
```

### Métricas

Monitore:
- Duração do build
- Taxa de sucesso/falha
- Uso de recursos

## Segurança

### Boas Práticas

1. ✅ **Nunca** commite credenciais no código
2. ✅ Use AWS Secrets Manager para credenciais sensíveis
3. ✅ Aplique princípio do menor privilégio nas IAM roles
4. ✅ Habilite logs de auditoria no CloudTrail
5. ✅ Rotacione credenciais regularmente

### Rotação de Credenciais

```bash
# Atualizar o secret
aws secretsmanager update-secret \
  --secret-id aic-modernization \
  --secret-string '{
    "api-key": "nova-chave-api",
    "org-id": "686"
  }'
```

## Suporte

Para problemas ou dúvidas:
- Consulte os logs do CodeBuild
- Verifique a documentação da API: [`README_AUTOMATION.md`](README_AUTOMATION.md:1)
- Entre em contato com a equipe do AI Cockpit Modernization

## Arquivos Relacionados

- [`buildspec.yml`](buildspec.yml:1) - Configuração do CodeBuild
- [`automate_from_buildspec.py`](automate_from_buildspec.py:1) - Script de automação
- [`mcp_client.py`](mcp_client.py:1) - Cliente MCP para API
- [`automate_docs.py`](automate_docs.py:1) - Funções auxiliares
- [`README_BUILDSPEC_AUTOMATION.md`](README_BUILDSPEC_AUTOMATION.md:1) - Documentação detalhada