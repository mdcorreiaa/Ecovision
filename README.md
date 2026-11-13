# ECOVISION
### Plataforma de Gestão e Monitoramento de Unidades de Conservação

Projeto acadêmico (APS) desenvolvido para a disciplina de Processamento de
Imagens e Visão Computacional, utilizando dados abertos do **Cadastro
Nacional de Unidades de Conservação (CNUC)**, disponibilizado pelo
Ministério do Meio Ambiente e Mudança do Clima no Portal Brasileiro de
Dados Abertos.

---

## 1. Descrição

O ECOVISION permite consultar, visualizar e gerir informações ambientais
sobre Unidades de Conservação brasileiras, com acesso controlado por
**reconhecimento facial** e três níveis de permissão (Usuário Geral,
Direção e Administrador).

Fluxo geral do sistema:

```
Usuário → Reconhecimento facial → Autenticação → Identificação do perfil
       → Verificação de permissão → Dashboard/consulta
       → Acesso liberado ou negado → Registro no sistema
```

## 2. Objetivo

- Identificar o usuário por reconhecimento facial e autenticá-lo;
- Consultar seu perfil e verificar suas permissões;
- Liberar ou negar acesso conforme o nível do usuário;
- Consultar e visualizar os dados ambientais do CNUC (dashboards, gráficos, mapas);
- Registrar acessos autorizados, tentativas negadas e erros de autenticação;
- Permitir a administração de usuários e permissões (perfil Administrador).

## 3. Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3 + Flask |
| Biometria / Imagens | OpenCV (Haar Cascade + LBPH) |
| Banco de dados | MySQL (SQLAlchemy + PyMySQL) |
| Frontend | HTML5, CSS3, JavaScript |
| Gráficos | Chart.js |
| Mapas | Leaflet + OpenStreetMap |
| Testes | Pytest |

Nenhuma dessas tecnologias foi substituída em relação ao que foi definido
na proposta da APS.

## 4. Estrutura de pastas

```
ECOVISION/
├── app/
│   ├── routes/         # Blueprints Flask (auth, dashboard, unidades, mapa, relatorios, admin)
│   ├── services/        # Regras de negócio (auth_service, uc_service, log_service, permissoes)
│   ├── models/           # Models SQLAlchemy (Usuario, UnidadeConservacao, Logs)
│   ├── biometric/        # Detecção (Haar Cascade), reconhecimento (LBPH) e captura de câmera
│   ├── templates/        # Views Jinja2 (login, dashboard, mapa, admin/, etc.)
│   └── static/
│       ├── css/
│       └── js/
├── database/
│   └── schema.sql         # DDL completo do MySQL + DER textual
├── data/                   # Onde o CSV oficial do CNUC deve ser colocado
├── scripts/
│   ├── import_cnuc.py       # Importação do CNUC para o MySQL
│   └── create_test_users.py # Cria usuários de teste (um por nível)
├── tests/                    # Testes automatizados (pytest)
├── config/
│   └── config.py               # Configuração central via variáveis de ambiente
├── requirements.txt
├── .env.example
├── README.md
└── run.py
```

> Nota: em relação à estrutura sugerida originalmente, foi adicionada uma
> pasta `database/` na raiz (além de `app/biometric/`) para armazenar o
> `schema.sql` de forma independente do código Python, facilitando a
> apresentação do modelo de dados separadamente do restante da aplicação.

## 5. Modelagem do banco de dados

### Entidades principais

**usuarios** — id, nome, login, senha_hash, nivel_acesso (1/2/3), status,
possui_cadastro_facial, is_dado_teste, data_cadastro.

**amostras_faciais** — id, usuario_id (FK), imagem (BLOB — o recorte do
rosto em escala de cinza, já detectado pelo OpenCV), data_criacao. Cada
foto usada no cadastro biométrico vira uma linha aqui; não existe
arquivo de foto ou de modelo salvo em disco.

**unidades_conservacao** — id, codigo_cnuc, nome, categoria_manejo,
esfera_administrativa, bioma, area_ha, ano_criacao, situacao_fundiaria,
plano_manejo, latitude, longitude, fonte_importacao, data_importacao.

**logs_acesso** — id, usuario_id (FK), data_hora, tipo_acao,
recurso_acessado, resultado, endereco_ip, detalhes.

**tentativas_autenticacao** — id, usuario_id (FK, nulo se não identificado),
data_hora, resultado, motivo_falha, endereco_ip, metodo.

### DER (textual)

```
usuarios (1) ----< (N) logs_acesso              [ON DELETE SET NULL]
usuarios (1) ----< (N) tentativas_autenticacao   [ON DELETE SET NULL]
unidades_conservacao  (tabela independente, consultada mas sem FK com usuarios)
```

