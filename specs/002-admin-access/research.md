# Research: Administração e Acesso

## R1. Usuário padrão ou personalizado

- **Decision**: usar `django.contrib.auth.models.User`.
- **Rationale**: o perfil é único e não há campos extras. Trocar o modelo depois da primeira migration
  é caro, mas nenhum requisito atual o exige (YAGNI).
- **Alternatives**: `AbstractUser` personalizado (útil só se surgirem campos como nome de exibição ou
  e-mail obrigatório); `AbstractBaseUser` (reimplementa o que já existe).

## R2. Como representar o perfil único

- **Decision**: grupo "Administrador" com todas as permissões de todos os modelos (incluindo contas e
  grupos). Uma conta é administradora se for ativa, `is_staff` e membro do grupo. Quem não tem o grupo
  não obtém nenhuma permissão: o Admin não lista nenhum cadastro e responde 403 em URL direta.
- **Rationale**: usa só mecanismos nativos (princípio I). O Admin já exige `is_staff` para entrar e
  verifica permissões de modelo no servidor em cada view (FR-006, FR-009).
- **Alternatives**: usar só `is_superuser` (ignora o conceito de perfil e não é revogável por
  cadastro); permissões atribuídas conta a conta (mais trabalho e erro humano).

## R3. Manter as permissões do grupo atualizadas

- **Decision**: sinal `post_migrate` que cria o grupo e define todas as permissões existentes, de forma
  idempotente. Cadastros novos de features seguintes entram no grupo automaticamente na próxima
  migração.
- **Rationale**: o grupo nunca fica desatualizado e não depende de um passo manual esquecido. As
  permissões são criadas pelo próprio `post_migrate` do auth, então o sinal deve rodar depois dele
  (conectado em `ready()` do app `core`, que vem depois de `auth` em `INSTALLED_APPS`).
- **Alternatives**: migration de dados (precisaria ser repetida a cada feature); comando manual
  (esquecível).

## R4. Criação de contas

- **Decision**: comando `create_admin <usuário>` que pede a senha sem eco (duas vezes), valida com os
  validadores de senha, cria a conta ativa, `is_staff` e no grupo. Contas seguintes também podem ser
  criadas pelo próprio painel (tela de usuários), e a desativação é feita desmarcando "ativo".
- **Rationale**: resolve a "primeira conta" (FR-013), sem senha na linha de comando nem em log.
  `createsuperuser` continua válido, mas não atribui o perfil.
- **Alternatives**: só `createsuperuser` (cria superusuário, que ignora o perfil).

## R5. Autenticação, sessão e senhas

- **Decision**: manter `ModelBackend`, sessões em banco, hash PBKDF2 padrão e `AUTH_PASSWORD_VALIDATORS`
  do Django. A mensagem de login do Admin já é genérica (FR-003). Conta desativada perde o acesso na
  requisição seguinte, pois o backend rejeita usuários inativos ao carregar a sessão (FR-005).
- **Rationale**: nada customizado, menos superfície de erro. Sem bloqueio de login (decisão da
  clarificação) e sem recuperação por e-mail (FR-017).
- **Alternatives**: django-axes ou throttling (descartado na clarificação); SSO (fora do escopo).

## R6. Registros inativos nas listas de relacionamento

- **Decision**: `ActiveOnlyForeignKeyMixin` em `apps/core/admin.py`, que filtra por `is_active=True`
  na lista de escolha de chaves estrangeiras cujo modelo relacionado tem o campo `is_active`. Os
  cadastros das próximas features adotam o mixin.
- **Rationale**: atende o FR-012 sem modelos ainda existentes e fica testável com mocks.
- **Alternatives**: repetir o filtro em cada `ModelAdmin` (duplicação).

## R7. Painel em português e arquivos estáticos

- **Decision**: `LANGUAGE_CODE` já é `pt-br`, e o painel recebe título e cabeçalho em português. Os
  rótulos dos modelos virão dos `verbose_name` em cada feature. Os estáticos do Admin são servidos pelo
  `runserver` com `DJANGO_DEBUG=true`, o que basta para uso local.
- **Rationale**: execução só local; servir estáticos em produção está fora do escopo.
- **Alternatives**: WhiteNoise (útil só em hospedagem).

## R8. Testes sem banco

- **Decision**: testar com `RequestFactory`, `SimpleNamespace` e `unittest.mock` para usuário, grupo,
  permissões e consultas. Cobrir: `AdminSite.has_permission` com usuário anônimo, inativo, sem
  `is_staff` e administrador; `sync_admin_group`; comando `create_admin`; mixin de inativos; e as
  rotas e configurações (middlewares, apps, validadores).
- **Rationale**: Princípio III proíbe qualquer acesso a banco. O comportamento de login do Django em si
  não é retestado, só a nossa configuração e nosso código.
- **Alternatives**: testes de integração com banco (proibidos).

## R9. API pública e CORS

- **Decision**: não alterar a API nem o CORS. O painel usa cookies de sessão na própria origem do
  backend; o frontend público não os utiliza, e `CORS_ALLOW_CREDENTIALS` permanece desativado.
- **Rationale**: o frontend não tem login de administrador (suposição da spec) e a leitura pública
  segue sem autenticação (FR-016).
