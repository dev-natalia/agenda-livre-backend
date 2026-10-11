# Feature Specification: Administração e Acesso

**Feature Branch**: `002-admin-access`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "feature 2 em docs/04-backlog-do-produto.md" (EP-02 — Administração e acesso: US-004 Autenticar administradores, US-005 Aplicar permissões administrativas, US-006 Gerenciar conteúdo pela interface administrativa)

## Clarifications

### Session 2026-10-11

- Q: Quantos perfis de administrador o sistema deve ter na primeira versão? → A: Um único perfil; todo administrador pode fazer tudo, inclusive gerenciar contas.
- Q: O que deve acontecer quando alguém erra a senha várias vezes seguidas? → A: Sem bloqueio nesta versão, pois o sistema roda apenas localmente.

## User Scenarios & Testing *(mandatory)*

Os usuários desta feature são as pessoas que administram o conteúdo do Agenda Livre (equipe do CEU Navegantes e da equipe do projeto) e, entre elas, quem concede e retira acessos (na primeira versão há um único perfil de administrador, com acesso total). A feature entrega a porta de entrada protegida e as regras de permissão sobre as quais os cadastros (unidades, categorias, atividades e programações) serão construídos nas features seguintes.

### User Story 1 - Entrar na área administrativa (Priority: P1)

Uma pessoa administradora abre a área administrativa, informa suas credenciais e passa a ter acesso ao painel. Quem não está autenticado, ou informa credenciais inválidas, não consegue entrar.

**Why this priority**: sem autenticação, não há como proteger nenhuma operação de escrita. Todas as demais features dependem desta barreira.

**Independent Test**: acessar a área administrativa sem login e verificar o redirecionamento para a tela de entrada; entrar com credenciais válidas e inválidas e comparar os resultados.

**Acceptance Scenarios**:

1. **Dado** uma pessoa não autenticada, **Quando** ela tenta abrir qualquer página da área administrativa, **Então** é levada à tela de entrada e nenhum conteúdo administrativo é exibido.
2. **Dado** credenciais válidas de uma conta ativa com acesso administrativo, **Quando** a pessoa envia o formulário de entrada, **Então** ela acessa o painel administrativo.
3. **Dado** uma senha incorreta ou um usuário inexistente, **Quando** o formulário é enviado, **Então** o acesso é negado com uma mensagem genérica que não revela qual dos dois dados está errado.
4. **Dado** uma conta desativada, **Quando** a pessoa tenta entrar com credenciais corretas, **Então** o acesso é negado.
5. **Dado** uma conta existente sem acesso administrativo, **Quando** a pessoa tenta entrar na área administrativa, **Então** o acesso é negado.
6. **Dado** uma pessoa autenticada, **Quando** ela encerra a sessão, **Então** deixa de ter acesso até entrar novamente.

---

### User Story 2 - Limitar operações por permissão (Priority: P1)

Somente contas com o perfil de administrador executam operações administrativas. Uma conta sem esse perfil não consegue executar nenhuma operação restrita, e essa verificação vale mesmo que ela tente a operação por um caminho direto.

**Why this priority**: autenticar não basta; a constituição exige que toda escrita seja restrita a usuários administradores autorizados. Sem as permissões, qualquer conta com acesso poderia alterar tudo.

**Independent Test**: criar uma conta administradora e uma conta comum sem o perfil e verificar que só a primeira realiza operações, inclusive ao acessar diretamente o endereço de uma operação restrita.

**Acceptance Scenarios**:

1. **Dado** uma conta sem o perfil de administrador, **Quando** a pessoa tenta executá-la, **Então** a operação é recusada e nada é alterado.
2. **Dado** uma conta sem o perfil de administrador, **Quando** ela navega pelo painel, **Então** nenhum cadastro é oferecido a ela.
3. **Dado** uma conta sem permissão, **Quando** ela acessa diretamente o endereço de uma operação restrita, **Então** o acesso é negado do mesmo modo que pelo painel.
4. **Dado** uma conta com o perfil de administrador, **Quando** ela executa as operações de manutenção, **Então** elas são realizadas normalmente.
5. **Dado** que o perfil de administrador foi retirado de uma conta, **Quando** ela tenta a operação na sessão seguinte, **Então** a operação é recusada.
6. **Dado** a documentação do sistema, **Quando** a equipe a consulta, **Então** encontra o perfil de administrador e o que ele pode fazer.

---

### User Story 3 - Gerenciar o conteúdo pela interface administrativa (Priority: P2)