O SQL completo (`CREATE DATABASE`, `CREATE TABLE`, índices, constraints)
está em [`database/schema.sql`](database/schema.sql). O mesmo schema
também é criado automaticamente pelo SQLAlchemy (`db.create_all()`) ao
rodar `scripts/create_test_users.py`.

## 6. Importação dos dados do CNUC

1. Baixe o CSV oficial em: https://dados.mma.gov.br/dataset/unidadesdeconservacao
2. Salve o arquivo em `data/cnuc_unidades_conservacao.csv`
3. Execute:
   ```bash
   python scripts/import_cnuc.py
   ```

O script (`scripts/import_cnuc.py`):
- mapeia automaticamente variações comuns de nome de coluna do CNUC;
- trata campos vazios (nunca inventa dados ambientais);
- converte tipos (área → float, ano → int, plano de manejo → booleano);
- evita duplicar registros já importados (por `codigo_cnuc` ou nome);
- imprime um relatório final com quantidade de linhas lidas, importadas,
  atualizadas e ignoradas (com o motivo).

Se o arquivo não for encontrado, o script informa exatamente onde ele
deve ser colocado, sem travar a aplicação.

## 7. Reconhecimento facial

- **Detecção**: `app/biometric/deteccao.py` usa Haar Cascade
  (`cv2.CascadeClassifier`) para localizar o rosto no frame da câmera.
- **Cadastro biométrico**: a tela "Cadastro Biométrico" (`/cadastro-facial`)
  captura N fotos (padrão: 15) do usuário logado pela webcam. Cada recorte
  de rosto (já em escala de cinza) é salvo como **BLOB direto no banco de
  dados**, na tabela `amostras_faciais` — não existe arquivo em disco.
- **Identificação (autenticação/login)**: a tela "Reconhecimento Facial"
  (`/reconhecimento-facial`) captura um frame ao vivo pela webcam. A cada
  tentativa, o sistema busca TODAS as amostras faciais do banco, treina um
  modelo LBPH em memória na hora (`app/biometric/reconhecimento.py`) e
  compara contra o frame capturado. O algoritmo LBPH retorna um rótulo (o
  `usuario_id`) e uma distância de confiança - quanto **menor**, mais
  parecido. O limiar aceito é configurável via `FACE_RECOGNITION_THRESHOLD`
  no `.env`. Não há cache de modelo em disco: o retreino acontece a cada
  tentativa de login, sempre a partir dos dados atuais do banco.
- **Erros tratados**: câmera indisponível, rosto não detectado, rosto não
  reconhecido, modelo ainda não treinado (nenhum usuário cadastrado).
- **Resultado**: toda tentativa (sucesso ou falha) é gravada em
  `tentativas_autenticacao`; todo acesso pós-login relevante é gravado em
  `logs_acesso`.

Biblioteca adicional necessária: `opencv-contrib-python` (inclui o
módulo `cv2.face`, usado pelo LBPH; o pacote `opencv-python` "puro" **não**
inclui esse módulo).

## 8. Segurança

- Senhas (usadas apenas como mecanismo administrativo de apoio, não como
  fluxo principal de login) nunca são armazenadas em texto puro —
  `werkzeug.security.generate_password_hash`;
- O banco armazena apenas o **caminho** do modelo biométrico treinado,
  nunca a imagem do rosto em texto/binário dentro do próprio registro do
  usuário;
- Credenciais do banco ficam em variáveis de ambiente (`.env`, nunca
  versionado — veja `.env.example`);
- Toda rota sensível é protegida no servidor pelo decorator
  `@requer_nivel(N)` (`app/services/permissoes.py`) — um usuário de nível
  inferior **não consegue** acessar uma rota de nível superior mesmo
  digitando a URL diretamente;
- Bloqueio automático após N tentativas de autenticação falhas
  (configurável via `MAX_LOGIN_ATTEMPTS` / `LOCKOUT_MINUTES`);
- Tratamento de erros centralizado (`app/__init__.py`) para 404, 403, 500
  e falha de conexão com o banco, sem expor detalhes internos ao usuário.

## 9. Níveis de acesso

| Nível | Perfil | Pode |
|---|---|---|
| 1 | Usuário Geral | Dashboard, unidades, mapa, filtros, indicadores básicos |
| 2 | Direção | Tudo do nível 1 + análises, comparativos, relatórios |
| 3 | Administrador | Tudo dos níveis anteriores + gestão de usuários, permissões, logs |

## 10. Instalação e execução

### 10.1 Pré-requisitos
- Python 3.10+
- MySQL Server 8+ em execução localmente
- Uma webcam (usada tanto no cadastro biométrico quanto no login por
  reconhecimento facial)

### 10.2 Passo a passo

