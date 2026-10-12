# Feature Specification: Imagens das Atividades

**Feature Branch**: `010-activity-images`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "Adicionar imagens às atividades conforme o épico EP-10 descrito em docs/09-adicao-de-imagens.md (US-037 a US-044): armazenamento das imagens no Amazon S3 (bucket agenda-livre-imagens, sa-east-1, leitura pública com nomes de objeto aleatórios), upload pelo Django Admin com validação (JPEG/PNG/WebP, até 5 MB, 400x300 a 6000x6000 px, tratamento para lado maior de 1600 px sem EXIF), texto alternativo ou marcação de imagem decorativa, campo "image" aninhado ({url, alt, decorative} ou null) em GET /activities/ e GET /activities/{id}/, campos image/image_alt/image_decorative em Activity, e imagens fictícias no comando seed_demo. Resolve o item de imagens em docs/PENDENCIAS-BACKEND.md."

## User Scenarios & Testing *(mandatory)*

As features 001 a 009 entregaram a fundação, a administração, os cadastros, as atividades, as programações, a consulta pública, os requisitos transversais, os ambientes e as páginas informativas. A feature 004 excluiu as imagens de propósito ("imagens não fazem parte desta versão"), e o frontend (DOC-12/DOC-13) já prevê imagem no card e na página de detalhes, usando hoje o fallback visual como caso normal. Esta feature implementa o **EP-10 — Imagens das atividades** (`docs/09-adicao-de-imagens.md`, US-037 a US-044) e resolve o item correspondente de `docs/PENDENCIAS-BACKEND.md`.

Os atores são **o administrador** (que envia e mantém as imagens), **a pessoa visitante** (que vê as imagens, por meio do frontend), **a pessoa desenvolvedora do frontend** (que consome o campo novo da API) e **a pessoa que apresenta o projeto** (que usa os dados de demonstração).

### User Story 1 - Administrador anexa uma imagem à atividade (Priority: P1)

Um administrador, ao cadastrar ou editar uma atividade na área administrativa, envia uma imagem que a ilustra, informa o texto alternativo (ou marca a imagem como decorativa) e vê uma pré-visualização antes de salvar. A imagem é opcional.

**Why this priority**: sem a possibilidade de anexar imagens não há o que expor nem exibir; é a base de toda a feature e o menor recorte que já entrega valor ao conteúdo.

**Independent Test**: na área administrativa, editar uma atividade, enviar uma imagem válida com texto alternativo, salvar e reabrir a atividade; confirmar que a imagem aparece na pré-visualização. Salvar outra atividade sem imagem e confirmar que continua válida e publicável.

**Acceptance Scenarios**:

1. **Dado** um administrador com permissão de editar atividades, **Quando** ele envia uma imagem válida e informa o texto alternativo, **Então** a atividade é salva com a imagem e a pré-visualização é exibida ao reabri-la.
2. **Dado** uma atividade sem imagem, **Quando** ela é salva ou publicada, **Então** a operação é bem-sucedida, pois a imagem é opcional.
3. **Dado** uma atividade com imagem, **Quando** o administrador troca ou remove a imagem, **Então** a atividade passa a refletir a mudança e os campos de auditoria (usuário e data/hora da última atualização) são atualizados.
4. **Dado** uma pessoa sem permissão de editar atividades, **Quando** ela tenta enviar, trocar ou remover uma imagem, **Então** a operação é negada.
5. **Dado** uma atividade existente, **Quando** uma imagem é enviada, **Então** o identificador da atividade permanece o mesmo.

---

### User Story 2 - Somente imagens válidas e acessíveis são aceitas (Priority: P1)

O sistema recusa arquivos que não sejam imagens permitidas ou que excedam os limites, trata a imagem antes de guardá-la (redução de tamanho e remoção de metadados) e exige o texto alternativo ou a marcação de imagem decorativa, para proteger a segurança, o desempenho e a acessibilidade.

**Why this priority**: aceitar qualquer arquivo seria um risco de segurança, e imagens sem alternativa textual violariam o requisito de acessibilidade da constituição; essas regras precisam valer desde o primeiro envio.

**Independent Test**: tentar enviar arquivos de tipo não permitido, corrompidos, grandes demais, pequenos demais e uma imagem válida com metadados de localização; confirmar que apenas a última é aceita e que a versão guardada não contém os metadados.

**Acceptance Scenarios**:

1. **Dado** um arquivo que não é JPEG, PNG nem WebP (inclusive um arquivo com extensão de imagem mas conteúdo de outro tipo), **Quando** o administrador tenta enviá-lo, **Então** o envio é rejeitado com mensagem clara em português.
2. **Dado** uma imagem com mais de 5 MB, ou com dimensões menores que 400×300 px ou maiores que 6000×6000 px, **Quando** ela é enviada, **Então** o envio é rejeitado com mensagem clara indicando o limite excedido.
3. **Dado** um arquivo corrompido, **Quando** ele é enviado, **Então** o envio é rejeitado com mensagem clara, sem erro interno.
4. **Dado** uma imagem válida cujo lado maior excede 1600 px, **Quando** ela é salva, **Então** a versão guardada tem o lado maior reduzido a 1600 px, mantendo a proporção.
5. **Dado** uma imagem com metadados (por exemplo, localização), **Quando** ela é salva, **Então** a versão guardada e disponibilizada ao público não contém esses metadados.
6. **Dado** uma imagem enviada, **Quando** o administrador não informa texto alternativo e não a marca como decorativa, **Então** o envio é rejeitado pedindo uma das duas informações.
7. **Dado** o texto alternativo preenchido, **Quando** a imagem também é marcada como decorativa, **Então** o envio é rejeitado, pois os dois não podem coexistir.
8. **Dado** um nome de arquivo qualquer (inclusive com caracteres especiais ou trechos de caminho), **Quando** a imagem é guardada, **Então** o nome original não é usado na identificação do arquivo guardado.

---

### User Story 3 - Visitante recebe os dados da imagem na consulta pública (Priority: P1)

A pessoa desenvolvedora do frontend recebe, nas respostas públicas de listagem e de detalhe das atividades, um campo `image` com o endereço da imagem, o texto alternativo e a indicação de imagem decorativa, ou `null` quando a atividade não tem imagem, para exibir a imagem no card e na página de detalhes.

**Why this priority**: é o ponto em que o valor chega à pessoa visitante; sem isso a imagem fica restrita à área administrativa.

**Independent Test**: consultar a listagem e o detalhe de uma atividade publicada com imagem e de outra sem imagem; confirmar o formato do campo `image` nos dois casos e que atividades não publicadas continuam ausentes.

**Acceptance Scenarios**:

1. **Dado** uma atividade publicada com imagem, **Quando** a listagem ou o detalhe é consultado, **Então** a resposta traz `image` com endereço absoluto da imagem, texto alternativo e indicador de imagem decorativa.
2. **Dado** uma atividade publicada sem imagem, **Quando** a listagem ou o detalhe é consultado, **Então** `image` vem como `null`, sem erro.
3. **Dado** uma imagem marcada como decorativa, **Quando** consultada, **Então** o indicador de decorativa vem verdadeiro e o texto alternativo vem vazio.
4. **Dado** uma atividade em rascunho, cancelada ou encerrada, **Quando** a consulta pública é feita, **Então** nenhuma resposta pública devolve o endereço da imagem dessa atividade.
5. **Dado** qualquer resposta pública, **Quando** inspecionada, **Então** não contém caminho interno de armazenamento, nome original do arquivo nem dados administrativos.
6. **Dado** os campos já existentes das respostas, **Quando** o campo `image` é adicionado, **Então** nenhum campo anterior muda de nome, tipo ou significado.

---

### User Story 4 - A imagem carrega de forma confiável para qualquer visitante (Priority: P2)

A pessoa visitante abre o endereço da imagem recebido da API, sem fazer login, e a imagem é entregue corretamente. Endereços de imagens não são previsíveis nem listáveis.

**Why this priority**: sem a entrega correta a imagem não aparece, mas a regra depende das histórias anteriores para ter o que entregar.

**Independent Test**: abrir, em janela anônima, o endereço de uma imagem devolvido pela API e confirmar que ela carrega; tentar listar o conteúdo do armazenamento e confirmar que é negado.

**Acceptance Scenarios**:

1. **Dado** o endereço de imagem de uma atividade publicada, **Quando** aberto sem autenticação, **Então** a imagem é entregue com o tipo de conteúdo correto.
2. **Dado** o armazenamento das imagens, **Quando** alguém tenta listar seus arquivos, **Então** a listagem é negada.
3. **Dado** duas imagens enviadas, **Quando** seus endereços são comparados, **Então** não seguem padrão previsível e não têm relação com título, identificador da atividade ou nome original do arquivo.
4. **Dado** que uma atividade deixou de estar publicada, **Quando** alguém que já conhecia o endereço da imagem o acessa, **Então** a imagem ainda pode ser entregue; este é um risco aceito e documentado, mitigado pela remoção do arquivo quando a imagem é trocada, removida ou a atividade é excluída.