Uma pessoa administradora autorizada usa o painel para manter o conteúdo sem mexer diretamente no banco de dados: encontra os cadastros disponíveis, preenche formulários com rótulos compreensíveis e recebe validação dos campos obrigatórios.

**Why this priority**: o painel é a interface de gerenciamento definida pela constituição. Nesta feature ela é preparada e protegida; os cadastros de negócio em si chegam nas features seguintes. Por isso a prioridade é menor que a das barreiras de acesso.

**Independent Test**: com uma conta autorizada, abrir o painel, localizar os cadastros disponíveis, abrir um formulário, enviá-lo sem os campos obrigatórios e verificar a mensagem de validação.

**Acceptance Scenarios**:

1. **Dado** uma conta autorizada, **Quando** ela abre o painel, **Então** vê todos os cadastros disponíveis, com nomes em português.
2. **Dado** um formulário com campo obrigatório vazio, **Quando** a pessoa tenta salvar, **Então** o registro não é salvo e a mensagem indica o campo a corrigir.
3. **Dado** um cadastro com relacionamento com outro, **Quando** a pessoa o edita, **Então** consegue escolher o registro relacionado em uma lista legível.
4. **Dado** um registro inativo, **Quando** a pessoa cria um novo vínculo, **Então** o registro inativo não é oferecido como opção (regra aplicada quando houver cadastros com relacionamentos).
5. **Dado** uma conta sem o perfil de administrador, **Quando** ela tenta acessar um cadastro, **Então** o acesso é negado.

---

### User Story 4 - Conceder e retirar acessos (Priority: P2)

Uma pessoa administradora cria outra conta de administrador e pode desativá-la quando a pessoa não precisar mais de acesso.

**Why this priority**: sem uma forma de criar e retirar contas, não há administradores reais. O número de contas é pequeno e a primeira conta é criada por procedimento documentado.

**Independent Test**: criar uma conta pelo procedimento documentado, entrar com ela, desativá-la e confirmar que a entrada passa a ser recusada.

**Acceptance Scenarios**:

1. **Dado** o procedimento documentado, **Quando** a pessoa cria a primeira conta de administrador, **Então** ela consegue entrar na área administrativa.
2. **Dado** uma conta existente, **Quando** um administrador a desativa, **Então** a pessoa perde o acesso sem que seus registros anteriores sejam apagados.
3. **Dado** uma conta comum, **Quando** um administrador lhe atribui o perfil de administrador, **Então** ela passa a ter acesso total à área administrativa.

---

### Edge Cases

- Várias tentativas seguidas de entrada com senha errada: não há bloqueio nesta versão; cada tentativa é avaliada de forma independente e continua recusada.
- Sessão expirada enquanto a pessoa preenche um formulário: a gravação deve ser recusada e a pessoa orientada a entrar de novo.
- Conta com permissões alteradas enquanto a pessoa está com a sessão aberta.
- Pessoa desativada com sessão ativa: o acesso deve cessar.
- Senha fraca ao criar ou alterar uma conta.
- Acesso à área administrativa por um endereço que não existe ou já foi removido.
- Esquecimento da senha: o procedimento de recuperação ainda precisa ser definido (ver Assumptions).
- Desativação da última conta de administrador, deixando o sistema sem quem o administre.
- O frontend público tenta usar a sessão administrativa a partir de outra origem.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST negar o acesso a toda a área administrativa a quem não estiver autenticado.
- **FR-002**: O sistema MUST autenticar administradores pelo mecanismo nativo de usuários do Django, sem criar um sistema de autenticação paralelo.
- **FR-003**: O sistema MUST recusar credenciais inválidas e contas desativadas, com mensagem genérica que não indique se o usuário ou a senha está errado.
- **FR-004**: O sistema MUST armazenar senhas apenas de forma protegida (nunca em texto simples), e MUST NOT exibi-las ou registrá-las em logs.
- **FR-005**: O sistema MUST permitir encerrar a sessão e MUST encerrar o acesso de contas que forem desativadas.
- **FR-006**: O sistema MUST verificar as permissões no servidor em toda operação administrativa, independentemente de a opção aparecer ou não na interface.
- **FR-007**: O sistema MUST ter um único perfil de administrador, com permissão para visualizar, criar, alterar e remover todos os tipos de registro e para gerenciar contas.
- **FR-008**: O sistema MUST permitir atribuir e retirar o perfil de administrador de uma conta, e uma conta sem o perfil MUST NOT executar nenhuma operação administrativa.
- **FR-009**: O acesso ao Django Admin MUST exigir tanto autenticação quanto autorização; ter uma conta existente não basta.
- **FR-010**: Toda criação, alteração e exclusão de unidades, categorias, atividades e programações MUST ser feita pelo Django Admin, sem telas administrativas customizadas (Constituição, Princípio I).
- **FR-011**: A interface administrativa MUST usar rótulos em português compreensíveis e validar campos obrigatórios antes de salvar.
- **FR-012**: A interface administrativa MUST apresentar os relacionamentos entre registros de forma selecionável, e MUST NOT oferecer registros inativos para novos vínculos quando essa regra se aplicar.
- **FR-013**: O sistema MUST oferecer um procedimento documentado para criar a primeira conta de administrador e para criar e desativar as demais.
- **FR-014**: O sistema MUST documentar o perfil de administrador e suas permissões, e essa documentação MUST estar pronta antes da demonstração final.
- **FR-015**: O sistema MUST NOT bloquear contas ou origens por tentativas repetidas de entrada nesta versão; toda tentativa com credenciais incorretas é recusada normalmente.
- **FR-016**: A área pública de consulta MUST continuar acessível sem login; esta feature MUST NOT exigir autenticação para leitura pública.
- **FR-017**: Esta feature MUST NOT incluir recuperação de senha por e-mail, cadastro público de contas ou autenticação por terceiros, pois o sistema roda apenas localmente e a equipe é pequena.

