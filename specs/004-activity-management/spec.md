# Feature Specification: Gestão de Atividades

**Feature Branch**: `004-activity-management`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "feature 04 dentro de docs/04-backlog-do-produto.md" (EP-04 — Gestão de atividades: US-009 Cadastrar uma atividade como rascunho, US-010 Selecionar públicos-alvo, US-011 Editar uma atividade, US-012 Publicar uma atividade, US-013 Cancelar uma atividade, US-014 Marcar uma atividade como encerrada)

## User Scenarios & Testing *(mandatory)*

Os usuários desta feature são as pessoas administradoras do Agenda Livre (equipe do CEU Navegantes e da equipe do projeto), que já entram na área administrativa (feature 002) e mantêm unidades e categorias (feature 003). Esta feature entrega o cadastro e o ciclo de vida das atividades: preparar como rascunho, descrever o público, editar, publicar, cancelar e encerrar. As datas e horários das atividades (programações) e a consulta pública chegam em features posteriores; aqui a atividade é tratada como o conteúdo geral, independente de quando acontece.

### User Story 1 - Cadastrar uma atividade como rascunho (Priority: P1)

Uma pessoa administradora cadastra uma nova atividade informando título, descrição, unidade e categoria (e, opcionalmente, resumo, observações sobre o público e link externo) e a salva como rascunho, para preparar o conteúdo antes de divulgá-lo.

**Why this priority**: sem atividades cadastradas não há conteúdo a publicar, editar ou consultar. É a base de todo o restante da feature.

**Independent Test**: com uma conta administradora, cadastrar uma atividade com os campos obrigatórios e verificar que ela fica salva como rascunho, com criador e horário registrados; tentar salvar sem um campo obrigatório e verificar a recusa.

**Acceptance Scenarios**:

1. **Dado** uma conta administradora, **Quando** ela informa título, descrição, unidade ativa e categoria ativa e salva, **Então** a atividade é criada com situação "rascunho".
2. **Dado** o formulário de cadastro, **Quando** algum campo obrigatório (título, descrição, unidade ou categoria) é deixado em branco, **Então** o cadastro é recusado com mensagem indicando o campo.
3. **Dado** o formulário de cadastro, **Quando** a pessoa escolhe a unidade e a categoria, **Então** são oferecidas apenas unidades e categorias ativas.
4. **Dado** uma atividade em rascunho, **Quando** alguém consulta o conteúdo público, **Então** a atividade não aparece.
5. **Dado** uma atividade recém-criada, **Quando** a pessoa administradora consulta seus dados, **Então** vê quem a criou, quem a atualizou por último e os respectivos horários.
6. **Dado** o formulário de cadastro, **Quando** são preenchidos resumo, observações sobre o público e link externo, **Então** esses campos são salvos; **E** um link externo malformado é recusado.

---

### User Story 2 - Selecionar públicos-alvo (Priority: P1)

Ao cadastrar ou editar uma atividade, a pessoa administradora marca uma ou mais opções padronizadas de público-alvo (por exemplo, crianças, adultos, pessoas idosas) e pode acrescentar uma observação livre, para descrever quem pode participar.

**Why this priority**: o público-alvo é parte central da descrição da atividade e alimenta filtros futuros; precisa existir antes da publicação para que o conteúdo esteja completo.

**Independent Test**: cadastrar uma atividade com duas opções de público e uma observação, verificar que as duas opções ficam vinculadas; tentar vincular a mesma opção duas vezes e verificar que não há duplicidade; verificar que opções inativas não são oferecidas.

**Acceptance Scenarios**:

1. **Dado** uma atividade, **Quando** a pessoa seleciona várias opções de público-alvo, **Então** todas ficam associadas à atividade.
2. **Dado** uma atividade com uma opção já selecionada, **Quando** a mesma opção é indicada novamente, **Então** o vínculo não é duplicado.
3. **Dado** uma atividade, **Quando** a pessoa preenche a observação livre sobre o público, **Então** o texto é salvo junto com a atividade, complementando as opções.
4. **Dado** uma opção de público-alvo inativa, **Quando** a pessoa escolhe públicos para uma atividade, **Então** a opção inativa não é oferecida para novos vínculos.
5. **Dado** uma atividade que já usa uma opção de público-alvo, **Quando** essa opção é desativada, **Então** o vínculo existente é preservado.
6. **Dado** uma atividade, **Quando** nenhuma opção é selecionada, **Então** a atividade pode ser salva como rascunho (a seleção só é exigida para publicar — ver FR-010).

