# Feature Specification: Filtro por Público-alvo

**Feature Branch**: `011-audience-filter`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "Filtro por público-alvo conforme o épico EP-11 descrito em docs/10-filtro-por-publico-alvo.md (US-045 a US-050): novo endpoint público GET /api/v1/audiences/ (paginado, ordenado por nome, só públicos ativos, campos id, name, slug e description ou null, como /units/ e /categories/); parâmetro opcional audience (UUID, um único valor) em GET /api/v1/activities/, combinável pelo critério E com q, unit, category, neighborhood, date, date_from e date_to; identificador malformado responde 400 com errors.audience e identificador inexistente ou inativo responde 200 com lista vazia; regra inclusiva de "Todas as idades": filtrar por um público específico também devolve as atividades marcadas como "Todas as idades", filtrar por "Todas as idades" devolve só as marcadas com ela, e a atividade aparece uma única vez; "Todas as idades" é identificada por um novo campo booleano includes_everyone (padrão falso) em TargetAudience, marcado no Django Admin e carregado pelo seed_catalog, com migration aditiva em audiences; target_audiences (id e name, ordenados por nome, lista vazia se não houver) em cada item da listagem de atividades, sem consulta extra por atividade; filtro por público-alvo no list_filter do Django Admin (opções ativas mais inativas com atividades vinculadas); mudanças aditivas, sem alterar campos existentes. A US-050 (frontend) fica fora do backend. Atualizar DOC-03, DOC-05, o contrato da API pública e o README ao final."

## User Scenarios & Testing *(mandatory)*

As features 001 a 010 entregaram a fundação, a administração, os cadastros, as atividades, as programações, a consulta pública, os requisitos transversais, os ambientes, as páginas informativas e as imagens. Hoje a consulta pública filtra por unidade, categoria, bairro, data e busca por texto, mas **não por público-alvo**: o público já está cadastrado em cada atividade e aparece no detalhe, porém não na listagem, e não há como o frontend obter a lista de públicos para montar um seletor. Esta feature implementa o **EP-11 — Filtro por público-alvo** (`docs/10-filtro-por-publico-alvo.md`, US-045 a US-050), com a regra inclusiva de “Todas as idades” decidida em 2026-10-12.

Os atores são **a pessoa visitante** (que filtra e lê os resultados, por meio do frontend), **a pessoa desenvolvedora do frontend** (que consome os dados novos), **o administrador** (que mantém o catálogo de públicos-alvo e revisa atividades) e **a pessoa que apresenta o projeto** (que usa os dados de demonstração).

### User Story 1 - Visitante filtra as atividades por público-alvo (Priority: P1)

Uma pessoa visitante escolhe um público-alvo (por exemplo, “Adultos”) e vê somente as atividades voltadas a ele, mais as atividades abertas a “Todas as idades”. Se escolher a própria opção “Todas as idades”, vê somente as atividades marcadas com ela.

**Why this priority**: é o objetivo da feature e o que entrega valor direto a quem busca atividades para si ou para a família.

**Independent Test**: com atividades publicadas associadas a públicos diferentes (inclusive “Todas as idades”), consultar a listagem pública com o filtro de cada público e conferir quais atividades voltam; repetir com um identificador malformado, um inexistente e um inativo.

**Acceptance Scenarios**:

1. **Dado** atividades publicadas para “Adultos”, para “Crianças” e para “Todas as idades”, **Quando** a pessoa filtra por “Adultos”, **Então** recebe as atividades de “Adultos” e as de “Todas as idades”, e nenhuma de “Crianças”.
2. **Dado** as mesmas atividades, **Quando** a pessoa filtra por “Todas as idades”, **Então** recebe somente as marcadas com essa opção.
3. **Dado** uma atividade associada ao público escolhido e também a “Todas as idades”, **Quando** a pessoa filtra por esse público, **Então** a atividade aparece uma única vez.
4. **Dado** uma atividade associada a vários públicos, **Quando** a pessoa filtra por qualquer um deles, **Então** a atividade aparece, uma única vez.
5. **Dado** um identificador de público que não tem o formato válido, **Quando** a pessoa filtra, **Então** recebe um erro de parâmetro inválido indicando o campo do público, com mensagem em português.
6. **Dado** um identificador válido de um público que não existe ou está inativo, **Quando** a pessoa filtra, **Então** recebe uma lista vazia, sem erro.
7. **Dado** qualquer filtro por público, **Quando** a lista é montada, **Então** atividades em rascunho, canceladas ou encerradas nunca aparecem.
8. **Dado** a listagem sem o filtro, **Quando** consultada, **Então** o resultado, a ordenação e a paginação são idênticos aos de antes da feature.