---

### User Story 5 - Arquivos não ficam órfãos (Priority: P2)

Quando uma imagem é trocada, removida ou a atividade é excluída, o arquivo anterior deixa de ocupar o armazenamento e deixa de ser acessível, evitando acúmulo de arquivos sem uso e reduzindo a exposição de imagens antigas.

**Why this priority**: é higiene e custo, e reduz o risco aceito na história anterior; não bloqueia o uso básico.

**Independent Test**: enviar uma imagem, trocá-la por outra, remover a segunda e excluir a atividade; confirmar, em cada passo, que o arquivo substituído ou removido deixa de existir no armazenamento.

**Acceptance Scenarios**:

1. **Dado** uma atividade com imagem, **Quando** o administrador a substitui por outra, **Então** o arquivo anterior é removido do armazenamento.
2. **Dado** uma atividade com imagem, **Quando** o administrador a remove, **Então** o arquivo é removido do armazenamento.
3. **Dado** uma atividade com imagem, **Quando** a atividade é excluída, **Então** o arquivo da imagem é removido do armazenamento.
4. **Dado** que a remoção do arquivo anterior falhe por indisponibilidade do armazenamento, **Quando** a troca é concluída, **Então** a atividade é salva com a nova imagem, o administrador não vê erro interno e a falha é registrada no log local.

---

### User Story 6 - Dados de demonstração incluem imagens (Priority: P3)

A pessoa que apresenta o projeto executa o comando de carga de dados de demonstração (`seed_demo`) e obtém atividades com imagens fictícias, algumas delas sem imagem, para mostrar a plataforma completa e o fallback visual do frontend.

**Why this priority**: melhora a demonstração, mas não é necessário para o funcionamento do sistema.

**Independent Test**: executar o comando duas vezes em um ambiente de demonstração e verificar que parte das atividades tem imagem com texto alternativo ou marcação de decorativa, que outras ficam sem imagem e que a segunda execução não duplica arquivos nem registros.

**Acceptance Scenarios**:

1. **Dado** o comando de demonstração, **Quando** executado, **Então** parte das atividades recebe uma imagem fictícia e outras permanecem sem imagem.
2. **Dado** as imagens de demonstração, **Quando** inspecionadas, **Então** cada uma tem texto alternativo ou está marcada como decorativa, e nenhuma contém pessoas reais identificáveis nem marcas de terceiros.
3. **Dado** que o comando já foi executado, **Quando** é executado novamente, **Então** não duplica arquivos nem registros.

---

### Edge Cases