---

### User Story 3 - Editar uma atividade (Priority: P1)

Uma pessoa administradora altera os dados de uma atividade existente para mantê-los corretos e atualizados, sem que ela perca sua identidade ou gere duplicatas.

**Why this priority**: informações mudam; sem edição, qualquer correção exigiria recriar a atividade.

**Independent Test**: editar o título e o público-alvo de uma atividade existente e verificar que o mesmo registro foi atualizado, com usuário e horário da alteração registrados e sem vínculos duplicados.

**Acceptance Scenarios**:

1. **Dado** uma atividade existente, **Quando** uma conta administradora altera campos editáveis e salva, **Então** as alterações são gravadas no mesmo registro, que mantém seu identificador.
2. **Dado** uma edição, **Quando** a pessoa remove um campo obrigatório ou escolhe unidade/categoria inválida, **Então** a edição é recusada e nada é alterado.
3. **Dado** uma edição salva, **Quando** a pessoa consulta a atividade, **Então** o usuário da última atualização e o horário refletem essa edição, e o criador original permanece o mesmo.
4. **Dado** uma atividade já vinculada a públicos-alvo, **Quando** ela é editada e salva repetidas vezes, **Então** os vínculos de público-alvo não são duplicados.
5. **Dado** uma atividade cuja unidade ou categoria foi desativada depois do cadastro, **Quando** ela é editada sem alterar esses campos, **Então** a edição é aceita e o vínculo existente é mantido.
6. **Dado** uma conta sem o perfil de administrador, **Quando** tenta editar, **Então** a operação é recusada.

---

### User Story 4 - Publicar uma atividade (Priority: P1)

Uma pessoa administradora publica uma atividade que está pronta, tornando-a elegível para a consulta pública.

**Why this priority**: publicar é o objetivo do produto — informar a comunidade. Sem publicação, o conteúdo fica restrito à administração.

**Independent Test**: publicar uma atividade completa em rascunho e verificar a mudança de situação, o registro de auditoria e a elegibilidade para consulta pública; tentar publicar uma atividade incompleta e verificar a recusa.

**Acceptance Scenarios**:

1. **Dado** uma atividade em rascunho com todos os dados obrigatórios válidos, **Quando** uma conta administradora a publica, **Então** a situação passa a "publicada" e ela fica elegível para a consulta pública.
2. **Dado** uma atividade em rascunho com dado obrigatório ausente ou inválido (incluindo unidade ou categoria hoje inativa), **Quando** a publicação é tentada, **Então** é recusada com mensagem explicando o motivo e a atividade permanece em rascunho.
3. **Dado** uma atividade que permanece em rascunho, **Quando** alguém consulta o conteúdo público, **Então** ela continua privada.
4. **Dado** uma publicação realizada, **Quando** a pessoa administradora consulta a atividade, **Então** o usuário responsável e o horário da mudança estão registrados.
5. **Dado** uma conta sem o perfil de administrador, **Quando** tenta publicar, **Então** a operação é recusada.
6. **Dado** uma atividade cancelada ou encerrada, **Quando** a pessoa a publica novamente, **Então** a atividade volta a ser publicada, desde que os dados obrigatórios sejam válidos.

---

### User Story 5 - Cancelar uma atividade (Priority: P1)

Uma pessoa administradora cancela uma atividade que não acontecerá como divulgado, preservando todo o seu histórico.

**Why this priority**: informar corretamente um cancelamento evita que a comunidade compareça a algo que não vai acontecer.

**Independent Test**: cancelar uma atividade publicada e verificar a nova situação, a preservação do registro e a auditoria; verificar que ela não é tratada como atividade normalmente disponível.

**Acceptance Scenarios**:

1. **Dado** uma atividade publicada, **Quando** uma conta administradora a cancela, **Então** a situação passa a "cancelada".
2. **Dado** uma atividade cancelada, **Quando** a pessoa consulta a administração, **Então** o registro e quaisquer programações associadas continuam existindo.
3. **Dado** uma atividade cancelada, **Quando** o conteúdo público é consultado, **Então** ela não é apresentada como atividade normalmente disponível (apenas "publicada" é pública).
4. **Dado** um cancelamento, **Quando** a atividade é consultada, **Então** usuário e horário da alteração estão registrados.
5. **Dado** uma conta sem o perfil de administrador, **Quando** tenta cancelar, **Então** a operação é recusada.