---

### User Story 2 - Frontend obtém a lista de públicos-alvo (Priority: P1)

A pessoa desenvolvedora do frontend consulta um recurso público que lista os públicos-alvo disponíveis, para montar o seletor do filtro sem fixar valores no código.

**Why this priority**: sem a lista, o frontend não tem de onde obter os identificadores para filtrar; o filtro da história 1 fica inutilizável na prática.

**Independent Test**: consultar o recurso de públicos-alvo e conferir quais são listados, em que ordem, com quais campos, e que métodos de escrita são recusados.

**Acceptance Scenarios**:

1. **Dado** públicos-alvo ativos e inativos no catálogo, **Quando** o recurso é consultado, **Então** somente os ativos são listados, ordenados por nome.
2. **Dado** um público-alvo listado, **Quando** inspecionado, **Então** traz identificador, nome, identificador textual e descrição (ou ausente quando vazia), e nenhum dado administrativo.
3. **Dado** o recurso, **Quando** consultado sem login, **Então** responde normalmente.
4. **Dado** uma tentativa de criar, alterar ou apagar por esse recurso, **Quando** enviada, **Então** é recusada com o erro padrão de método não permitido.
5. **Dado** o catálogo sem públicos ativos, **Quando** o recurso é consultado, **Então** devolve uma lista vazia, sem erro.
6. **Dado** o formato paginado dos demais recursos de apoio (unidades e categorias), **Quando** o novo recurso é consultado, **Então** segue o mesmo formato de envelope e de paginação.

---

### User Story 3 - Administrador marca qual público significa “Todas as idades” (Priority: P1)

O administrador marca, no catálogo de públicos-alvo do Django Admin, a opção que significa “abrange todos” (a opção “Todas as idades”). É essa marca, e não o nome da opção, que o filtro usa para a regra inclusiva.

**Why this priority**: a regra da história 1 depende de saber qual público é “Todas as idades”; sem essa marca, o filtro inclusivo não funciona e a regra ficaria presa a um nome fixo.

**Independent Test**: no Admin, marcar e desmarcar a opção em um público-alvo e conferir que o comportamento do filtro da história 1 acompanha a marca; carregar o catálogo inicial e conferir que “Todas as idades” já vem marcada.

**Acceptance Scenarios**:

1. **Dado** o formulário de público-alvo no Admin, **Quando** o administrador o abre, **Então** vê uma caixa de seleção clara para indicar que o público abrange todos, desmarcada por padrão.
2. **Dado** o catálogo inicial carregado pelo comando de carga, **Quando** conferido, **Então** a opção “Todas as idades” está marcada e as demais não.
3. **Dado** um catálogo já existente com “Todas as idades” sem a marca, **Quando** o comando de carga é executado de novo, **Então** a marca passa a existir nessa opção, sem criar duplicatas.
4. **Dado** a marca removida de “Todas as idades”, **Quando** a pessoa filtra por “Adultos”, **Então** as atividades de “Todas as idades” deixam de ser incluídas.
5. **Dado** a marca colocada em outro público, **Quando** a pessoa filtra por um público específico, **Então** as atividades desse outro público passam a ser incluídas, pois o que vale é a marca.
6. **Dado** públicos-alvo já existentes antes da feature, **Quando** a mudança é aplicada, **Então** continuam válidos, com a marca desligada, sem perda de dados.

---

### User Story 4 - Combinar o público-alvo com os outros filtros (Priority: P2)

A pessoa visitante combina o público-alvo com unidade, categoria, bairro, data e busca por texto para refinar os resultados.

**Why this priority**: refina o uso do filtro, mas a história 1 já entrega valor sozinha.

**Independent Test**: aplicar o filtro de público junto com cada um dos outros e conferir que só voltam atividades que atendem a todos, e que combinações inválidas existentes continuam sendo recusadas como antes.

**Acceptance Scenarios**:

1. **Dado** o filtro de público e um filtro de unidade, **Quando** a lista é pedida, **Então** voltam só atividades daquela unidade voltadas ao público (ou a “Todas as idades”).
2. **Dado** o filtro de público junto com categoria, bairro, data, intervalo de datas ou busca por texto, **Quando** a lista é pedida, **Então** os resultados atendem a todos os filtros aplicados.
3. **Dado** uma combinação já inválida hoje (por exemplo, data junto de um intervalo), **Quando** o filtro de público também é enviado, **Então** o erro continua sendo o mesmo.
4. **Dado** vários parâmetros inválidos ao mesmo tempo, **Quando** a lista é pedida, **Então** cada um é reportado no seu campo.