- Arquivo vazio, truncado ou com a extensão trocada (por exemplo, um executável chamado `foto.jpg`): rejeitado pela verificação do conteúdo, sem erro interno.
- Imagem exatamente nos limites (5 MB, 400×300 px, 6000×6000 px): aceita; um byte ou pixel além do limite: rejeitada.
- Imagem com lado maior exatamente em 1600 px ou menor: guardada sem ampliação.
- Imagem PNG com transparência: preservada de forma que continue exibível.
- Imagem JPEG com orientação definida por metadados: a versão tratada mantém a orientação visual correta ao remover os metadados.
- Texto alternativo apenas com espaços: tratado como vazio.
- Texto alternativo acima do tamanho máximo: rejeitado com mensagem clara.
- Nome de arquivo com caracteres especiais, muito longo ou com tentativa de percurso de diretório: não afeta a identificação do arquivo guardado.
- Armazenamento indisponível no momento do envio: a operação falha com mensagem clara ao administrador, sem salvar a atividade com referência a um arquivo inexistente e sem expor detalhes internos.
- Armazenamento indisponível na consulta pública: a listagem e o detalhe continuam respondendo normalmente, pois a API entrega apenas o endereço da imagem, sem acessar o arquivo.
- Atividade com imagem que é cancelada ou volta a rascunho: a API deixa de devolver o endereço da imagem.
- Atividade existente criada antes desta feature: continua válida, com `image` igual a `null`.
- Duas atividades enviando a mesma imagem: cada envio gera um arquivo guardado com identificação própria.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir associar no máximo uma imagem a cada atividade; a imagem é opcional, e atividades sem imagem permanecem válidas e publicáveis.
- **FR-002**: O sistema MUST permitir que administradores com permissão de editar atividades enviem, troquem e removam a imagem pela área administrativa, com pré-visualização, e MUST negar essas operações a quem não tem a permissão.
- **FR-003**: O sistema MUST aceitar somente imagens JPEG, PNG e WebP, verificando o conteúdo do arquivo e não apenas a extensão ou o tipo informado.
- **FR-004**: O sistema MUST rejeitar arquivos com mais de 5 MB e imagens com dimensões menores que 400×300 px ou maiores que 6000×6000 px, e MUST rejeitar arquivos corrompidos, sempre com mensagem clara em português e sem erro interno.
- **FR-005**: O sistema MUST tratar a imagem antes de guardá-la: reduzir o lado maior a 1600 px quando exceder esse valor (sem ampliar imagens menores e mantendo a proporção), recodificá-la e remover todos os metadados, preservando a orientação visual.
- **FR-006**: O sistema MUST exigir, para toda atividade com imagem, o texto alternativo ou a marcação de imagem decorativa; MUST rejeitar a combinação dos dois e a ausência de ambos; MUST limitar o tamanho do texto alternativo; e MUST tratar texto alternativo só com espaços como vazio.
- **FR-007**: Quando a atividade não tem imagem, o texto alternativo e a marcação de decorativa MUST permanecer vazios e não ser exigidos.
- **FR-008**: O sistema MUST guardar cada imagem sob uma identificação aleatória e não previsível, sem relação com o título, o identificador da atividade ou o nome original do arquivo, e MUST NOT usar o nome original do arquivo em nenhuma parte da identificação.
- **FR-009**: As imagens MUST ser guardadas em armazenamento de arquivos em nuvem configurável por ambiente, e o banco de dados MUST guardar somente a referência à imagem, nunca o arquivo.
- **FR-010**: As imagens MUST ser legíveis publicamente, sem autenticação, pelo endereço recebido da API; o armazenamento MUST NOT permitir a listagem de seus arquivos; e a escrita MUST ser restrita à aplicação, com permissão limitada ao armazenamento do projeto.
- **FR-011**: As respostas de listagem e de detalhe da API pública MUST incluir o campo `image` com endereço absoluto, texto alternativo e indicação de imagem decorativa, ou `null` quando a atividade não tem imagem; os campos já existentes MUST NOT mudar.
- **FR-012**: A API pública MUST NOT devolver o endereço da imagem de atividades que não estejam publicadas e MUST NOT expor caminho interno de armazenamento, nome original do arquivo ou dados administrativos.
- **FR-013**: Quando uma imagem for trocada ou removida, ou quando a atividade for excluída, o sistema MUST remover do armazenamento o arquivo que deixou de ser usado; se a remoção falhar, a operação principal MUST ser concluída e a falha MUST ser registrada no log local, sem expor dados sensíveis.
- **FR-014**: Trocar ou remover a imagem MUST atualizar os campos de auditoria da atividade (usuário e data/hora da última atualização), e o identificador da atividade MUST permanecer o mesmo.
- **FR-015**: O armazenamento MUST NOT ser acessado pelos testes automatizados: eles MUST usar um dublê no lugar do armazenamento em nuvem, mantendo a suíte sem acesso a banco e com cobertura mínima de 90%.
- **FR-016**: Nome do armazenamento, região e credenciais MUST vir de variáveis de ambiente, sem segredos versionados; o arquivo de exemplo de variáveis MUST documentá-las sem valores reais, e nenhum segredo MUST ser gravado nos logs.
- **FR-017**: O comando de carga de dados de demonstração MUST associar imagens fictícias (com texto alternativo ou marcação de decorativa, sem pessoas reais identificáveis nem marcas de terceiros) a parte das atividades, deixar outras sem imagem, e MUST ser reexecutável sem duplicar arquivos nem registros.
- **FR-018**: A documentação MUST ser atualizada para refletir a feature: modelo de dados (DOC-03), backlog (DOC-04), especificação da API (DOC-05), infraestrutura (DOC-08), o contrato da API pública e o README (variáveis de ambiente e dependências novas); o item de imagens em `docs/PENDENCIAS-BACKEND.md` MUST ser marcado como resolvido ao final.

### Key Entities *(include if feature involves data)*

