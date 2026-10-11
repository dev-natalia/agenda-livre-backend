# Feature Specification: Consulta Pública de Atividades

**Feature Branch**: `006-public-consultation`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "feature 006, dentro de docs/04-*" (EP-06 — Consulta pública: US-019 Listar atividades publicadas, US-020 Consultar detalhes de uma atividade, US-021 Buscar por palavra-chave, US-022 Filtrar por unidade, US-023 Filtrar por categoria, US-024 Filtrar por data, US-025 Combinar filtros, US-026 Abrir link externo; inclui o requisito transversal US-027, consulta sem autenticação)

## User Scenarios & Testing *(mandatory)*

Os usuários desta feature são as **pessoas visitantes** do Agenda Livre: moradores e frequentadores dos CEUs que querem descobrir o que acontece, quando e onde. Elas não criam conta nem fazem login. As features anteriores entregaram o conteúdo (unidades, categorias, atividades, programações e o cálculo das próximas ocorrências); esta feature o torna **consultável publicamente**, de forma somente leitura. O site (frontend) é um repositório separado e consome estas consultas; Sobre e Contato não fazem parte desta feature.

### User Story 1 - Listar atividades publicadas (Priority: P1)

Uma pessoa visitante abre o site e vê a lista das atividades publicadas, com as informações resumidas de cada uma e a próxima data em que acontece, sem precisar entrar em nenhuma conta.

**Why this priority**: é a porta de entrada do produto; sem a listagem pública, nada do que a administração cadastrou chega à comunidade.

**Independent Test**: com atividades em rascunho, publicadas, canceladas e encerradas, consultar a listagem sem autenticação e verificar que só as publicadas aparecem, com dados resumidos, próxima ocorrência e sem nenhum dado administrativo.

**Acceptance Scenarios**:

1. **Dado** atividades publicadas, **Quando** uma pessoa sem login consulta a listagem, **Então** recebe as atividades publicadas, sem exigir autenticação.
2. **Dado** atividades em rascunho, canceladas ou encerradas, **Quando** a listagem é consultada, **Então** nenhuma delas aparece.
3. **Dado** uma atividade publicada na listagem, **Quando** o resultado é exibido, **Então** traz título, resumo, unidade (nome e bairro), categoria e a próxima ocorrência (data e horários), quando houver.
4. **Dado** a resposta da listagem, **Quando** ela é examinada, **Então** não contém dados administrativos (criador, atualizador, datas de auditoria, contas de usuário) nem informações pessoais.
5. **Dado** atividades publicadas com próximas ocorrências em datas diferentes, **Quando** a listagem é consultada sem filtros, **Então** vêm primeiro as que acontecem mais cedo.
6. **Dado** uma atividade publicada sem nenhuma ocorrência futura (sem programação ou só com datas passadas), **Quando** a listagem é consultada sem filtro de data, **Então** ela aparece depois das que têm próxima ocorrência, em ordem alfabética por título.
7. **Dado** muitas atividades publicadas, **Quando** a listagem é consultada, **Então** o resultado vem dividido em páginas, com a informação do total e de como chegar à página seguinte e à anterior.
8. **Dado** que não há nenhuma atividade publicada, **Quando** a listagem é consultada, **Então** o resultado é uma lista vazia, sem erro.

---

### User Story 2 - Consultar detalhes de uma atividade (Priority: P1)

A pessoa visitante abre uma atividade da lista e vê tudo o que precisa saber: o que é, para quem, onde, quando e, se houver, onde fazer a inscrição.

**Why this priority**: é o conteúdo que responde à dúvida principal da visitante ("quando e onde acontece?") e completa o fluxo mínimo útil junto da listagem.

**Independent Test**: abrir os detalhes de uma atividade publicada com programações pontual e recorrente, públicos-alvo e link externo, e verificar o conteúdo; abrir uma atividade em rascunho e uma inexistente e verificar a mesma resposta de "não encontrada".

**Acceptance Scenarios**:

1. **Dado** uma atividade publicada, **Quando** a pessoa abre seus detalhes, **Então** vê título, descrição completa, resumo, unidade (nome, endereço e bairro), categoria, públicos-alvo, observação sobre o público e as programações.
2. **Dado** uma atividade com programação pontual e recorrente, **Quando** os detalhes são exibidos, **Então** cada programação mostra seu tipo, período, horários e, se recorrente, os dias da semana por extenso.
3. **Dado** uma atividade com próximas ocorrências, **Quando** os detalhes são exibidos, **Então** aparece uma lista limitada das próximas datas e horários, em ordem cronológica, sem datas passadas.
4. **Dado** uma atividade em rascunho, cancelada ou encerrada, ou um identificador inexistente ou malformado, **Quando** a pessoa tenta abri-la, **Então** recebe a mesma resposta de "não encontrada", sem revelar que o registro existe.
5. **Dado** os detalhes de uma atividade, **Quando** examinados, **Então** não contêm dados de auditoria nem de contas administrativas.
6. **Dado** uma atividade publicada sem programações ou sem datas futuras, **Quando** os detalhes são abertos, **Então** são exibidos normalmente, com a lista de próximas ocorrências vazia.

---

### User Story 3 - Apoios de consulta: unidades e categorias (Priority: P1)

A pessoa visitante (por meio do site) vê as unidades e as categorias disponíveis para escolher nos filtros.

**Why this priority**: os filtros por unidade e categoria só são utilizáveis se a interface souber quais opções existem; sem isso, a busca refinada não é possível.

**Independent Test**: com unidades e categorias ativas e inativas, consultar as duas listas sem autenticação e verificar que só as ativas aparecem, em ordem alfabética, sem dados administrativos.

**Acceptance Scenarios**:

1. **Dado** unidades ativas e inativas, **Quando** a lista de unidades é consultada, **Então** só as ativas aparecem, em ordem alfabética, com nome, endereço e bairro.
2. **Dado** categorias ativas e inativas, **Quando** a lista de categorias é consultada, **Então** só as ativas aparecem, em ordem alfabética.
3. **Dado** uma unidade ou categoria desativada que ainda tem atividades publicadas, **Quando** os detalhes da atividade são abertos, **Então** a atividade continua sendo exibida normalmente, mostrando a unidade e a categoria a que pertence.
4. **Dado** as listas, **Quando** examinadas, **Então** não contêm dados administrativos.

---

### User Story 4 - Buscar por palavra-chave (Priority: P2)

A pessoa visitante digita um termo (por exemplo, "dança") e recebe as atividades publicadas relacionadas.

**Why this priority**: acelera a descoberta quando a pessoa já sabe o que procura; depende da listagem pronta.

**Independent Test**: buscar termos presentes no título, no resumo e na descrição de atividades publicadas e em rascunhos, e verificar que só as publicadas correspondentes retornam; buscar um termo sem correspondências e verificar a lista vazia.

**Acceptance Scenarios**:

1. **Dado** atividades publicadas, **Quando** a pessoa busca um termo presente no título, no resumo ou na descrição, **Então** essas atividades são retornadas.
2. **Dado** uma busca, **Quando** o termo difere do texto apenas por maiúsculas/minúsculas ou por acentos, **Então** ainda há correspondência (por exemplo, "danca" encontra "Oficina de dança").
3. **Dado** um termo que só aparece em uma atividade em rascunho, cancelada ou encerrada, **Quando** a pessoa busca, **Então** essa atividade não é retornada.
4. **Dado** um termo sem nenhuma correspondência, **Quando** a pessoa busca, **Então** o resultado é uma lista vazia e a interface pode exibir uma mensagem compreensível de "nenhum resultado".
5. **Dado** um termo vazio ou só com espaços, **Quando** a pessoa busca, **Então** o termo é ignorado e a listagem geral é retornada.
6. **Dado** um termo acima do tamanho máximo permitido, **Quando** a pessoa busca, **Então** a busca é recusada com mensagem clara.
7. **Dado** uma busca com resultados, **Quando** nenhuma ordenação extra é pedida, **Então** a ordem segue a mesma regra da listagem geral.

---

### User Story 5 - Filtrar por unidade, bairro e categoria (Priority: P2)

A pessoa visitante filtra a lista para ver só as atividades de uma unidade específica, de um bairro ou de uma categoria de interesse, e pode remover o filtro para voltar à lista geral.

**Why this priority**: refina a descoberta por lugar e por interesse, que são os dois critérios mais comuns; depende da listagem e dos apoios de consulta.