---

### User Story 5 - Visitante vê o público-alvo em cada resultado (Priority: P2)

A pessoa visitante vê, em cada atividade da listagem, a quem ela se destina, sem precisar abrir os detalhes.

**Why this priority**: melhora a leitura dos resultados e dá contexto ao filtro, mas não é indispensável para filtrar.

**Independent Test**: consultar a listagem e conferir que cada atividade traz seus públicos-alvo em ordem, com lista vazia quando não há nenhum, e que a quantidade de consultas ao banco não cresce com o número de atividades.

**Acceptance Scenarios**:

1. **Dado** uma atividade com vários públicos-alvo, **Quando** a listagem é consultada, **Então** os públicos aparecem no item, com identificador e nome, ordenados por nome.
2. **Dado** uma atividade sem público-alvo, **Quando** a listagem é consultada, **Então** a lista de públicos vem vazia, nunca ausente nem nula.
3. **Dado** uma listagem com muitas atividades, **Quando** consultada, **Então** a quantidade de acessos ao banco não aumenta por atividade.
4. **Dado** os campos já existentes de cada item e o texto livre sobre o público, **Quando** a listagem é consultada, **Então** nada muda nos campos anteriores, e o texto livre continua somente no detalhe.

---

### User Story 6 - Administrador filtra a lista de atividades por público-alvo (Priority: P3)

O administrador filtra a lista de atividades do Django Admin por público-alvo para localizar e revisar atividades de um mesmo público.

**Why this priority**: conveniência administrativa; o produto funciona sem ela.

**Independent Test**: abrir a lista de atividades no Admin e conferir as opções do filtro de público e os resultados ao escolher cada uma.

**Acceptance Scenarios**:

1. **Dado** a lista de atividades no Admin, **Quando** aberta, **Então** o painel lateral oferece o filtro por público-alvo, ao lado de situação, unidade e categoria.
2. **Dado** o filtro de público, **Quando** inspecionadas as opções, **Então** aparecem os públicos ativos e também os inativos que ainda têm atividades vinculadas.
3. **Dado** uma opção escolhida, **Quando** a lista é filtrada, **Então** mostra as atividades vinculadas a ela, cada uma uma única vez.
4. **Dado** o filtro novo, **Quando** usado, **Então** as permissões e as ações em lote existentes continuam como estavam.

---

### Edge Cases

