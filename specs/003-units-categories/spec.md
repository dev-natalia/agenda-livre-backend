# Feature Specification: Gestão de Unidades e Categorias

**Feature Branch**: `003-units-categories`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "feature 03 dentro de docs/04-backlog-do-produto.md" (EP-03 — Gestão de unidades e categorias: US-007 Cadastrar e atualizar unidades, US-008 Cadastrar e atualizar categorias)

## User Scenarios & Testing *(mandatory)*

Os usuários desta feature são as pessoas administradoras do Agenda Livre (equipe do CEU Navegantes e da equipe do projeto). Unidades e categorias são os cadastros de apoio sobre os quais as atividades serão criadas nas features seguintes: toda atividade pertencerá a uma única unidade e terá uma única categoria principal, escolhidas a partir de registros administráveis, nunca digitadas livremente. Todo o gerenciamento é feito pela área administrativa protegida entregue na feature 002.

### User Story 1 - Cadastrar e atualizar unidades (Priority: P1)

Uma pessoa administradora cadastra uma unidade informando ao menos o nome e o bairro, e depois pode corrigir ou complementar seus dados (endereço, descrição). O CEU Navegantes é a primeira unidade cadastrada.

**Why this priority**: sem unidade não há onde vincular atividades, e o filtro público por unidade e por bairro depende desse cadastro. É o requisito mínimo para a primeira versão utilizável.

**Independent Test**: com uma conta administradora, cadastrar o CEU Navegantes, editá-lo, tentar cadastrar outra unidade com o mesmo identificador e tentar salvar sem o nome.

**Acceptance Scenarios**:

1. **Dado** uma conta administradora, **Quando** ela cadastra uma unidade com nome e bairro, **Então** a unidade é salva e passa a constar na lista de unidades.
2. **Dado** um formulário de unidade sem o nome ou sem o bairro, **Quando** a pessoa tenta salvar, **Então** nada é salvo e a mensagem indica o campo a corrigir.
3. **Dado** uma unidade existente, **Quando** a pessoa altera seus dados e salva, **Então** as alterações passam a valer e a data da última atualização é renovada.
4. **Dado** uma unidade já cadastrada, **Quando** a pessoa tenta cadastrar outra com o mesmo identificador textual, **Então** o cadastro é recusado com mensagem clara.
5. **Dado** que a unidade não existe ainda, **Quando** a pessoa cadastra o CEU Navegantes, **Então** ele fica disponível como primeira unidade da plataforma.
6. **Dado** uma conta sem o perfil de administrador, **Quando** ela tenta cadastrar ou alterar uma unidade, **Então** o acesso é negado.

---

### User Story 2 - Cadastrar e atualizar categorias (Priority: P1)

Uma pessoa administradora mantém a lista de categorias usadas para classificar as atividades: cadastra, edita o nome e a descrição, e desativa categorias que não devem mais ser usadas.

**Why this priority**: toda atividade precisa de uma categoria principal escolhida entre registros administráveis, e a consulta pública será organizada e filtrada por categoria.

**Independent Test**: cadastrar uma categoria, editá-la, tentar duplicar o nome ou o identificador, tentar salvar sem nome e confirmar que a lista reflete cada resultado.

**Acceptance Scenarios**:

1. **Dado** uma conta administradora, **Quando** ela cadastra uma categoria com nome, **Então** a categoria é salva e passa a constar na lista.
2. **Dado** um formulário de categoria sem nome, **Quando** a pessoa tenta salvar, **Então** nada é salvo e a mensagem indica o campo a corrigir.
3. **Dado** uma categoria existente, **Quando** a pessoa altera o nome ou a descrição, **Então** as alterações passam a valer.
4. **Dado** uma categoria já cadastrada, **Quando** a pessoa tenta cadastrar outra com o mesmo nome ou identificador textual, **Então** o cadastro é recusado com mensagem clara.
5. **Dado** uma conta sem o perfil de administrador, **Quando** ela tenta cadastrar ou alterar uma categoria, **Então** o acesso é negado.

---

### User Story 3 - Desativar sem perder histórico (Priority: P1)

Uma pessoa administradora desativa uma unidade ou uma categoria que não será mais usada. O registro deixa de ser oferecido para novas atividades, mas as atividades e programações já vinculadas continuam intactas.