---

### User Story 6 - Marcar uma atividade como encerrada (Priority: P2)

Uma pessoa administradora marca como encerrada uma atividade que já terminou, mantendo sua situação administrativa atualizada sem apagar nada.

**Why this priority**: é organização administrativa; não bloqueia a divulgação nem o cancelamento, por isso vem depois.

**Independent Test**: marcar uma atividade publicada como encerrada e verificar a nova situação, a preservação dos dados e a auditoria.

**Acceptance Scenarios**:

1. **Dado** uma atividade publicada, **Quando** uma conta administradora a marca como encerrada, **Então** a situação passa a "encerrada".
2. **Dado** uma atividade encerrada, **Quando** a administração a consulta, **Então** a atividade e suas programações continuam preservadas.
3. **Dado** uma atividade encerrada, **Quando** o conteúdo público é consultado, **Então** ela não aparece (apenas "publicada" é pública).
4. **Dado** a mudança de situação, **Quando** a atividade é consultada, **Então** usuário e horário estão registrados.
5. **Dado** uma conta sem o perfil de administrador, **Quando** tenta encerrar, **Então** a operação é recusada.

---

### Edge Cases

- Título ou descrição só com espaços em branco: tratado como em branco e recusado.
- Duas atividades com o mesmo título: podem coexistir (por exemplo, turmas diferentes); o identificador textual é gerado de modo a não colidir (ver Assumptions).
- Unidade ou categoria desativada depois do cadastro: a atividade existente mantém o vínculo e continua editável; apenas novos vínculos e a publicação exigem opções ativas.
- Opção de público-alvo desativada depois de vinculada: o vínculo é preservado.
- Tentativa de excluir uma atividade que tem programações associadas: a exclusão é impedida; o caminho normal é cancelar ou encerrar.
- Pedido de mudança de situação para a situação em que a atividade já está (por exemplo, cancelar uma atividade já cancelada): sem efeito e sem erro confuso.
- Conta administradora desativada depois de criar atividades: as atividades e seus registros de autoria são preservados.
- Duas pessoas editando a mesma atividade quase ao mesmo tempo: prevalece a última gravação, e a auditoria mostra quem fez a última alteração.
- Link externo malformado ou com endereço que não seja web: recusado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir a pessoas administradoras cadastrar uma atividade com título, descrição, unidade e categoria obrigatórios, e resumo, observações sobre o público e link externo opcionais.
- **FR-002**: O sistema MUST salvar toda atividade nova na situação "rascunho" por padrão.
- **FR-003**: O sistema MUST recusar o cadastro e a edição quando faltarem campos obrigatórios (considerando em branco o texto só com espaços) ou quando unidade/categoria não existirem.
- **FR-004**: O sistema MUST oferecer apenas unidades, categorias e opções de público-alvo ativas para novos vínculos, e MUST preservar vínculos já existentes com registros posteriormente desativados.
- **FR-005**: O sistema MUST validar que o link externo, quando informado, seja um endereço web válido.
- **FR-006**: O sistema MUST permitir associar a uma atividade uma ou mais opções padronizadas de público-alvo e um texto livre complementar, sem permitir a mesma opção duas vezes na mesma atividade.
- **FR-007**: O sistema MUST permitir a pessoas administradoras editar os campos de uma atividade existente, mantendo seu identificador e sem criar duplicidades de vínculos.
- **FR-008**: O sistema MUST registrar, para cada atividade, quem a criou, quem a atualizou por último e os horários correspondentes, atualizando-os a cada alteração, inclusive mudanças de situação.
- **FR-009**: O sistema MUST permitir publicar uma atividade, tornando-a elegível para a consulta pública, e MUST manter em sigilo as atividades em rascunho.
- **FR-010**: O sistema MUST exigir, para publicar, que título, descrição, unidade ativa, categoria ativa e ao menos uma opção de público-alvo estejam válidos, recusando a publicação com mensagem clara caso contrário.
- **FR-011**: O sistema MUST permitir cancelar uma atividade, passando-a à situação "cancelada" e preservando o registro e suas programações.
- **FR-012**: O sistema MUST permitir marcar uma atividade como encerrada, passando-a à situação "encerrada" e preservando o registro e suas programações.
- **FR-013**: O sistema MUST tratar como pública somente a atividade "publicada"; rascunho, cancelada e encerrada MUST ficar visíveis apenas para a administração.
- **FR-014**: O sistema MUST permitir cancelar ou encerrar apenas atividades publicadas e MUST permitir publicar novamente uma atividade cancelada ou encerrada; toda transição de situação MUST ser registrada na auditoria.
- **FR-015**: O sistema MUST restringir cadastro, edição e mudança de situação a contas com o perfil de administrador, verificando essa permissão no servidor.
- **FR-016**: O sistema MUST impedir a exclusão de atividades que tenham programações associadas, orientando a usar o cancelamento ou o encerramento.
- **FR-017**: O sistema MUST apresentar o cadastro de atividades no painel administrativo com rótulos em português, validação dos campos e possibilidade de filtrar e buscar atividades por situação, unidade, categoria e título.
- **FR-018**: O sistema MUST fornecer, na primeira carga de dados, as opções iniciais de público-alvo (crianças, adolescentes, adultos, pessoas idosas e todas as idades) e permitir à administração mantê-las pelo painel.