**Independent Test**: com atividades em duas unidades, bairros e categorias distintos, aplicar cada filtro isoladamente e verificar que só as atividades correspondentes (publicadas) retornam; remover o filtro e verificar a lista completa.

**Acceptance Scenarios**:

1. **Dado** atividades de unidades diferentes, **Quando** a pessoa filtra por uma unidade, **Então** só as atividades dessa unidade são retornadas.
2. **Dado** unidades em bairros diferentes, **Quando** a pessoa filtra por bairro, **Então** só as atividades de unidades daquele bairro são retornadas (comparação sem diferenciar maiúsculas/minúsculas e acentos).
3. **Dado** atividades de categorias diferentes, **Quando** a pessoa filtra por uma categoria, **Então** só as atividades dessa categoria são retornadas.
4. **Dado** qualquer filtro aplicado, **Quando** há atividades em rascunho, canceladas ou encerradas que o satisfariam, **Então** elas continuam fora do resultado.
5. **Dado** um filtro aplicado, **Quando** a pessoa o remove, **Então** volta a listagem geral.
6. **Dado** um filtro por unidade ou categoria com identificador malformado, **Quando** a consulta é feita, **Então** é recusada com mensagem clara; com identificador válido porém inexistente, o resultado é uma lista vazia.

---

### User Story 6 - Filtrar por data ou período (Priority: P2)

A pessoa visitante informa um dia (ou um intervalo) e vê as atividades que de fato acontecem nele, inclusive as recorrentes.

**Why this priority**: responde à pergunta "o que tem para fazer neste sábado?", muito frequente; depende das regras de ocorrência da feature 005.

**Independent Test**: com uma atividade pontual em 20/11, uma recorrente às terças e quintas de 01/11 a 31/12 e uma com período que não contém seu dia da semana, filtrar por dia e por intervalo e verificar que os resultados correspondem às ocorrências reais.

**Acceptance Scenarios**:

1. **Dado** uma atividade pontual em uma data, **Quando** a pessoa filtra por essa data, **Então** a atividade é retornada; para outra data, não.
2. **Dado** uma atividade recorrente (terças e quintas, de 01/11 a 31/12), **Quando** a pessoa filtra por uma terça dentro do período, **Então** a atividade é retornada; por uma quarta ou por uma terça fora do período, não.
3. **Dado** um intervalo de datas, **Quando** a pessoa filtra pelo intervalo, **Então** são retornadas as atividades com ao menos uma ocorrência dentro dele (extremos inclusive).
4. **Dado** um filtro de data aplicado, **Quando** os resultados são exibidos, **Então** cada atividade mostra a primeira ocorrência dentro do período pedido e a ordenação segue essa data.
5. **Dado** um filtro de data, **Quando** há atividades em rascunho, canceladas ou encerradas com ocorrências no período, **Então** elas continuam fora do resultado.
6. **Dado** um intervalo com data inicial posterior à final, uma data em formato inválido, ou o pedido simultâneo de "dia" e "intervalo", **Quando** a consulta é feita, **Então** é recusada com mensagem clara que diz o que corrigir.
7. **Dado** um filtro por dia no passado, **Quando** a consulta é feita, **Então** o resultado é uma lista vazia (a consulta pública só trata de ocorrências de hoje em diante).
8. **Dado** um filtro por data, **Quando** o dia é definido, **Então** vale o fuso horário configurado para a aplicação.

---

### User Story 7 - Combinar filtros e busca (Priority: P3)

A pessoa visitante combina palavra-chave, unidade, bairro, categoria e data para refinar os resultados, podendo remover filtros individualmente ou limpar todos.

**Why this priority**: refinamento adicional sobre os filtros isolados; o valor básico já existe sem ele.

**Independent Test**: aplicar busca, unidade, categoria e data ao mesmo tempo e verificar que o resultado satisfaz todos; remover um filtro por vez e verificar que o resultado se amplia corretamente.

**Acceptance Scenarios**:

1. **Dado** vários filtros aplicados ao mesmo tempo, **Quando** a consulta é feita, **Então** só aparecem atividades que atendem a todos eles.
2. **Dado** uma combinação sem correspondências, **Quando** a consulta é feita, **Então** o resultado é uma lista vazia, sem erro.
3. **Dado** uma combinação de filtros, **Quando** a pessoa remove um deles, **Então** o resultado passa a respeitar apenas os restantes; sem nenhum, volta a listagem geral.
4. **Dado** qualquer combinação de filtros, **Quando** a consulta é feita, **Então** nunca aparecem atividades não publicadas.
5. **Dado** filtros combinados com paginação, **Quando** a pessoa navega entre as páginas, **Então** o total e a ordenação permanecem consistentes com os filtros aplicados.

---

### User Story 8 - Abrir o link externo de uma atividade (Priority: P3)

Quando a atividade tem inscrição ou informações mantidas por outra organização, a pessoa visitante recebe o endereço para acessá-las, e só quando ele for válido.

**Why this priority**: complementa os detalhes para atividades com inscrição externa; o Agenda Livre não processa inscrições.

**Independent Test**: abrir os detalhes de uma atividade com link válido, de uma sem link e de uma com valor de link inválido legado e verificar que o link só é entregue no primeiro caso.

**Acceptance Scenarios**:

1. **Dado** uma atividade com link externo válido, **Quando** os detalhes são consultados, **Então** o link é entregue, indicando que leva para fora do Agenda Livre.
2. **Dado** uma atividade sem link, ou com valor que não seja um endereço web válido (`http` ou `https`), **Quando** os detalhes são consultados, **Então** nenhum link é entregue.
3. **Dado** a consulta pública, **Quando** a pessoa usa o link, **Então** o Agenda Livre não coleta nem processa nenhuma inscrição.

---

### Edge Cases