**Why this priority**: sem desativação segura, a única forma de retirar um cadastro de uso seria apagá-lo, o que destruiria o histórico das atividades. A regra protege a integridade dos dados desde o início.

**Independent Test**: desativar uma unidade e uma categoria que já tenham registros vinculados (ou simular o vínculo), confirmar que os vínculos permanecem e que os registros inativos não aparecem como opção para novos vínculos.

**Acceptance Scenarios**:

1. **Dado** uma unidade ativa, **Quando** a pessoa a desativa, **Então** ela é marcada como inativa e nenhum registro relacionado é apagado nem alterado.
2. **Dado** uma categoria ativa, **Quando** a pessoa a desativa, **Então** ela é marcada como inativa e os vínculos existentes são preservados.
3. **Dado** uma unidade ou categoria inativa, **Quando** a pessoa cria uma nova atividade, **Então** o registro inativo não é oferecido como opção.
4. **Dado** uma unidade ou categoria inativa, **Quando** a pessoa a reativa, **Então** ela volta a ser oferecida para novas atividades.
5. **Dado** uma unidade ou categoria que já possui atividades vinculadas, **Quando** a pessoa tenta apagá-la, **Então** a exclusão é impedida e a pessoa é orientada a desativá-la.

---

### Edge Cases

- Nome da unidade ou da categoria composto só por espaços, ou com espaços sobrando no início e no fim.
- Nomes que diferem apenas por maiúsculas, minúsculas ou acentos (por exemplo, "Cultura e Artes" e "cultura e artes").
- Identificador textual gerado a partir do nome colide com o de outro registro.
- Alteração do nome de uma unidade ou categoria já usada por atividades: os vínculos permanecem e passam a exibir o nome novo.
- Desativação da única unidade ativa ou de todas as categorias: o sistema permite, mas novas atividades só poderão ser criadas depois de reativar ou cadastrar outro registro.
- Duas pessoas administradoras editando o mesmo registro ao mesmo tempo.
- Texto muito longo em nome, endereço ou descrição.
- Tentativa de cadastro por conta autenticada sem o perfil de administrador, inclusive por endereço direto.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir que administradores autorizados cadastrem e editem unidades pelo Django Admin, sem telas administrativas customizadas (Constituição, Princípio I).
- **FR-002**: Toda unidade MUST ter nome e bairro obrigatórios; endereço e descrição são opcionais.
- **FR-003**: O sistema MUST impedir duas unidades com o mesmo identificador textual (slug).
- **FR-004**: O sistema MUST permitir desativar e reativar uma unidade sem apagar nem alterar atividades ou programações relacionadas.
- **FR-005**: O sistema MUST permitir cadastrar o CEU Navegantes como primeira unidade, sem tratamento especial: ele é um registro comum, de modo que outras unidades possam ser cadastradas depois sem mudança na estrutura.
- **FR-006**: O sistema MUST permitir que administradores autorizados cadastrem, editem, desativem e reativem categorias pelo Django Admin.
- **FR-007**: Toda categoria MUST ter nome obrigatório; a descrição é opcional.
- **FR-008**: O sistema MUST impedir duas categorias com o mesmo nome ou o mesmo identificador textual (slug).
- **FR-009**: A desativação de uma categoria MUST preservar todos os vínculos existentes com atividades.
- **FR-010**: Unidades e categorias inativas MUST NOT ser oferecidas como opção ao vincular novas atividades; os vínculos já existentes com registros inativos MUST permanecer válidos e visíveis para administradores.
- **FR-011**: O sistema MUST impedir a exclusão de uma unidade ou categoria que tenha atividades vinculadas, orientando a pessoa a desativá-la.
- **FR-012**: O sistema MUST gerar o identificador textual a partir do nome quando a pessoa não o informar, e MUST recusar identificadores inválidos ou repetidos.
- **FR-013**: O sistema MUST registrar automaticamente as datas de criação e da última atualização de cada unidade e categoria, sem permitir edição manual.
- **FR-014**: Os formulários e listas MUST usar rótulos em português, validar campos obrigatórios antes de salvar e permitir distinguir facilmente registros ativos e inativos (por exemplo, por filtro e coluna de situação).
- **FR-015**: As listas de unidades e categorias MUST permitir busca por nome.
- **FR-016**: Todas as operações de escrita MUST exigir conta autenticada com o perfil de administrador, com verificação no servidor (herdado da feature 002).
- **FR-017**: Esta feature MUST NOT incluir cadastro de atividades, programações ou públicos-alvo, nem endpoints públicos de consulta; a exposição pública de unidades e categorias para filtros fica para a feature de consulta pública.
- **FR-018**: O sistema MUST oferecer um meio documentado e repetível de criar as primeiras unidades e as categorias iniciais, para que o ambiente de demonstração possa ser preparado sem digitar tudo manualmente.

