# Feature Specification: Qualidade, Segurança e Acessibilidade

**Feature Branch**: `007-quality-security-accessibility`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "feature 007 dentro de docs/04-*" (EP-07 — Qualidade, segurança e acessibilidade: US-027 Utilizar a plataforma sem autenticação na área pública, US-028 Usar a interface com recursos de acessibilidade, US-029 Tratar entradas inválidas, US-030 Registrar auditoria de conteúdo)

## User Scenarios & Testing *(mandatory)*

As features 001 a 006 entregaram a administração, os cadastros, as atividades, as programações e a consulta pública. Esta feature **consolida os requisitos transversais do EP-07** sobre o que já existe: garante, de ponta a ponta, que a área pública é aberta e não vaza dados internos (US-027), que os dados e erros da API sustentam um frontend acessível (US-028), que entradas inválidas são rejeitadas com mensagens úteis e seguras (US-029) e que a auditoria de autoria e de horários é consistente em todos os caminhos de escrita (US-030). Não cria telas nem endpoints novos para o público; o que for exclusivamente de interface (rótulos, foco, contraste) pertence ao repositório do frontend e aqui aparece apenas como o que o backend precisa fornecer.

Os atores são **visitantes** (sem conta), **administradores** (equipe do Agenda Livre) e **a equipe de desenvolvimento e revisão**.

### User Story 1 - Entradas inválidas são rejeitadas de forma segura e compreensível (Priority: P1)

Quem mantém o sistema quer que nenhum dado inválido entre, venha de formulário administrativo, de serviço interno ou de parâmetros da API pública, e que a resposta explique o problema sem expor detalhes internos.

**Why this priority**: integridade e estabilidade dos dados são pré-requisito para tudo o mais (prioridade P0 no backlog); falhas aqui corrompem o catálogo ou vazam informação.

**Independent Test**: enviar, a cada ponto de entrada, o conjunto de entradas inválidas (campo obrigatório ausente, relacionamento inexistente ou inativo, data/horário/status/dia da semana fora do domínio, identificador malformado, página inválida) e verificar que todas são recusadas, que nada é gravado e que a mensagem é clara e sem detalhes internos.

**Acceptance Scenarios**:

1. **Dado** um cadastro de unidade, categoria, atividade ou programação com campo obrigatório vazio, **Quando** é salvo, **Então** é recusado com mensagem indicando o campo e nada é gravado.
2. **Dado** uma atividade ligada a unidade ou categoria inexistente ou inativa, **Quando** é salva ou publicada, **Então** é recusada com mensagem compreensível.
3. **Dado** uma programação com data, horário, tipo de recorrência ou dia da semana inválidos (incluindo fim antes do início), **Quando** é salva, **Então** é recusada e a mensagem aponta o campo.
4. **Dado** uma mudança de situação não permitida, **Quando** solicitada, **Então** é recusada informando a situação atual e a pretendida.
5. **Dado** uma consulta pública com parâmetro malformado (data inválida, identificador que não é UUID, página inválida), **Quando** enviada, **Então** a API responde com erro de validação em formato único, com os problemas listados por campo.
6. **Dado** qualquer falha inesperada no servidor durante uma requisição da API, **Quando** a resposta é devolvida ao visitante, **Então** ela traz apenas uma mensagem genérica, sem rastreamento de pilha, caminhos, SQL, configuração ou segredos.

---

### User Story 2 - Área pública aberta e sem vazamento de dados internos (Priority: P1)

Uma pessoa visitante quer consultar atividades sem criar conta, e a equipe quer a garantia de que nenhuma resposta pública revela dados administrativos nem permite escrever.

**Why this priority**: é o requisito P0 de acesso aberto (US-027) e a principal proteção de privacidade (RNF-SEC-06).

**Independent Test**: percorrer todos os endpoints públicos sem credenciais (listagem, detalhe, filtros, busca, próximas ocorrências, listas de apoio) e verificar o acesso; tentar métodos de escrita nesses mesmos endereços e verificar a recusa; inspecionar os campos devolvidos.

**Acceptance Scenarios**:

1. **Dado** um visitante sem credenciais, **Quando** consulta qualquer endpoint público de leitura, **Então** a resposta é bem-sucedida sem pedir login.
2. **Dado** um visitante ou administrador autenticado, **Quando** tenta criar, alterar ou excluir conteúdo por qualquer endpoint público, **Então** a operação é recusada com "método não permitido" e nada muda.
3. **Dado** qualquer resposta pública (sucesso ou erro), **Quando** seus campos são examinados, **Então** não aparecem usuários que criaram ou atualizaram registros, identificadores internos de usuário, situação não pública, senhas, segredos ou informações de configuração.
4. **Dado** uma atividade que não está publicada, **Quando** um visitante a solicita por identificador, **Então** a resposta é indistinguível da de um identificador inexistente.
5. **Dado** que a área de gestão é restrita, **Quando** alguém não autenticado tenta acessá-la, **Então** o acesso é recusado.

