# Feature Specification: Gestão de Programações

**Feature Branch**: `005-schedule-management`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "feature 005, dentro de docs/04-backlog-do-produto.md" (EP-05 — Gestão de programações: US-015 Cadastrar programação pontual, US-016 Cadastrar programação recorrente, US-017 Editar uma programação, US-018 Consultar as próximas ocorrências)

## User Scenarios & Testing *(mandatory)*

Os usuários desta feature são as pessoas administradoras do Agenda Livre, que já entram na área administrativa (feature 002), mantêm unidades e categorias (feature 003) e cadastram atividades (feature 004). Esta feature entrega o "quando" das atividades: datas, horários e recorrência semanal. A exposição pública das programações e a busca por data pertencem a features posteriores; aqui a regra de cálculo das próximas ocorrências passa a existir e é visível para a administração.

### User Story 1 - Cadastrar programação pontual (Priority: P1)

Uma pessoa administradora cadastra, para uma atividade, uma programação que acontece em uma única data, informando a data e os horários de início e término.

**Why this priority**: sem data e horário, a atividade não informa à comunidade quando acontece. A programação pontual é o caso mais simples e base das demais.

**Independent Test**: com uma conta administradora, cadastrar uma programação pontual para uma atividade existente e verificar que fica salva com data, horários e autoria; tentar salvar com horário inválido e verificar a recusa.

**Acceptance Scenarios**:

1. **Dado** uma atividade existente, **Quando** a pessoa administradora informa uma data, horário de início e horário de término válidos e salva, **Então** a programação pontual é criada e associada à atividade.
2. **Dado** o cadastro de uma programação pontual, **Quando** o horário de início ou o de término é deixado em branco, **Então** o cadastro é recusado com mensagem indicando o campo.
3. **Dado** o cadastro, **Quando** o horário de término não é posterior ao de início (inclusive horários que atravessariam a meia-noite), **Então** o cadastro é recusado com mensagem explicativa.
4. **Dado** uma programação pontual, **Quando** ela é consultada, **Então** a data inicial e a data final são a mesma data informada.
5. **Dado** uma programação criada, **Quando** a administração a consulta, **Então** vê quem a criou, quem a atualizou por último e os respectivos horários.
6. **Dado** o cadastro, **Quando** é escolhida a atividade, **Então** qualquer atividade (rascunho, publicada, cancelada ou encerrada) pode receber programações.

---

### User Story 2 - Cadastrar programação recorrente (Priority: P1)

Uma pessoa administradora cadastra uma programação que se repete em dias da semana específicos ao longo de um período (por exemplo, terças e quintas, das 14h às 15h, de março a junho).

**Why this priority**: a maior parte das atividades dos CEUs é semanal; sem recorrência, cada ocorrência exigiria um cadastro separado.

**Independent Test**: cadastrar uma programação recorrente com dois dias da semana e um período, verificar que os dias ficam vinculados sem duplicidade e que cada regra de validação é aplicada.

**Acceptance Scenarios**:

1. **Dado** uma atividade, **Quando** a pessoa informa período de validade (data inicial e final), horário e ao menos um dia da semana e salva, **Então** a programação recorrente é criada.
2. **Dado** o cadastro de uma programação recorrente, **Quando** nenhum dia da semana é selecionado, **Então** o cadastro é recusado.
3. **Dado** o cadastro, **Quando** a data inicial é posterior à data final, **Então** o cadastro é recusado com mensagem explicativa.
4. **Dado** uma programação recorrente, **Quando** o mesmo dia da semana é indicado mais de uma vez, **Então** ele não é duplicado.
5. **Dado** uma programação recorrente, **Quando** ela é consultada, **Então** as ocorrências são calculadas a partir do período, dos dias da semana e do horário, sem que cada ocorrência seja um cadastro à parte.
6. **Dado** o cadastro de uma recorrência, **Quando** a pessoa busca cancelar ou alterar uma única ocorrência isoladamente, **Então** isso não é oferecido nesta versão (só é possível alterar a programação inteira).

---

### User Story 3 - Editar uma programação (Priority: P1)

Uma pessoa administradora corrige ou atualiza datas, horários e dias da semana de uma programação existente.

**Why this priority**: horários mudam; sem edição, qualquer correção exigiria apagar e recriar a programação.

**Independent Test**: editar o horário e os dias da semana de uma programação recorrente e verificar que as regras são reaplicadas, a autoria é atualizada, não há dias duplicados e as ocorrências refletem a mudança.

**Acceptance Scenarios**:

1. **Dado** uma programação existente, **Quando** a pessoa administradora altera data, horário ou dias da semana e salva, **Então** a mudança é gravada na mesma programação.
2. **Dado** uma edição, **Quando** os dados passam a violar uma regra (período invertido, horário inválido, recorrente sem dia da semana), **Então** a edição é recusada e nada é alterado.
3. **Dado** uma edição salva, **Quando** a programação é consultada, **Então** o usuário da última atualização e o horário refletem a edição, e o criador original permanece o mesmo.
4. **Dado** uma programação recorrente editada várias vezes, **Quando** seus dias da semana são consultados, **Então** não há dias repetidos.
5. **Dado** uma programação editada, **Quando** suas próximas ocorrências são calculadas, **Então** elas refletem os dados atualizados.
6. **Dado** uma programação, **Quando** a pessoa muda seu tipo (pontual ↔ recorrente), **Então** as regras do novo tipo passam a valer (por exemplo, pontual não mantém dias da semana).
7. **Dado** uma conta sem o perfil de administrador, **Quando** tenta cadastrar ou editar programações, **Então** a operação é recusada.

---

### User Story 4 - Consultar as próximas ocorrências (Priority: P2)

A pessoa administradora (e, nas próximas features, a pessoa visitante) vê as próximas datas e horários em que uma atividade acontecerá, calculados a partir de suas programações.

**Why this priority**: é o resultado útil das programações, mas depende delas e a exposição pública fica para a feature de consulta pública; por isso vem depois.

**Independent Test**: para uma atividade com uma programação pontual e uma recorrente, verificar que a lista de próximas ocorrências traz apenas datas de hoje em diante, em ordem cronológica, respeitando período, dias da semana e fuso horário.

**Acceptance Scenarios**:

1. **Dado** uma programação pontual futura, **Quando** as próximas ocorrências são calculadas, **Então** aparece uma ocorrência com a data e o horário correspondentes.
2. **Dado** uma programação recorrente, **Quando** as próximas ocorrências são calculadas, **Então** só aparecem datas dentro do período de validade e nos dias da semana selecionados, com o horário da programação.
3. **Dado** programações com datas já passadas, **Quando** as próximas ocorrências são calculadas, **Então** ocorrências anteriores ao momento atual não são apresentadas como próximas.
4. **Dado** uma ocorrência de hoje cujo horário de término já passou, **Quando** as próximas ocorrências são calculadas, **Então** ela não é listada como próxima.
5. **Dado** uma atividade cancelada ou encerrada, **Quando** suas próximas ocorrências são consultadas, **Então** ela não é apresentada como atividade com ocorrências disponíveis (apenas atividades publicadas têm próximas ocorrências).
6. **Dado** uma atividade sem programações ou sem datas futuras, **Quando** as próximas ocorrências são consultadas, **Então** o resultado é vazio, sem erro.
7. **Dado** o cálculo de ocorrências, **Quando** o dia é definido, **Então** vale o fuso horário configurado para a aplicação, não o do navegador ou do servidor.

---

### Edge Cases

- Programação recorrente cujo período não contém nenhum dos dias da semana escolhidos: é aceita, mas não gera ocorrências (a consulta de ocorrências fica vazia).
- Período recorrente de um único dia: válido; gera ocorrência apenas se o dia da semana coincidir.
- Programação pontual com data final diferente da inicial: recusada.
- Horário de término igual ao de início: recusado (término precisa ser posterior ao início).
- Programação com data no passado: aceita no cadastro (útil para histórico), mas nunca listada como próxima ocorrência.
- Duas programações idênticas na mesma atividade: permitidas; não há regra de unicidade entre programações.
- Programações sobrepostas na mesma atividade (mesmo dia, horários que se cruzam): permitidas nesta versão.
- Exclusão de uma programação: não exclui a atividade; já a exclusão de atividade com programações continua impedida (feature 004).
- Atividade cancelada ou encerrada: suas programações são preservadas e continuam editáveis pela administração.
- Conta administradora desativada depois de criar programações: os registros de autoria são preservados.
- Mudança de horário de verão: o cálculo usa o fuso configurado; horários são tratados como horário local da unidade.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir a pessoas administradoras cadastrar uma programação associada a uma atividade existente, escolhendo entre os tipos "pontual" e "recorrente".
- **FR-002**: O sistema MUST exigir, em toda programação, atividade, tipo, período (data inicial e final) e horários de início e término.
- **FR-003**: O sistema MUST recusar programações cuja data inicial seja posterior à data final, com mensagem clara.
- **FR-004**: O sistema MUST recusar programações cujo horário de término não seja posterior ao de início; horários que atravessam a meia-noite não são suportados nesta versão.
- **FR-005**: O sistema MUST exigir, em programação pontual, que a data inicial e a final sejam iguais, e MUST impedir que ela tenha dias da semana.
- **FR-006**: O sistema MUST exigir, em programação recorrente, pelo menos um dia da semana (segunda a domingo) e MUST impedir o mesmo dia duas vezes na mesma programação.
- **FR-007**: O sistema MUST calcular as ocorrências a partir das regras da programação, sem armazenar uma linha por ocorrência.
- **FR-008**: O sistema MUST NOT oferecer exceções individuais (cancelar, remarcar ou alterar uma única ocorrência) nesta versão.
- **FR-009**: O sistema MUST permitir a pessoas administradoras editar uma programação existente (datas, horários, tipo e dias da semana), reaplicando todas as validações e sem criar dias duplicados.
- **FR-010**: O sistema MUST registrar, para cada programação, quem a criou, quem a atualizou por último e os horários correspondentes, atualizando-os a cada alteração.
- **FR-011**: O sistema MUST calcular as próximas ocorrências de uma atividade em ordem cronológica, incluindo somente ocorrências ainda não encerradas no momento da consulta, e respeitando o período de validade, os dias da semana e o fuso horário configurado para a aplicação.
- **FR-012**: O sistema MUST considerar a situação da atividade no cálculo: apenas atividades "publicadas" têm próximas ocorrências apresentadas como disponíveis; para rascunho, cancelada e encerrada o resultado é vazio.
- **FR-013**: O sistema MUST preservar as programações quando a atividade é cancelada ou encerrada, e MUST impedir que a exclusão de uma programação apague a atividade.
- **FR-014**: O sistema MUST restringir cadastro, edição e exclusão de programações a contas com o perfil de administrador, verificando a permissão no servidor.
- **FR-015**: O sistema MUST apresentar o cadastro de programações no painel administrativo, dentro da própria atividade e também em lista própria, com rótulos em português, dias da semana nomeados, validação dos campos e possibilidade de filtrar por atividade, tipo e período.
- **FR-016**: O sistema MUST apresentar, na administração de cada atividade, as próximas ocorrências calculadas.