- Atividade publicada cuja unidade ou categoria foi desativada depois: continua pública (as desativações preservam vínculos), mas a unidade ou categoria inativa deixa de aparecer nas listas de apoio; filtrar por ela ainda funciona.
- Atividade publicada que foi cancelada, encerrada ou voltou a rascunho entre duas páginas de consulta: a próxima consulta já reflete a situação atual; não há garantia de consistência entre páginas consultadas em momentos diferentes.
- Atividade com programações apenas no passado: aparece na listagem geral (ao final) e nos detalhes, mas não em filtros de data.
- Ocorrência de hoje cujo horário de término já passou: não conta como ocorrência para o filtro de hoje nem como próxima ocorrência.
- Programação recorrente sem nenhum dia da semana coincidente no período: a atividade não aparece em filtro de data por causa dessa programação.
- Filtro de intervalo muito longo (por exemplo, vários anos): aceito até o limite máximo definido; acima dele, recusado com mensagem clara, para proteger o desempenho.
- Termo de busca com caracteres especiais, aspas ou tentativa de injeção: tratado como texto comum, sem efeito sobre a consulta nem erro interno.
- Página solicitada além do total (por exemplo, página 99 de 3): resposta de "não encontrada" clara, sem erro interno.
- Tamanho de página acima do limite ou inválido: o valor é limitado ao máximo permitido ou recusado com mensagem clara; nunca devolve lista ilimitada.
- Parâmetros de consulta desconhecidos: ignorados, sem erro.
- Tentativa de escrita (criar, alterar ou apagar) na área pública: recusada, mesmo com conta administradora autenticada por essa via.
- Consulta feita com credenciais inválidas ou expiradas enviadas por engano: a consulta pública continua funcionando como anônima.
- Dois resultados com a mesma data de próxima ocorrência: desempate por horário de início e depois por título, para que a ordem seja estável entre páginas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST oferecer consulta pública, somente leitura e sem autenticação, de atividades, unidades e categorias.
- **FR-002**: O sistema MUST incluir na consulta pública apenas atividades com situação "publicada"; rascunho, cancelada e encerrada MUST NOT aparecer em nenhuma listagem, busca, filtro ou detalhe.
- **FR-003**: O sistema MUST apresentar, na listagem, para cada atividade: identificador, título, resumo, unidade (nome e bairro), categoria e a próxima ocorrência (data, horário de início e de término), quando houver.
- **FR-004**: O sistema MUST paginar a listagem, informando total de resultados e a forma de acessar as páginas anterior e seguinte, com tamanho de página padrão e máximo definidos, e MUST NOT devolver listas ilimitadas.
- **FR-005**: O sistema MUST ordenar a listagem por data da próxima ocorrência (mais cedo primeiro), desempatando por horário de início e por título; atividades sem ocorrência futura vêm depois, em ordem alfabética por título. Com filtro de data, a ordenação usa a primeira ocorrência dentro do período pedido.
- **FR-006**: O sistema MUST apresentar, nos detalhes de uma atividade publicada: título, resumo, descrição, unidade (nome, endereço e bairro), categoria, públicos-alvo, observação sobre o público, link externo (quando válido), as programações (tipo, período, horários e dias da semana) e uma lista limitada das próximas ocorrências em ordem cronológica.
- **FR-007**: O sistema MUST responder com "não encontrada", de forma indistinguível, a detalhes de atividades inexistentes, com identificador malformado ou não publicadas, sem revelar a existência de registros privados.
- **FR-008**: O sistema MUST NOT expor, em nenhuma resposta pública, dados administrativos (criador, atualizador, datas de auditoria, contas de usuário, situações internas além do necessário) nem informações pessoais.
- **FR-009**: O sistema MUST listar, para uso nos filtros, apenas unidades ativas e apenas categorias ativas, em ordem alfabética por nome, sem dados administrativos; atividades publicadas ligadas a uma unidade ou categoria depois desativada MUST continuar consultáveis.
- **FR-010**: O sistema MUST permitir buscar por palavra-chave nos campos de título, resumo e descrição das atividades publicadas, sem diferenciar maiúsculas/minúsculas nem acentos.
- **FR-011**: O sistema MUST tratar termo de busca vazio ou só com espaços como ausência de busca, MUST recusar com mensagem clara termos acima do tamanho máximo definido, e MUST tratar o termo sempre como texto comum.
- **FR-012**: O sistema MUST permitir filtrar por unidade, por bairro da unidade e por categoria, e MUST recusar com mensagem clara identificadores malformados; identificadores válidos sem correspondência resultam em lista vazia.
- **FR-013**: O sistema MUST permitir filtrar por um dia ou por um intervalo de datas (extremos inclusive), considerando as ocorrências reais calculadas a partir das programações (pontuais e recorrentes, respeitando período, dias da semana e horário), no fuso horário configurado para a aplicação.
- **FR-014**: O sistema MUST recusar, com mensagem clara, filtros de data com formato inválido, intervalo com início posterior ao fim, pedido simultâneo de dia e intervalo, ou intervalo acima do limite máximo definido; e MUST considerar apenas ocorrências de hoje em diante (ocorrências já terminadas não contam).
- **FR-015**: O sistema MUST permitir combinar busca e todos os filtros, retornando apenas atividades que atendem a todos eles, e permitir que qualquer filtro seja omitido para retornar à listagem mais ampla.
- **FR-016**: O sistema MUST entregar o link externo da atividade somente quando estiver preenchido e for um endereço web válido (`http` ou `https`), e MUST NOT coletar nem processar inscrições.
- **FR-017**: O sistema MUST recusar qualquer tentativa de criar, alterar ou apagar dados pela área pública, mantendo as operações de escrita protegidas pelo acesso administrativo existente.
- **FR-018**: O sistema MUST reutilizar a regra de cálculo de ocorrências da feature 005, de modo que a próxima ocorrência, as ocorrências dos detalhes e o filtro de data concordem entre si e com o que a administração vê.
- **FR-019**: O sistema MUST responder a erros de consulta (parâmetros inválidos, página inexistente, registro não encontrado) com mensagens úteis em formato consistente, sem expor detalhes internos, caminhos, consultas ou rastros de erro.
- **FR-020**: O sistema MUST permitir que o frontend, hospedado em outra origem, faça essas consultas a partir do navegador (acesso entre origens para leitura pública).

### Key Entities