---

### User Story 3 - Auditoria consistente de atividades e programações (Priority: P1)

Quem responde pelo sistema quer saber quem criou e quem atualizou cada atividade e programação, e quando, qualquer que seja o caminho da alteração.

**Why this priority**: rastreabilidade é requisito P0 (US-030, RNF-PRIV-02) e depende de nenhum caminho de escrita ficar de fora.

**Independent Test**: criar e depois alterar uma atividade e uma programação por cada caminho existente (formulário principal, programação em linha, mudança de situação) com usuários diferentes e conferir criador, atualizador e horários.

**Acceptance Scenarios**:

1. **Dado** um administrador que cria uma atividade ou programação, **Quando** salva, **Então** criador e atualizador são esse usuário e os horários de criação e atualização são registrados.
2. **Dado** um registro já existente, **Quando** outro administrador o altera, **Então** o criador permanece, o atualizador passa a ser o novo usuário e o horário de atualização avança.
3. **Dado** uma programação criada ou editada dentro da página da atividade, **Quando** salva, **Então** recebe os mesmos campos de auditoria que uma programação salva isoladamente.
4. **Dado** uma mudança de situação (publicar, cancelar, encerrar), **Quando** concluída, **Então** o atualizador e o horário de atualização da atividade refletem quem a fez.
5. **Dado** um usuário que é autor de registros, **Quando** se tenta removê-lo, **Então** a remoção é impedida (a autoria nunca fica órfã), e a política está documentada junto com a de operações automatizadas.
6. **Dado** os dados de auditoria, **Quando** a administração os exibe, **Então** aparecem somente para leitura e nunca podem ser editados manualmente.

---

### User Story 4 - Dados e erros da API sustentam um frontend acessível (Priority: P2)

A equipe do frontend quer que a API entregue informação estruturada e mensagens que permitam construir uma interface acessível, com erros associáveis aos campos.

**Why this priority**: a acessibilidade da interface é entregue no frontend; o backend só precisa não atrapalhar. É P2 porque depende de decisões de meta ainda pendentes (WCAG 2.2 AA proposto no DOC-06).

**Independent Test**: examinar as respostas públicas e de erro e verificar que cada dado de apresentação é textual e estruturado, e que cada erro de validação nomeia o campo.

**Acceptance Scenarios**:

1. **Dado** uma atividade pública, **Quando** a resposta é examinada, **Então** a situação, a modalidade, a unidade e a categoria vêm com nome legível por pessoas (não apenas código ou cor), e datas e horários vêm em formato inequívoco.
2. **Dado** um erro de validação em parâmetros ou campos, **Quando** a resposta é examinada, **Então** há mensagem geral e lista de mensagens por nome de campo, permitindo ao frontend associar cada erro ao seu campo.
3. **Dado** qualquer mensagem de erro, **Quando** lida por uma pessoa, **Então** está em português, descreve o problema e o que corrigir, sem jargão técnico nem códigos internos.
4. **Dado** que a meta de conformidade e o método de verificação de acessibilidade (WCAG 2.2 AA, ferramentas automáticas e revisão manual) estão no DOC-06, **Quando** a documentação do projeto é consultada, **Então** há registro claro do que o backend fornece e do que cabe ao frontend verificar.

---

### Edge Cases