### Key Entities *(include if feature involves data)*

- **Unidade**: local que realiza atividades (CEU Navegantes é a primeira). Possui nome, identificador textual único, bairro, endereço em texto simples (opcional), descrição (opcional), situação ativa ou inativa e datas de criação e atualização. Uma unidade terá várias atividades; cada atividade pertence a uma única unidade.
- **Categoria**: classificação principal de uma atividade. Possui nome único, identificador textual único, descrição (opcional), situação ativa ou inativa e datas de criação e atualização. Uma categoria pode ter várias atividades; cada atividade tem exatamente uma categoria.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa administradora cadastra uma nova unidade ou categoria em menos de 2 minutos, a partir do painel.
- **SC-002**: 100% das tentativas de salvar unidade sem nome ou sem bairro, ou categoria sem nome, são recusadas com mensagem indicando o campo a corrigir.
- **SC-003**: 100% das tentativas de criar unidade ou categoria com identificador (e, nas categorias, nome) já existente são recusadas.
- **SC-004**: Após desativar uma unidade ou categoria, 0 registros vinculados são apagados ou alterados, e o registro deixa de aparecer como opção para novas atividades em 100% dos casos.
- **SC-005**: 100% das tentativas de excluir unidade ou categoria com atividades vinculadas são impedidas.
- **SC-006**: 100% das operações de escrita por contas sem o perfil de administrador ou sem autenticação são recusadas.
- **SC-007**: Seguindo apenas a documentação, a equipe prepara o ambiente de demonstração com o CEU Navegantes e as categorias iniciais em até 5 minutos.

## Assumptions

- "Feature 03" refere-se ao épico EP-03 do backlog (US-007 e US-008), a terceira feature na sequência de implementação, após 001 (EP-01) e 002 (EP-02).
- Seguem a constituição v1.1.0: toda escrita passa pelo Django Admin e exige usuário autenticado e autorizado; testes unitários com mocks, sem acesso a banco, e cobertura mínima de 90%; execução somente local.
- Os campos seguem `docs/03-modelo-de-dados.md`: o bairro é obrigatório para unidades (decisão de 2026-10-11); o identificador textual é obrigatório e único em ambas as entidades. A pendência "campos obrigatórios finais de unidade" fica resolvida por esse documento, podendo ser revista antes da publicação.
- Unidades e categorias são cadastros de apoio sem hierarquia: não há categorias aninhadas nem unidades vinculadas a outras.
- A lista de categorias iniciais usa a proposta do documento de visão (Cultura e Artes, Cursos e Formação, Esporte e Atividade Física, Lazer e Recreação, Saúde e Bem-estar, Educação e Meio Ambiente, Eventos e Encontros, Participação Comunitária). A validação definitiva com os responsáveis continua pendente e não bloqueia esta feature, pois as categorias são editáveis.
- A atividade (feature 004) ainda não existe; por isso as regras de vínculo (não oferecer inativos, impedir exclusão com vínculo, preservar vínculos na desativação) são especificadas aqui como comportamento esperado do cadastro e verificadas com testes unitários com mocks, e serão exercitadas ponta a ponta quando as atividades forem criadas.
- A desativação é a forma recomendada de retirar um registro de uso; a exclusão física só é possível quando não há atividades vinculadas.
- O identificador textual é derivado do nome, em minúsculas, sem acentos e com hifens, e pode ser ajustado pela pessoa administradora.
- Não há campo de imagem, coordenadas ou contato nas unidades nesta versão; o endereço é texto simples.
- Referências: `docs/04-backlog-do-produto.md` (US-007 e US-008), `docs/03-modelo-de-dados.md` (entidades `Unit` e `Category`), `docs/01-visao-do-produto-e-requisitos.md` (seções 8 e 9) e `docs/PENDENCIAS.md`.