### Key Entities

- **Programação**: define quando uma atividade acontece. Pertence a uma atividade; tem tipo (pontual ou recorrente), data inicial, data final, horário de início, horário de término e dados de autoria (criador, último atualizador e horários).
- **Dia da semana da programação**: cada dia (segunda a domingo) em que uma programação recorrente acontece; cada par programação–dia existe no máximo uma vez; programações pontuais não têm dias.
- **Ocorrência**: data e horário concretos calculados a partir de uma programação; não é armazenada.
- **Atividade** (feature 004): recebe uma ou mais programações; sua situação influencia a disponibilidade das ocorrências.
- **Conta administradora** (feature 002): autora das criações e alterações, registrada na auditoria.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa administradora consegue cadastrar uma programação recorrente completa (período, horário e dias da semana) em menos de 2 minutos.
- **SC-002**: 100% das tentativas de salvar programações com período invertido, horário de término não posterior ao de início, pontual com datas diferentes ou recorrente sem dia da semana são recusadas com mensagem que indica o que corrigir.
- **SC-003**: Em 100% das criações e edições, a programação mostra quem fez a última alteração e quando.
- **SC-004**: Após qualquer número de edições, nenhuma programação apresenta dias da semana duplicados.
- **SC-005**: 100% das tentativas de cadastrar, editar ou excluir programações feitas por contas sem o perfil de administrador são recusadas sem alterar dados.
- **SC-006**: Em 100% dos casos de teste de cálculo (pontual, recorrente, período sem dias coincidentes, datas passadas, ocorrência de hoje já terminada, atividade não publicada), as próximas ocorrências correspondem exatamente ao esperado.
- **SC-007**: Cancelar ou encerrar uma atividade não elimina nenhuma de suas programações.

## Assumptions

- As features 001 a 004 estão concluídas; esta feature depende de Atividade, do perfil único de administrador e do painel administrativo.
- O cadastro acontece pelo painel administrativo existente; não há tela administrativa própria nem escrita pública. Endpoints públicos de leitura (listagem, detalhes, busca e filtro por data) pertencem às features seguintes; aqui a regra de cálculo das ocorrências é entregue e exibida para a administração, e será reutilizada por elas.
- A numeração dos dias da semana segue 1 = segunda-feira a 7 = domingo (DOC-03).
- Horários que atravessam a meia-noite não são suportados na primeira versão (DOC-03, sujeito a confirmação); término deve ser posterior ao início no mesmo dia.
- Datas inicial e final são inclusivas nas duas pontas no cálculo da recorrência.
- Os horários são tratados como horário local da unidade, no fuso da aplicação; o "agora" do cálculo usa esse fuso.
- Programações no passado e programações sobrepostas são permitidas; não há bloqueio por conflito de horário.
- Publicar uma atividade não exige programação cadastrada (decisão da feature 004); a elegibilidade para consulta pública conforme programação será aplicada na feature de consulta pública.
- Não há limite de programações por atividade nesta versão.
- Cancelar ou encerrar a atividade não altera as programações; o efeito sobre a disponibilidade é aplicado no cálculo (FR-012).
- O sistema roda apenas localmente; hospedagem, backup e monitoramento estão fora do escopo.
