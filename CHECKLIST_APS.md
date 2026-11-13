# Checklist Final — Requisitos da APS × Implementação no ECOVISION

Este documento cruza cada requisito obrigatório citado nos documentos
`APS_2026.docx` e `Orientações Detalhadas — APS - PIVC.docx` com o
arquivo/módulo do repositório que o implementa, para garantir que a
documentação e o código representem exatamente a mesma solução.

| # | Requisito da APS | Implementado em | Status |
|---|---|---|---|
| 1 | Base de dados aberta do MMA (CNUC) | `scripts/import_cnuc.py`, `app/models/unidade_conservacao.py` | ✅ |
| 2 | Plataforma em Python | Todo o backend (`app/`, `run.py`) | ✅ |
| 3 | Identificação e autenticação biométrica | `app/biometric/deteccao.py`, `app/biometric/reconhecimento.py`, `app/routes/auth.py` | ✅ |
| 4 | Três níveis de acesso (1, 2, 3) | `Usuario.nivel_acesso`, `app/services/permissoes.py` (`requer_nivel`) | ✅ |
| 5 | Nível 1 — informações gerais | Dashboard, unidades, mapa (`requer_nivel(1)` em `dashboard.py`, `unidades.py`, `mapa.py`) | ✅ |
| 6 | Nível 2 — informações da Direção | Análises e relatórios (`requer_nivel(2)` em `relatorios.py`) | ✅ |
| 7 | Nível 3 — Administrador | Gestão de usuários, permissões, logs (`requer_nivel(3)` em `admin.py`) | ✅ |
| 8 | Identificação → Autenticação → Autorização demonstradas claramente | Fluxo em `app/services/auth_service.py::autenticar_por_frame` + README seção 7 | ✅ |
| 9 | Tratamento de acesso não autorizado | `requer_nivel()` registra tentativa e redireciona para `/acesso-negado` | ✅ |
| 10 | Tratamento de erros de autenticação | `ResultadoAutenticacao.MENSAGENS` (rosto não detectado/reconhecido, câmera indisponível, etc.) | ✅ |
| 11 | Registro de acessos autorizados | Tabela `logs_acesso` via `registrar_acesso()` | ✅ |
| 12 | Registro de tentativas negadas | Tabela `logs_acesso` (`resultado="negado"`) | ✅ |
| 13 | Registro de erros de autenticação | Tabela `tentativas_autenticacao` via `registrar_tentativa()` | ✅ |
| 14 | Modelagem do banco (entidades, atributos, relacionamentos) | `database/schema.sql` + README seção 5 (DER textual) | ✅ |
| 15 | Camadas da aplicação (interface, regras de negócio, autenticação, banco) | Estrutura `app/routes` / `app/services` / `app/biometric` / `app/models` | ✅ |
| 16 | Dashboards, indicadores, gráficos | `app/templates/dashboard.html` + `app/static/js/dashboard.js` (Chart.js) | ✅ |
| 17 | Mapas interativos | `app/templates/mapa.html` + `app/static/js/mapa.js` (Leaflet) | ✅ |
| 18 | Filtros e consultas dinâmicas | `app/services/uc_service.py::aplicar_filtros`, `/api/unidades`, `/api/mapa/geojson` | ✅ |
| 19 | Não inventar dados ambientais | `scripts/import_cnuc.py` só grava o que existir no CSV oficial; campos ausentes ficam `NULL` | ✅ |
| 20 | Não usar APIs pagas / rodar localmente | LBPH (OpenCV) local, MySQL local, Leaflet+OSM (gratuito), Chart.js (biblioteca local via CDN) | ✅ |
| 21 | Segurança de senha/dados sensíveis | `werkzeug.security` (hash de senha), credenciais do banco via `.env` | ✅ |
| 22 | Bloqueio de acesso indevido | `MAX_LOGIN_ATTEMPTS` / `LOCKOUT_MINUTES` em `auth_service.py` | ✅ |
| 23 | Dados de teste apenas para usuários | `scripts/create_test_users.py`, campo `Usuario.is_dado_teste` | ✅ |
| 24 | Testes automatizados | `tests/` (25 testes: auth, permissões, banco, importação, erros) | ✅ |
| 25 | README completo | `README.md` (tecnologias, instalação, execução, testes, problemas comuns) | ✅ |
| 26 | Não simplificar/remover reconhecimento facial ou os 3 níveis | Ambos implementados de ponta a ponta (não são simulações) | ✅ |

## Limitações e decisões técnicas explicitadas (não ocultadas)

- **Dados geográficos do CNUC**: nem toda exportação do CNUC traz
  latitude/longitude por unidade. O mapa e o script de importação já
  estão preparados para exibi-los assim que existirem no CSV utilizado
  (`unidades_com_geolocalizacao()`), mas nenhuma coordenada é inventada
  quando ausente — a unidade simplesmente não aparece no mapa, e o
  sistema avisa quantas unidades ficaram de fora por esse motivo.
- **Armazenamento das fotos em banco de dados, cadastro e login por
  webcam**: por decisão do usuário, tanto o cadastro (`/cadastro-facial`)
  quanto o login (`/reconhecimento-facial`) usam a webcam ao vivo. A
  diferença em relação a uma primeira versão é que as fotos capturadas
  no cadastro NÃO são salvas como arquivo em disco: cada recorte de
  rosto vira uma linha BLOB na tabela `amostras_faciais`
  (`app/models/amostra_facial.py`). Na autenticação, o sistema busca
  todas as amostras do banco e treina o modelo LBPH em memória, na
  hora, comparando contra o frame ao vivo da webcam
  (`app/biometric/reconhecimento.py::identificar_usuario`).
- **Login de apoio por senha (`/login-emergencial`)**: existe apenas
  para o bootstrap do primeiro administrador (antes de qualquer
  cadastro biométrico existir) e como contingência de câmera. O fluxo
  principal e obrigatório da APS — identificação biométrica — está
  implementado em `/reconhecimento-facial` e é o caminho normal de uso
  após o primeiro cadastro.
- **Retreinamento do modelo LBPH global a cada novo cadastro**: escolha
  deliberada de simplicidade para uma base de usuários pequena, própria
  de um contexto acadêmico (ver comentário em
  `app/biometric/reconhecimento.py::rebuild_modelo_global`).
