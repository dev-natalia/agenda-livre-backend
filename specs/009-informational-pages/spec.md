# Feature Specification: Páginas Informativas (Sobre e Contato)

**Feature Branch**: `009-informational-pages`

**Created**: 2026-10-11

**Status**: Implemented

**Input**: User description: "feature 009 dentro de docs/04-*" (EP-09 — Páginas informativas e contato: US-035 Página de contato demonstrativa e US-036 Ler a página Sobre, ambas P2 e somente frontend, sem endpoint no backend)

## User Scenarios & Testing *(mandatory)*

As features 001 a 008 entregaram a fundação, a administração, os cadastros, as atividades, as programações, a consulta pública, os requisitos transversais e o EP-08. Esta feature trata do **último épico do backlog (EP-09)**. Por decisão de 2026-10-11, as páginas **Sobre** (texto fixo) e **Contato** (apenas demonstrativa, sem envio) existem **somente no frontend** e **não têm endpoint no backend**.

Portanto, o trabalho desta feature no backend **não é criar funcionalidade**, e sim **garantir e documentar a fronteira**: que o backend não expõe, não recebe e não armazena nada relativo a Sobre e Contato, e que a equipe do frontend sabe exatamente o que esperar (e o que não esperar) da API. As histórias de visitante (US-035 e US-036) são cumpridas pelo frontend; aqui elas viram critérios verificáveis de ausência.

Os atores são **a pessoa visitante** (que lê as páginas no frontend), **a pessoa desenvolvedora do frontend** (que as implementa) e **a pessoa responsável pela avaliação do projeto** (que confere o escopo entregue).

### User Story 1 - Backend não expõe nem guarda dados de Sobre e Contato (Priority: P1)

Uma pessoa responsável pela avaliação quer ter certeza de que a página de contato é realmente apenas demonstrativa: nenhuma mensagem enviada por visitantes chega ao backend, é armazenada ou é registrada, e nenhum conteúdo da página Sobre vem de lá.

**Why this priority**: é o único comportamento verificável no backend e protege a privacidade (Princípio V da constituição): um endpoint de contato passaria a coletar dados pessoais de visitantes sem que o escopo tenha previsto isso.

**Independent Test**: percorrer todas as rotas publicadas pela API e pela área administrativa e confirmar que nenhuma delas trata Sobre ou Contato; tentar enviar uma mensagem de contato a caminhos plausíveis e confirmar que a resposta é "não encontrado", sem qualquer efeito colateral.

**Acceptance Scenarios**:

1. **Dado** o conjunto de rotas do backend, **Quando** é inspecionado, **Então** não existe nenhuma rota para enviar, listar ou ler mensagens de contato, nem para fornecer o texto da página Sobre.
2. **Dado** uma requisição de envio de mensagem a um caminho de contato plausível (por exemplo, `/api/contact/` ou `/api/contato/`), **Quando** ela chega ao backend, **Então** a resposta é o erro padronizado de "não encontrado" em JSON, nada é gravado no banco e nada do corpo da requisição é registrado nos logs.
3. **Dado** a área administrativa, **Quando** consultada, **Então** não há cadastro de mensagens de contato nem de textos da página Sobre.
4. **Dado** o modelo de dados, **Quando** inspecionado, **Então** não existe tabela de mensagens, contatos ou conteúdo estático de páginas.

---

### User Story 2 - Equipe do frontend sabe o que esperar do backend (Priority: P2)

Uma pessoa desenvolvedora do frontend quer um registro claro de que Sobre e Contato são páginas estáticas e demonstrativas, para implementá-las sem depender da API e sem esperar um endpoint que não existirá.

**Why this priority**: evita retrabalho e expectativas erradas entre os dois repositórios, mas não altera o comportamento do sistema.

**Independent Test**: ler a documentação do projeto e confirmar que uma única pessoa, sem consultar o código, consegue responder: "Sobre e Contato têm endpoint?", "o formulário de contato envia algo?" e "de onde vem o texto de Sobre?".

**Acceptance Scenarios**:

1. **Dado** a especificação da API (DOC-05), **Quando** lida, **Então** informa explicitamente que não há endpoints de Sobre nem de Contato e que o frontend não deve chamar a API para essas páginas.
2. **Dado** o README, **Quando** lido, **Então** registra que Sobre e Contato são exclusivas do frontend, com texto fixo e formulário demonstrativo sem envio.
3. **Dado** o backlog (DOC-04), **Quando** lido, **Então** US-035 e US-036 constam como "somente frontend" e US-035 registra que nenhuma mensagem é enviada nem armazenada.

---

### User Story 3 - Fechamento do backlog e do escopo documentados (Priority: P3)

A equipe quer que o backlog e a lista de pendências mostrem que todos os épicos estão tratados, para que o encerramento do backend seja inequívoco antes da entrega acadêmica.

**Why this priority**: é um fechamento documental; não altera o comportamento do sistema.

**Independent Test**: percorrer o backlog e as pendências e verificar que cada épico (EP-01 a EP-09) tem destino conhecido: implementado, fora do escopo ou exclusivo do frontend.