- Identificador de público vazio (`audience=`): tratado como **ausente**, igual aos filtros de unidade e categoria (nenhum filtro é aplicado).
- Identificador repetido (`audience=a&audience=b`): vale um único valor; é usado o último informado, sem erro, e o comportamento é o mesmo dos filtros de unidade e categoria.
- Público escolhido está ativo, mas nenhuma atividade publicada o usa: lista vazia, sem erro.
- Atividade publicada sem nenhum público-alvo: aparece na listagem geral e nunca em um filtro por público (nem como “Todas as idades”).
- Público inativo que ainda tem atividades vinculadas: filtrar por ele devolve lista vazia; as atividades continuam visíveis na listagem geral e mostram esse público em `target_audiences`.
- Nenhum público marcado como “abrange todos”: o filtro por um público específico devolve apenas as atividades vinculadas a ele.
- Mais de um público marcado como “abrange todos”: todos são tratados como “Todas as idades” pela regra inclusiva.
- Filtrar pelo público marcado como “abrange todos”: devolve somente as atividades vinculadas a ele, sem incluir as de outros públicos.
- Atividade vinculada ao público escolhido e a “Todas as idades” ao mesmo tempo: aparece uma única vez, sem duplicata na contagem nem na paginação.
- Contagem e paginação com o filtro: o total reflete as atividades distintas que atendem ao filtro.
- Mudança de página com o filtro ativo: segue a mesma regra da paginação existente (página inválida responde como hoje).
- Atividade com a data ou o filtro de data combinados ao de público: a ordenação por próxima ocorrência não muda.
- Catálogo inicial carregado em um banco já povoado: não duplica públicos nem tira marcas já feitas pelo administrador de outros públicos.
- Públicos-alvo cadastrados antes da feature: continuam funcionando; a marca começa desligada até o administrador ou o comando de carga marcá-la.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A consulta pública de atividades MUST aceitar um parâmetro opcional que indica um público-alvo pelo seu identificador, e MUST devolver somente atividades associadas a esse público, conforme as regras abaixo.
- **FR-002**: Quando o público escolhido **não** é o marcado como “abrange todos”, o resultado MUST incluir também as atividades associadas a qualquer público marcado como “abrange todos”.
- **FR-003**: Quando o público escolhido é o marcado como “abrange todos”, o resultado MUST conter somente as atividades associadas a ele.
- **FR-004**: Cada atividade MUST aparecer no máximo uma vez no resultado, mesmo que satisfaça mais de uma condição do filtro (vários públicos, ou público escolhido e “Todas as idades”), e a contagem e a paginação MUST refletir as atividades distintas.
- **FR-005**: Um identificador de público com formato inválido MUST responder com o erro padrão de parâmetro inválido (status 400), indicando o campo do público, com mensagem em português; os demais erros de validação continuam reportados por campo.
- **FR-006**: Um identificador bem formado que não existe ou que pertence a um público inativo MUST responder com sucesso e lista vazia, no mesmo comportamento dos filtros de unidade e categoria.
- **FR-007**: O filtro MUST respeitar a visibilidade pública: atividades em rascunho, canceladas ou encerradas nunca aparecem, com ou sem o filtro.
- **FR-008**: O filtro de público MUST poder ser combinado pelo critério “E” com busca por texto, unidade, categoria, bairro, data e intervalo de datas, sem alterar a validação nem o comportamento desses filtros, nem das combinações que já são recusadas.
- **FR-009**: Sem o filtro de público, o resultado, a ordenação por próxima ocorrência, a paginação e todos os campos já existentes MUST permanecer idênticos aos de antes da feature.
- **FR-010**: O sistema MUST oferecer um recurso público de leitura que lista os públicos-alvo, paginado no mesmo formato de unidades e categorias, ordenado por nome, sem autenticação, listando somente os públicos ativos.
- **FR-011**: Cada item do recurso de públicos-alvo MUST trazer identificador, nome, identificador textual e descrição (ausente quando vazia), e MUST NOT expor dados administrativos nem a marca de “abrange todos” nem a situação ativa/inativa.
- **FR-012**: O recurso de públicos-alvo MUST recusar métodos de escrita com o erro padrão de método não permitido, como os demais recursos públicos.
- **FR-013**: Cada item da listagem pública de atividades MUST trazer seus públicos-alvo (identificador e nome), ordenados por nome, e uma lista vazia quando a atividade não tiver nenhum; o campo MUST ser sempre presente.
- **FR-014**: Incluir os públicos-alvo na listagem MUST NOT aumentar a quantidade de acessos ao banco proporcionalmente ao número de atividades; o texto livre sobre o público MUST continuar somente no detalhe.
- **FR-015**: O catálogo de públicos-alvo MUST ter uma marca “abrange todos”, desligada por padrão, editável no Django Admin com rótulo claro em português, e que seja o único critério usado pela regra inclusiva (o nome ou o identificador textual da opção MUST NOT ser usado).
- **FR-016**: A mudança no catálogo MUST ser aditiva: públicos-alvo existentes continuam válidos, com a marca desligada, sem perda de dados nem alteração das associações com atividades.
- **FR-017**: O comando de carga inicial do catálogo MUST marcar a opção “Todas as idades” como “abrange todos”, MUST ser seguro para repetir (sem duplicar registros) e MUST aplicar a marca também em um catálogo que já existia sem ela, sem desmarcar outros públicos que o administrador tenha marcado.
- **FR-018**: A lista de atividades do Django Admin MUST oferecer o filtro por público-alvo, com as opções ativas e as inativas que ainda tenham atividades vinculadas, mostrando cada atividade uma única vez, sem alterar permissões nem ações em lote existentes.
- **FR-019**: Nenhuma resposta pública MUST expor dados de auditoria, de contas ou informações pessoais por causa desta feature.
- **FR-020**: Os testes automatizados MUST continuar unitários, sem acesso a banco, com cobertura total mínima de 90%.
- **FR-021**: A documentação MUST ser atualizada para refletir a feature: modelo de dados (DOC-03), especificação da API (DOC-05), o contrato da API pública de consulta e o README; o DOC-04 já registra o EP-11 e a constituição já cita o público-alvo entre os filtros.

### Key Entities *(include if feature involves data)*