### Key Entities *(include if feature involves data)*

- **Conta administrativa**: identifica uma pessoa que administra o conteúdo; possui credenciais protegidas, um estado ativo ou inativo e, opcionalmente, o perfil de administrador. Será referenciada nos registros de auditoria (usuário criador e atualizador) das features seguintes.
- **Perfil de administrador**: único perfil da primeira versão; concede todas as permissões sobre todos os cadastros e sobre as contas. Se surgir necessidade de papéis distintos, novos perfis serão tratados em uma feature futura.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das páginas e operações da área administrativa recusam quem não está autenticado.
- **SC-002**: 100% das tentativas de operação sem a permissão correspondente são recusadas, tanto pelo painel quanto por acesso direto.
- **SC-003**: Uma pessoa autorizada entra no painel em menos de 1 minuto a partir da tela de entrada.
- **SC-004**: Nenhuma senha aparece em texto simples no banco, em logs, em mensagens de erro ou no repositório.
- **SC-005**: Uma pessoa administradora cria uma nova conta de administrador e a vê entrar com sucesso em até 5 minutos, seguindo apenas a documentação.
- **SC-006**: A consulta pública continua funcionando sem login em 100% dos casos após a ativação do controle de acesso.
- **SC-007**: Após uma conta ser desativada, 100% das novas tentativas de acesso com ela são recusadas.

## Assumptions

- "Feature 2" refere-se ao épico EP-02 do backlog (US-004, US-005 e US-006), conforme a Feature 001, que deixa "Autenticação e Django Admin" para esta feature. Os cadastros de unidades e categorias (US-007 e US-008, EP-03) ficam para a feature seguinte; aqui o painel é preparado, protegido e coberto por testes.
- Seguem a constituição v1.1.0: toda escrita passa pelo Django Admin e exige usuário autenticado e autorizado; testes unitários com mocks, sem acesso a banco, e cobertura mínima de 90%; execução somente local.
- Perfis: há um único perfil de administrador com acesso total, inclusive à gestão de contas (decisão da sessão de clarificação de 2026-10-11). A pendência "Perfis e permissões do admin" fica resolvida por essa decisão.
- A recuperação de acesso (US-004) fica para um administrador redefinir a senha pelo procedimento documentado, sem envio de e-mail. Uma solução automática será avaliada somente se o sistema for disponibilizado a administradores reais.
- Contas são criadas por administradores; não há cadastro público de administradores.
- A decisão entre o usuário padrão do Django e um usuário personalizado (PENDENCIAS) precisa ser tomada antes da primeira migration e será resolvida na fase de planejamento.
- Como a consulta pública não exige login, a sessão administrativa é usada apenas no painel do Django Admin. O frontend separado não terá tela de login do administrador.
- Não há limite de tentativas de entrada nem bloqueio temporário, pois o sistema roda apenas localmente (decisão da sessão de clarificação de 2026-10-11). Isso deve ser reavaliado antes de qualquer exposição fora do ambiente local.
- Referências: `docs/04-backlog-do-produto.md` (US-004, 005 e 006), `docs/02-arquitetura-do-sistema.md`, `docs/06-requisitos-nao-funcionais.md` e `docs/PENDENCIAS.md`.