- **Atividade pública**: visão de leitura de uma atividade publicada; reúne título, resumo, descrição, unidade, categoria, públicos-alvo, observação sobre o público, link externo (quando válido) e programações. Nunca inclui dados de auditoria.
- **Unidade pública / Categoria pública**: visão de leitura de unidades e categorias ativas, usada para exibição e para as opções de filtro.
- **Programação** (feature 005): regra de quando a atividade acontece (pontual ou recorrente); exposta como regra, sem dados de autoria.
- **Ocorrência** (feature 005): data e horário concretos calculados a partir de uma programação; usada na próxima ocorrência, na lista dos detalhes e no filtro de data; não é armazenada.
- **Consulta (busca e filtros)**: conjunto de critérios opcionais — palavra-chave, unidade, bairro, categoria, dia ou intervalo, página e tamanho de página — aplicados em conjunto.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa visitante, sem criar conta nem fazer login, encontra e abre os detalhes de uma atividade em até 3 interações a partir da listagem inicial.
- **SC-002**: 100% das atividades em rascunho, canceladas ou encerradas ficam ausentes de todas as listagens, buscas, filtros e detalhes públicos, em todas as combinações de critérios testadas.
- **SC-003**: 100% das respostas públicas, nos casos de teste, não contêm nenhum dado administrativo, de auditoria ou pessoal.
- **SC-004**: Em 100% dos casos de teste de filtro de data (pontual, recorrente dentro e fora do período, dia da semana não coincidente, ocorrência de hoje já encerrada, data passada, intervalo), o resultado corresponde exatamente às ocorrências esperadas.
- **SC-005**: Em 100% dos casos de teste, a combinação de busca e filtros retorna somente atividades que satisfazem todos os critérios aplicados, e a remoção de um critério nunca reduz o resultado.
- **SC-006**: 95% das consultas de listagem, busca e filtro, com até 1.000 atividades publicadas, retornam em menos de 2 segundos para a pessoa visitante.
- **SC-007**: 100% dos parâmetros inválidos (identificador malformado, datas inválidas, termo longo demais, tamanho de página inválido) resultam em mensagem clara que indica o que corrigir, sem erro interno.
- **SC-008**: 100% das tentativas de escrita pela área pública são recusadas sem alterar dados.
- **SC-009**: O link externo é entregue em 100% dos casos com endereço web válido e em 0% dos casos com valor ausente ou inválido.
- **SC-010**: A próxima ocorrência mostrada na listagem coincide em 100% dos casos de teste com a primeira ocorrência calculada na administração da mesma atividade.

## Assumptions

- As features 001 a 005 estão concluídas; esta feature depende de Unidade, Categoria, Atividade, públicos-alvo, Programação e do cálculo de ocorrências.
- A consulta pública é somente leitura; não há contas de visitantes, favoritos, inscrições nem comentários.
- Apenas atividades "publicadas" são públicas (decisão de 2026-10-11); a elegibilidade por programação não exclui atividades publicadas sem datas futuras da listagem geral, que aparecem ao final (DOC-05 deixava essa regra em aberto; este é o padrão adotado).
- Paginação: tamanho de página padrão de 12 resultados e máximo de 50; valores acima do máximo são limitados ao máximo. Os valores podem ser ajustados no planejamento.
- Busca: tamanho máximo do termo de 100 caracteres; considera título, resumo e descrição; a lista de campos pode ser revista no contrato da API.
- Filtro de data: intervalo máximo de 366 dias; apenas ocorrências a partir de hoje, no fuso da aplicação, são consideradas (não há histórico público, conforme DOC-05).
- Detalhes: a lista de próximas ocorrências é limitada a 5 itens, além das regras das programações.
- Combinações de filtro de data: "dia" e "intervalo" são alternativas; pedir os dois juntos é recusado (DOC-05 propõe rejeitar combinações ambíguas).
- Unidades e categorias inativas deixam de ser oferecidas como opções de filtro, mas atividades publicadas já vinculadas continuam públicas (as desativações preservam vínculos, features 003 e 004).
- Categorias ativas sem atividades publicadas ainda são listadas, pois a interface pode precisar delas; o frontend pode ocultá-las.
- O contrato exato (rotas, nomes de campos, envelope de paginação) segue o DOC-05 e será fixado no planejamento; os endpoints opcionais de detalhe de unidade e de categoria só entram se o frontend precisar.
- Não há ordenação escolhida pela pessoa visitante nesta versão; a ordenação é a definida em FR-005.
- Acessibilidade, layout, mensagens exibidas ao visitante e a navegação por teclado são responsabilidade do frontend, em repositório separado; esta feature entrega respostas claras e mensagens de erro compreensíveis.
- O sistema roda apenas localmente; hospedagem, cache de borda, monitoramento e escalabilidade estão fora do escopo.
- Fora do escopo: endpoint público de histórico, páginas Sobre e Contato, imagens das atividades, exceções individuais de ocorrência e qualquer operação de escrita.