- **Público-alvo (existente, ampliado)**: opção padronizada de público (por exemplo, Crianças, Adultos, Todas as idades), com nome, identificador textual, descrição opcional e situação ativo/inativo. Ganha uma marca “abrange todos”, desligada por padrão, que identifica a(s) opção(ões) que valem para qualquer público.
- **Atividade (existente)**: já se associa a um ou mais públicos-alvo; passa a poder ser filtrada por eles e a exibi-los na listagem. Nenhum campo novo.
- **Associação atividade–público (existente)**: liga a atividade a cada público; a mesma opção não se repete na mesma atividade. Não muda.
- **Filtro de público**: parâmetro opcional da consulta pública, com um único identificador, combinável com os demais filtros.
- **Lista de públicos-alvo (recurso público)**: coleção paginada, somente leitura, dos públicos ativos, usada pelo frontend para montar o seletor.
- **Item da listagem (existente, ampliado)**: ganha a lista de públicos-alvo da atividade (identificador e nome).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos casos de teste da regra inclusiva, o resultado do filtro por um público específico contém exatamente as atividades publicadas desse público mais as de “Todas as idades”, e o filtro por “Todas as idades” contém exatamente as marcadas com ela.
- **SC-002**: Nenhuma atividade aparece duas vezes no resultado em nenhuma combinação de públicos testada, e a contagem total e a paginação batem com as atividades distintas.
- **SC-003**: 100% dos identificadores malformados são recusados com mensagem clara no campo do público, e 100% dos identificadores inexistentes ou inativos devolvem lista vazia, sem erro.
- **SC-004**: Nenhuma resposta pública, com ou sem filtro, contém atividade em rascunho, cancelada ou encerrada.
- **SC-005**: Sem o filtro, as respostas de listagem e detalhe permanecem iguais às anteriores, exceto pela inclusão da lista de públicos em cada item da listagem; nenhum campo existente muda.
- **SC-006**: A pessoa desenvolvedora do frontend consegue montar o seletor e aplicar o filtro usando apenas o recurso de públicos e o parâmetro de filtro, sem consultar outra fonte.
- **SC-007**: O número de acessos ao banco para montar a listagem é o mesmo para 5 e para 50 atividades.
- **SC-008**: Todas as combinações do filtro de público com os demais filtros testadas devolvem somente atividades que atendem a todos, e as combinações inválidas existentes continuam sendo recusadas como antes.
- **SC-009**: Um administrador marca ou desmarca a opção “abrange todos” em menos de 30 segundos, sem consultar documentação, e o comportamento do filtro acompanha a marca imediatamente.
- **SC-010**: Rodar a carga inicial duas vezes em um banco já povoado não cria registros novos e deixa “Todas as idades” marcada.
- **SC-011**: A suíte de testes continua passando com cobertura total mínima de 90%, sem acessar banco de dados.

## Assumptions

- A regra inclusiva de “Todas as idades” e a identificação por uma marca própria do catálogo já foram decididas (DOC-10, pendências 1 e 8, em 2026-10-12); esta spec as trata como restrições.
- O filtro aceita **um único** público por consulta, como os filtros de unidade e categoria; vários valores, união e interseção ficam fora do escopo.
- O parâmetro tem o nome `audience`, mantendo o padrão em inglês dos demais (`unit`, `category`).
- A marca “abrange todos” é aplicada a quem estiver marcado, ativo ou não: desativar um público preserva os vínculos existentes (DOC-03) e o que decide a regra é a marca. Para filtrar, porém, só públicos ativos podem ser escolhidos; um público inativo devolve lista vazia.
- Não se impede marcar mais de um público como “abrange todos”; todos são tratados da mesma forma.
- A listagem pública de públicos-alvo não expõe a marca nem a situação: o frontend não precisa saber qual é “Todas as idades” para filtrar, pois a regra é aplicada no servidor.
- O recurso de públicos-alvo segue o padrão dos recursos de apoio existentes (paginação e ordenação por nome), e o tamanho de página usa o mesmo padrão e o mesmo limite.
- O campo de públicos na listagem usa o mesmo formato do detalhe (identificador e nome) e a mesma ordenação por nome.
- O trabalho do frontend (seletor do filtro, exibição do público no card, tratamento de lista vazia e de erro, US-050) fica fora desta feature; o backend entrega o contrato que ele consome.
- Fora do escopo: filtrar por vários públicos ao mesmo tempo, criar ou editar públicos-alvo pela API, buscar no texto livre do público (já coberto pela busca por texto), ordenar por público, contagem de atividades por público e alterar a lista de públicos cadastrada.
- Os testes seguem a constituição: unitários, com dublês para o ORM e o relógio, sem acesso a banco.
- A constituição (Princípio IV) e o DOC-04 já foram atualizados para citar o público-alvo entre os filtros da API (constituição v1.2.0, em 2026-10-12).