**Acceptance Scenarios**:

1. **Dado** o backlog, **Quando** lido, **Então** EP-09 consta como "somente frontend, sem trabalho no backend", e o histórico de revisões registra o fechamento desta feature.
2. **Dado** o arquivo de pendências, **Quando** lido, **Então** não resta item aberto referente a Sobre ou Contato no backend.
3. **Dado** o README, **Quando** lido, **Então** a lista de funcionalidades do backend e a lista do que fica fora do escopo coincidem com o backlog.

---

### Edge Cases

- Alguém, no futuro, adiciona por engano uma rota de contato ou de Sobre: o teste de ausência de rotas falha e bloqueia a mudança até que haja uma decisão formal de escopo (nova spec).
- O frontend, por engano, envia o formulário de contato à API: recebe o erro padronizado de "não encontrado"; nenhum dado digitado é gravado nem aparece nos logs de erro (feature 008), pois erros esperados de cliente não são registrados.
- Envio de requisição de contato com corpo grande ou malformado: a resposta continua sendo o erro padronizado de "não encontrado", sem detalhes técnicos expostos ao visitante.
- Pedido para que o texto de Sobre seja editável pela área administrativa: está fora do escopo desta feature e exigiria nova spec, pois a decisão vigente é texto fixo no frontend.
- Pedido para enviar e-mail real a partir do formulário de contato: fora do escopo; a página é demonstrativa.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O backend MUST NOT expor nenhuma rota para enviar, listar, ler, editar ou apagar mensagens de contato, nem para fornecer o texto da página Sobre.
- **FR-002**: Requisições a caminhos plausíveis de contato ou de Sobre MUST receber o erro padronizado de "não encontrado" em JSON, sem efeito colateral: nada é gravado no banco e nenhum conteúdo do corpo da requisição é registrado nos logs.
- **FR-003**: O backend MUST NOT armazenar mensagens de contato nem conteúdo de páginas informativas, e a área administrativa MUST NOT oferecer cadastro desses dados.
- **FR-004**: Um conjunto de verificações automatizadas MUST falhar caso surja no backend qualquer rota, modelo ou cadastro administrativo ligado a contato ou à página Sobre, protegendo a decisão de escopo.
- **FR-005**: A especificação da API (DOC-05) MUST declarar explicitamente que Sobre e Contato não têm endpoint e que o frontend não deve consultar a API para essas páginas.
- **FR-006**: O README MUST registrar que Sobre (texto fixo) e Contato (demonstrativa, sem envio) são exclusivas do frontend.
- **FR-007**: O backlog (DOC-04) MUST registrar US-035 e US-036 como somente frontend, com o critério de que a página de contato não envia nem armazena mensagens e de que não há endpoint, e MUST registrar o fechamento desta feature no histórico de revisões.
- **FR-008**: O arquivo de pendências MUST NOT conter item aberto referente a Sobre ou Contato no backend.
- **FR-009**: As verificações automatizadas desta feature MUST ser unitárias, sem acesso a banco, mantendo a cobertura total em pelo menos 90%.

### Key Entities *(include if feature involves data)*

Esta feature **não introduz nem altera entidades**. Por decisão de escopo, não existem no backend as entidades "Mensagem de contato" nem "Conteúdo da página Sobre"; a ausência delas é parte do que se quer garantir.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das tentativas de envio de contato simuladas a caminhos plausíveis, a resposta é "não encontrado" e nenhum registro é criado.
- **SC-002**: Em 100% das tentativas simuladas, nenhum conteúdo do corpo da requisição de contato aparece nos registros de erro.
- **SC-003**: A inspeção das rotas, dos modelos e do cadastro administrativo encontra 0 elementos ligados a Sobre ou Contato.
- **SC-004**: Uma pessoa desenvolvedora do frontend responde corretamente às três perguntas de escopo (endpoint, envio de formulário, origem do texto de Sobre) em até 2 minutos usando apenas a documentação.
- **SC-005**: 100% dos épicos do backlog (EP-01 a EP-09) têm destino documentado: implementado, fora do escopo ou exclusivo do frontend.
- **SC-006**: A suíte completa passa, sem acesso a banco, com cobertura total de no mínimo 90%.

## Assumptions

- "Feature 009" refere-se ao épico EP-09 do backlog (US-035 e US-036), a nona feature na sequência, após 001 a 008.
- A decisão de 2026-10-11 permanece válida: Sobre (texto fixo) e Contato (demonstrativa, sem envio) são exclusivas do frontend, sem endpoint, sem armazenamento e sem trabalho de funcionalidade no backend.
- Por isso, esta é uma feature de **proteção e documentação de escopo**: o ganho está em impedir que o backend colete dados de visitantes sem previsão e em alinhar os dois repositórios.
- Nenhum e-mail, notificação ou integração externa é feito a partir da página de contato.
- A implementação das páginas em si (conteúdo, layout, acessibilidade) pertence ao repositório do frontend e não é avaliada aqui.
- Os testes são unitários, com mocks, sem banco, conforme a constituição.