- Parâmetros repetidos, vazios ou desconhecidos na consulta pública: resposta previsível (os desconhecidos são ignorados, conforme a feature 006), nunca erro interno.
- Textos muito longos, com espaços nas pontas ou com marcação HTML: aceitos ou recusados conforme o limite do campo, nunca interpretados como marcação nas respostas.
- Endereço externo com esquema perigoso (por exemplo, que executa código) ou malformado: recusado no cadastro.
- Corpo de requisição malformado ou tipo de conteúdo não suportado em endpoint que o receba: erro de cliente em formato único, não erro de servidor.
- Rota inexistente na API: resposta em formato JSON único, sem página técnica.
- Dois administradores salvam o mesmo registro quase ao mesmo tempo: o último a salvar fica como atualizador; nenhum campo de auditoria fica vazio.
- Atividade com programações criadas por um usuário e alteradas por outro: cada programação guarda a própria autoria.
- Operações em lote ou rotinas que alteram registros sem um usuário humano: hoje inexistentes; se surgirem, precisam de política definida antes (ver Pressupostos).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Todos os endpoints públicos de leitura MUST funcionar sem autenticação, e nenhum endpoint público MUST aceitar operações de escrita.
- **FR-002**: Respostas públicas, inclusive de erro, MUST NOT conter usuários autores ou atualizadores, identificadores internos de usuário, situação não pública, credenciais, segredos nem detalhes de configuração.
- **FR-003**: Atividades não publicadas MUST ser tratadas na área pública exatamente como inexistentes.
- **FR-004**: O sistema MUST validar no servidor a presença dos campos obrigatórios de unidade, categoria, atividade e programação, em todos os caminhos de entrada.
- **FR-005**: O sistema MUST recusar relacionamentos inexistentes ou inativos ao salvar ou publicar atividades.
- **FR-006**: O sistema MUST validar datas, horários, tipo de recorrência, dias da semana e situação, incluindo coerência entre início e fim.
- **FR-007**: O sistema MUST validar o formato de endereços externos e recusar esquemas não web.
- **FR-008**: Parâmetros da consulta pública MUST ser validados, e qualquer valor malformado MUST resultar em erro de validação, nunca em falha interna.
- **FR-009**: Todos os erros da API MUST seguir um formato JSON único: mensagem geral e, na validação, mensagens agrupadas por nome de campo.
- **FR-010**: Falhas inesperadas MUST ser respondidas com mensagem genérica, sem rastreamento de pilha, caminhos, consultas ou segredos, independentemente do ambiente.
- **FR-011**: Mensagens de erro MUST estar em português, ser compreensíveis por pessoas leigas e indicar o que corrigir.
- **FR-012**: Respostas públicas MUST apresentar situação, modalidade, unidade e categoria em forma textual legível, e datas e horários em formato inequívoco.
- **FR-013**: Atividades e programações MUST registrar usuário criador, usuário atualizador, horário de criação e horário de atualização.
- **FR-014**: Toda escrita administrativa MUST preencher a auditoria: formulário principal, programações dentro da atividade, programações isoladas e mudanças de situação.
- **FR-015**: Uma atualização MUST preservar o criador, trocar o atualizador e avançar o horário de atualização.
- **FR-016**: Campos de auditoria MUST ser somente leitura na administração.
- **FR-017**: A remoção de um usuário que seja autor de registros MUST ser impedida, e a política (contas removidas e operações automatizadas) MUST estar documentada.
- **FR-018**: Logs MUST NOT conter senhas, segredos ou dados pessoais desnecessários.
- **FR-019**: Cada requisito acima MUST ter testes automatizados unitários, sem acesso a banco, mantendo a cobertura total em pelo menos 90%.
- **FR-020**: A documentação MUST registrar o que o backend entrega para a acessibilidade e o que cabe ao frontend verificar.

### Key Entities *(include if feature involves data)*

- **Atividade**: registro com criador, atualizador e horários de auditoria; sua situação define a visibilidade pública.
- **Programação**: registro ligado a uma atividade, com autoria e horários próprios.
- **Usuário administrador**: conta que autoriza a escrita; aparece como autor, nunca em respostas públicas.
- **Resposta de erro**: mensagem geral mais, quando houver validação, lista de mensagens por campo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos endpoints públicos de leitura respondem com sucesso sem credenciais, e 100% das tentativas de escrita nesses endereços são recusadas.
- **SC-002**: Em 100% das respostas públicas examinadas (sucesso e erro), nenhum campo de autoria, usuário, segredo ou configuração aparece.
- **SC-003**: Cada categoria de entrada inválida da lista de cenários (campo obrigatório, relacionamento, data, horário, status, dia da semana, identificador, página) tem ao menos um teste que comprova a recusa e a ausência de gravação.
- **SC-004**: Em nenhuma situação de erro simulada a resposta contém rastreamento de pilha, caminho de arquivo, consulta ou segredo.
- **SC-005**: Em 100% das escritas administrativas testadas (por todos os caminhos), criador, atualizador e horários ficam preenchidos e corretos.
- **SC-006**: Toda mensagem de erro de validação nomeia o campo afetado, e uma pessoa revisora consegue entender o que corrigir em cada uma delas sem consultar o código.
- **SC-007**: A suíte completa passa, sem acesso a banco, com cobertura total de no mínimo 90%.

## Assumptions

- A feature não adiciona endpoints públicos; trabalha sobre os endpoints e a administração existentes (features 002 a 006).
- A consulta sem autenticação (US-027) já está implementada na feature 006; aqui ela é verificada de ponta a ponta e protegida contra regressão.
- A acessibilidade visual e de interação (rótulos, teclado, foco, hierarquia de títulos, contraste) é responsabilidade do frontend, em repositório separado; o backend entrega dados textuais e erros por campo. A meta proposta é WCAG 2.2 nível AA, conforme DOC-06, e é confirmada antes da validação final do produto.
- Política de contas removidas: manter a regra atual, que impede remover usuários que sejam autores (a autoria nunca fica órfã); contas que deixam a equipe são desativadas.
- Política de operações automatizadas: não existem hoje rotinas que alterem atividades ou programações sem usuário humano; se forem criadas, deverão definir o ator antes de entrar.
- Como o sistema roda apenas localmente, "ambiente hospedado" no backlog é tratado como a regra mais restritiva: o visitante nunca recebe detalhes internos de erro.
- Os testes são unitários, com mocks, sem banco, conforme a constituição; a estratégia mais ampla de casos de teste é assunto da spec `007-test-strategy`.
- Imagens e texto alternativo de imagens estão fora do escopo enquanto imagens não fizerem parte da primeira versão.