### Key Entities

- **Atividade**: conteúdo divulgado pela plataforma, independente de datas. Tem título, resumo opcional, descrição, observações opcionais sobre o público, link externo opcional, situação (rascunho, publicada, encerrada ou cancelada), unidade, categoria e dados de autoria (criador, último atualizador e horários).
- **Opção de público-alvo**: faixa padronizada de público (por exemplo, crianças, pessoas idosas), com nome e indicação de ativa/inativa.
- **Vínculo atividade–público-alvo**: relação entre uma atividade e uma opção de público-alvo; cada par existe no máximo uma vez.
- **Unidade e Categoria** (já existentes, feature 003): classificam a atividade; precisam estar ativas para novos vínculos.
- **Conta administradora** (feature 002): autora das criações e alterações, registrada na auditoria.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa administradora consegue cadastrar uma atividade completa como rascunho, incluindo público-alvo, em menos de 3 minutos.
- **SC-002**: 100% das atividades em rascunho, canceladas ou encerradas ficam fora do conteúdo público; apenas as publicadas são elegíveis.
- **SC-003**: 100% das tentativas de cadastrar, editar ou mudar a situação feitas por contas sem o perfil de administrador são recusadas sem alterar dados.
- **SC-004**: 100% das tentativas de publicar uma atividade com dados obrigatórios ausentes ou inválidos são recusadas com mensagem que indica o que corrigir.
- **SC-005**: Em 100% das alterações (criação, edição e mudança de situação), a atividade mostra quem fez a última alteração e quando.
- **SC-006**: Após qualquer número de edições, nenhuma atividade apresenta vínculos duplicados de público-alvo e nenhuma perde seu identificador.
- **SC-007**: Cancelar ou encerrar uma atividade não elimina nenhum dado: 100% dos registros e programações associados continuam existindo.

## Assumptions

- As features 001 (fundação), 002 (acesso administrativo) e 003 (unidades e categorias, ainda em branch própria, não mesclada) estão concluídas; esta feature depende de Unidade, Categoria, do perfil único de administrador e do painel administrativo.
- O cadastro e a manutenção acontecem pelo painel administrativo existente; não há tela administrativa própria nem escrita pública (decisão da constituição). Os endpoints de leitura pública pertencem a features posteriores.
- Há um único perfil de administrador, com acesso total (decisão da feature 002).
- As programações (datas e horários) pertencem à feature seguinte; por isso a publicação nesta feature não exige programação cadastrada. A regra de elegibilidade para consulta pública conforme programação será aplicada quando programações e consulta pública existirem.
- Fluxo de situações: rascunho → publicada; publicada → cancelada ou encerrada; cancelada ou encerrada → publicada novamente (reabertura). Não há retorno de publicada para rascunho nesta versão.
- A regra sobre "todas as idades" combinar ou não com outras opções não é imposta nesta versão; vale a lista inicial acima, ajustável pelo painel (pendência de refinamento do backlog).
- O identificador textual (slug) da atividade é gerado automaticamente a partir do título, com sufixo para evitar colisão; não é digitado pela pessoa administradora.
- A descrição é texto simples; imagens não fazem parte desta versão.
- Sem controle de edição simultânea: prevalece a última gravação.
- O sistema roda apenas localmente; hospedagem, backup e monitoramento estão fora do escopo.