```bash
# 1. Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Criar o banco no MySQL
mysql -u root -p < database/schema.sql
# (ou crie manualmente um usuário/banco e deixe o SQLAlchemy criar as
#  tabelas ao rodar create_test_users.py)

# 4. Configurar variáveis de ambiente
cp .env.example .env
# edite o .env com usuário/senha do seu MySQL

# 5. Criar usuários de teste (um por nível de acesso)
python scripts/create_test_users.py

# 6. Importar os dados do CNUC (opcional para rodar o app, mas
#    necessário para o dashboard/mapa mostrarem dados reais)
#    Baixe o CSV em https://dados.mma.gov.br/dataset/unidadesdeconservacao
#    e salve em data/cnuc_unidades_conservacao.csv
python scripts/import_cnuc.py

# 7. Executar a aplicação
python run.py
```

### 10.3 Acessando

Abra `http://localhost:5000` no navegador. O navegador solicitará
permissão de câmera (necessária apenas se você acessar via streaming
JS no futuro; a captura atual é feita no lado do servidor via OpenCV, a
partir da câmera conectada à máquina onde o Flask está rodando).

Na tela inicial, clique em **"Entrar com reconhecimento facial"**.

**Importante:** um usuário só consegue entrar pelo fluxo facial depois de
ter seu rosto cadastrado. Para o primeiro cadastro (galinha e ovo: é
preciso estar logado para acessar "Cadastro Biométrico"), veja a seção
de testes abaixo.

## 11. Testando cada perfil (dados de teste)

`scripts/create_test_users.py` cria três usuários **de teste**
(`is_dado_teste=True` no banco, para deixar claro que não são dados
reais):

| Login | Senha (apoio administrativo) | Nível |
|---|---|---|
| `usuario_geral` | `teste123` | 1 - Usuário Geral |
| `usuario_direcao` | `teste123` | 2 - Direção |
| `usuario_admin` | `teste123` | 3 - Administrador |

Como o login principal é facial, para a primeira demonstração:

1. Rode `python scripts/create_test_users.py` (cria os 3 usuários de teste com senha `teste123`);
2. Acesse `http://localhost:5000/login-emergencial` e entre com `usuario_admin` / `teste123`
   — este é um **login de apoio por senha**, existente exatamente para o bootstrap do primeiro
   acesso (quando ainda não há nenhum cadastro biométrico no sistema) e para contingência caso
   uma câmera fique indisponível. Toda autenticação por essa via também é auditada em
   `tentativas_autenticacao` (`metodo="senha"`);
3. Já autenticado como administrador, acesse **"Cadastro Biométrico"** e capture o rosto desse
   usuário pela webcam (as fotos vão direto para a tabela `amostras_faciais` no banco); repita o
   processo para os demais usuários de teste (o administrador pode orientar cada um a fazer login
   de apoio uma única vez só para cadastrar o próprio rosto);
4. A partir daí, todos passam a entrar normalmente pelo fluxo facial em `/reconhecimento-facial`.

### Exemplos de acesso permitido / negado

- Usuário Nível 1 acessando `/dashboard` → **permitido** (200);
- Usuário Nível 1 acessando `/relatorios` ou `/admin/usuarios` diretamente
  pela URL → **negado**, redirecionado para a tela de acesso negado, e a
  tentativa é registrada em `logs_acesso` com `resultado=negado`;
- Usuário Nível 3 acessando qualquer rota → **permitido**.

## 12. Testes automatizados

```bash
pytest tests/ -v
```

Cobrem: conexão/persistência no banco, autenticação (com a captura de
câmera mockada, já que hardware físico não é testável em CI), controle
de permissões por nível (incluindo tentativa de acesso via URL direta),
importação do CNUC (conversão de tipos, deduplicação, arquivo ausente) e
tratamento de rotas inexistentes.

Os testes usam SQLite em memória para rodar sem exigir um MySQL
configurado no ambiente de CI; a aplicação em produção usa MySQL
normalmente.

## 13. Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `cv2.face` não encontrado | Instalado `opencv-python` em vez de `opencv-contrib-python` | `pip uninstall opencv-python && pip install opencv-contrib-python` |
| Câmera indisponível | Webcam ocupada por outro app, ou índice errado | Ajuste `CAMERA_INDEX` no `.env` |
| Erro de conexão com MySQL | Serviço não iniciado ou credenciais erradas | Verifique `DB_*` no `.env` e se o MySQL está rodando |
| Mapa aparece vazio | CSV do CNUC importado não possui colunas de latitude/longitude | Normal — o CNUC nem sempre disponibiliza geolocalização por unidade; a estrutura já está pronta para exibir assim que dados geográficos existirem |
| Rosto não reconhecido com frequência | Iluminação ruim ou poucas amostras no cadastro | Refaça o cadastro biométrico com mais luz e mais amostras (`qtd_amostras`) |