- **Atividade (existente, ampliada)**: ganha a imagem opcional e seus dois complementos de acessibilidade, o texto alternativo e a marcação de decorativa. Mantém identificador, status e auditoria.
- **Imagem da atividade**: arquivo tratado (JPEG, PNG ou WebP, lado maior de até 1600 px, sem metadados) guardado em armazenamento em nuvem sob identificação aleatória; no banco existe apenas a referência. Tem no máximo uma por atividade.
- **Dados de acessibilidade da imagem**: texto alternativo (com limite de tamanho) ou indicação de imagem decorativa, mutuamente exclusivos, obrigatórios quando existe imagem.
- **Campo `image` da API pública**: objeto com endereço absoluto, texto alternativo e indicação de decorativa, ou `null`; presente nas respostas de listagem e de detalhe.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um administrador consegue anexar uma imagem válida a uma atividade, com texto alternativo, e salvar em menos de 1 minuto, sem consultar documentação.
- **SC-002**: 100% dos arquivos de tipo não permitido, corrompidos ou fora dos limites de tamanho e dimensão são rejeitados com mensagem clara, e nenhuma rejeição resulta em erro interno.
- **SC-003**: 100% das imagens disponibilizadas ao público não contêm metadados (por exemplo, localização) e têm lado maior de, no máximo, 1600 px.
- **SC-004**: 100% das imagens guardadas têm texto alternativo ou estão marcadas como decorativas; nenhuma imagem sem uma das duas informações é aceita.
- **SC-005**: Em 100% das respostas públicas de listagem e detalhe, o campo `image` está presente e tem o formato definido (objeto ou `null`), e nenhum campo existente é alterado.
- **SC-006**: Nenhuma resposta pública devolve o endereço de imagem de atividade não publicada, e nenhuma resposta expõe caminho interno, nome original do arquivo ou dados administrativos.
- **SC-007**: A pessoa desenvolvedora do frontend consegue exibir a imagem no card e no detalhe usando somente o campo `image`, sem consultar outra fonte.
- **SC-008**: Em todos os cenários de troca, remoção e exclusão testados, nenhum arquivo substituído ou removido permanece no armazenamento.
- **SC-009**: Após executar o comando de demonstração, parte das atividades tem imagem e outras não, e uma segunda execução não altera a quantidade de arquivos nem de registros.
- **SC-010**: A suíte de testes continua passando com cobertura total mínima de 90%, sem acessar o armazenamento em nuvem nem banco de dados.

## Assumptions

- A decisão de usar armazenamento em nuvem (Amazon S3, bucket `agenda-livre-imagens`, região `sa-east-1`, leitura pública dos objetos sem listagem, nomes aleatórios) já foi tomada e está registrada no DOC-09; esta spec a trata como restrição, e os detalhes de configuração ficam para o plano.
- A imagem fica diretamente na atividade (uma por atividade); galeria e várias imagens estão fora do escopo.
- Não há miniaturas na versão 1: o backend guarda uma única versão tratada, com lado maior de até 1600 px. Miniaturas separadas ficam como melhoria futura (P2).
- Somente administradores enviam imagens; pessoas visitantes não enviam.
- O limite do texto alternativo é de 200 caracteres, valor usual para descrições curtas de imagem; pode ser ajustado no plano.
- Não há texto alternativo padrão sugerido: o administrador sempre escreve o texto ou marca a imagem como decorativa.
- A política de arquivos órfãos é remover o arquivo no momento da troca, da remoção ou da exclusão da atividade, sem rotina agendada de varredura; arquivos já órfãos por falhas de remoção podem ser removidos manualmente.
- Risco aceito: por o armazenamento ser de leitura pública, quem já conhece o endereço de uma imagem continua a acessá-la enquanto o arquivo existir, mesmo que a atividade deixe de estar publicada. A mitigação é o endereço não previsível, a ausência de listagem e a remoção do arquivo quando ele deixa de ser usado.
- A exibição da imagem, o fallback visual e a atualização dos DOC-12/DOC-13 (US-043) são trabalho do frontend, em repositório separado, e estão fora desta feature; esta feature entrega o contrato que ele consome.
- Fora do escopo: edição interativa de imagem no servidor, imagens para unidades, categorias ou páginas informativas, moderação automática de conteúdo, CDN, backup dos arquivos e hospedagem em produção.
- Os testes seguem a constituição: unitários, com dublês para o armazenamento em nuvem e para o ORM, sem acesso a banco.
- O custo e a região da conta de nuvem são acompanhados pela equipe fora do código; as regras de CORS do bucket são definidas no plano, caso o frontend precise buscar as imagens por script.
- Atividades existentes antes da feature permanecem sem imagem (`image` igual a `null`) e não exigem migração de dados.
