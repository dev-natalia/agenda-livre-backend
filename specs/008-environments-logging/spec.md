# Feature Specification: Ambientes e Registro de Erros

**Feature Branch**: `008-environments-logging`

**Created**: 2026-10-11

**Status**: Implemented

**Input**: User description: "feature 008 dentro de docs/04-*" (EP-08 — Entrega e operação: US-031 Configurar ambientes e US-034 Registrar erros operacionais, em versão básica e local; US-032 Preparar implantação e US-033 Planejar backup e restauração permanecem fora do escopo; EP-09 é somente frontend)

## User Scenarios & Testing *(mandatory)*

As features 001 a 007 entregaram a fundação, a administração, os cadastros, as atividades, as programações, a consulta pública e os requisitos transversais. Esta feature **fecha o EP-08** dentro do escopo decidido em 2026-10-11 (o sistema roda apenas localmente): confirma e completa a configuração por ambiente (US-031) e acrescenta um **registro básico de erros em arquivo local** (US-034). Implantação (US-032), backup e restauração (US-033), monitoramento e hospedagem continuam fora do escopo, e as páginas Sobre e Contato (EP-09) pertencem somente ao frontend, sem trabalho no backend.

Os atores são **a pessoa desenvolvedora** (quem instala e roda o sistema) e **a pessoa responsável pela manutenção** (quem investiga falhas). Visitantes e administradores não veem mudança de comportamento.

### User Story 1 - Investigar uma falha pelos registros locais (Priority: P1)

Uma pessoa responsável pela manutenção quer consultar registros úteis quando algo falha, para descobrir o que aconteceu sem reproduzir o problema e sem que segredos fiquem expostos.

**Why this priority**: é a única parte nova do EP-08 dentro do escopo; hoje as falhas inesperadas só vão para a saída do terminal e se perdem quando ele é fechado.

**Independent Test**: provocar uma falha inesperada e uma falha de conexão com o banco e verificar que cada uma gerou um registro persistente, com tipo da falha e contexto, sem senha, chave secreta nem dados pessoais.

**Acceptance Scenarios**:

1. **Dado** uma falha inesperada durante uma requisição, **Quando** ela ocorre, **Então** fica registrado, de forma persistente, o horário, a gravidade, o tipo da falha, o método e o caminho acessados e o rastreamento técnico.
2. **Dado** que a falha tem como causa informações sensíveis (senha do banco, chave secreta, cabeçalhos de autorização, cookies, corpo de formulário de login), **Quando** o registro é gravado, **Então** nenhum desses valores aparece nele.
3. **Dado** uma falha de conexão com o banco ou variável de ambiente ausente na inicialização, **Quando** ocorre, **Então** o tipo da falha e o contexto necessário aparecem nos registros, sem mostrar valores de configuração secretos.
4. **Dado** que o visitante recebe somente uma mensagem genérica de erro (feature 007), **Quando** a pessoa de manutenção consulta os registros, **Então** encontra o detalhe técnico que não foi mostrado ao visitante.
5. **Dado** que o sistema roda por muito tempo, **Quando** o arquivo de registro cresce, **Então** ele é rotacionado com limite de tamanho e quantidade, sem ocupar o disco indefinidamente.

---

### User Story 2 - Configurar o sistema por ambiente com segurança apropriada (Priority: P1)

Uma pessoa desenvolvedora quer rodar o mesmo código em desenvolvimento e nos testes com configurações apropriadas a cada um, e ter a garantia de que valores sensíveis nunca entram no repositório.

**Why this priority**: é requisito P0 (US-031). A base já existe (feature 001); falta tornar explícito e verificável o que muda entre desenvolvimento e um ambiente mais restrito, e fechar as lacunas documentais.

**Independent Test**: instalar em uma máquina limpa seguindo apenas o README, rodar com as configurações de desenvolvimento e depois com as restritivas, e conferir que as proteções adicionais só ficam ativas no modo restritivo e que nenhum segredo está versionado.

**Acceptance Scenarios**:

1. **Dado** o repositório versionado, **Quando** é inspecionado, **Então** não contém senhas, chaves ou endpoints reais; o arquivo de exemplo traz apenas valores fictícios.
2. **Dado** a documentação, **Quando** lida, **Então** lista todas as variáveis de ambiente, inclusive as novas desta feature, com obrigatoriedade, padrão e finalidade.
3. **Dado** o modo de depuração desligado, **Quando** o sistema inicia, **Então** as proteções de transporte e de cookies adequadas a um ambiente restritivo ficam ativas, e no modo de desenvolvimento elas não impedem o uso local.
4. **Dado** o ambiente de testes, **Quando** a suíte roda, **Então** nenhum dado real é usado e nenhuma conexão com o banco é aberta.
5. **Dado** uma variável obrigatória ausente, **Quando** o sistema inicia, **Então** ele não sobe e informa os nomes das ausentes, sem mostrar valores (comportamento da feature 001 preservado).

---

### User Story 3 - Escopo de entrega e operação documentado (Priority: P3)

A equipe quer que a documentação deixe claro o que é e o que não é entregue em operação, para que a avaliação do projeto não espere implantação, backup ou monitoramento.

**Why this priority**: evita ambiguidade de escopo, mas não altera o comportamento do sistema.

**Independent Test**: ler o README e os documentos do backlog e de infraestrutura e confirmar que registram o local dos registros de erro, como consultá-los e a lista do que está fora do escopo.

**Acceptance Scenarios**:

1. **Dado** o README, **Quando** lido, **Então** explica onde ficam os registros de erro, como consultá-los e o que nunca é gravado neles.
2. **Dado** o backlog e o documento de infraestrutura, **Quando** lidos, **Então** US-032, US-033 e o monitoramento constam como fora do escopo e US-034 consta como "registro básico local".
3. **Dado** a pendência de EP-09, **Quando** consultada, **Então** consta que Sobre e Contato não têm trabalho no backend.

---

### Edge Cases

- O diretório ou arquivo de registro não pode ser criado ou gravado (permissão, disco cheio): o sistema continua atendendo requisições, e a falha de registro não derruba a aplicação nem vaza para o visitante.
- Falhas em sequência com a mesma causa: cada ocorrência gera registro, sem repetir dados sensíveis.
- Mensagem de exceção que contenha, por acaso, um valor sensível (por exemplo, uma senha dentro de um endereço de conexão): o valor é mascarado antes de ser gravado.
- Requisições comuns bem-sucedidas e erros esperados de cliente (validação, não encontrado, método não permitido): não poluem o registro de erros, que fica reservado a falhas relevantes.
- Ambiente de testes: o registro em arquivo não grava dentro do repositório nem deixa resíduos após a execução.
- Registro de ações administrativas (quem alterou o quê) já é coberto pela auditoria da feature 007 e não é duplicado aqui.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST registrar de forma persistente, em arquivo local, as falhas inesperadas da aplicação, com horário, gravidade, tipo da falha, método e caminho da requisição e rastreamento técnico.
- **FR-002**: Os registros MUST NOT conter senhas, chaves secretas, cabeçalhos de autorização, cookies, tokens ou corpos de requisição, e valores sensíveis presentes em mensagens de exceção MUST ser mascarados antes da gravação.
- **FR-003**: Falhas de inicialização e de conexão com o banco MUST ser registradas com o tipo da falha e o contexto necessário (por exemplo, nome das variáveis ausentes, host e porta), sem valores secretos.
- **FR-004**: O arquivo de registro MUST ter rotação com limite de tamanho e de quantidade de arquivos antigos, configuráveis com valores padrão razoáveis.
- **FR-005**: O local e o nível mínimo do registro MUST ser configuráveis por variável de ambiente, com padrões que funcionem sem configuração adicional e fora do controle de versão.
- **FR-006**: Erros esperados de cliente (validação, não encontrado, método não permitido, acesso negado) MUST NOT ser gravados como falhas; apenas falhas inesperadas e de infraestrutura entram no registro de erros.
- **FR-007**: Uma falha ao gravar o registro MUST NOT interromper o atendimento nem alterar a resposta enviada ao visitante, que continua genérica (feature 007).
- **FR-008**: As proteções de segurança específicas de ambiente restritivo (transporte seguro e cookies seguros) MUST ficar ativas quando o modo de depuração estiver desligado e inativas no desenvolvimento local, por configuração explícita e documentada.
- **FR-009**: O repositório MUST NOT conter segredos; o arquivo de exemplo de variáveis MUST conter apenas valores fictícios e todas as variáveis, inclusive as novas, MUST estar documentadas no README.
- **FR-010**: A suíte de testes MUST NOT usar dados reais nem abrir conexão com o banco, e MUST NOT gravar registros fora de um diretório temporário.
- **FR-011**: O README e os documentos DOC-04 e DOC-08 MUST registrar o local e o uso dos registros, que implantação (US-032), backup (US-033) e monitoramento estão fora do escopo e que EP-09 é somente frontend.
- **FR-012**: Cada requisito acima MUST ter testes automatizados unitários, sem acesso a banco, mantendo a cobertura total em pelo menos 90%.

### Key Entities *(include if feature involves data)*

- **Registro de erro**: ocorrência gravada em arquivo local com horário, gravidade, tipo da falha, contexto da requisição ou da inicialização e rastreamento técnico; nunca contém dados sensíveis. Não é armazenado no banco.
- **Configuração de ambiente**: conjunto de variáveis de ambiente que define depuração, hosts, banco, origens permitidas e, nesta feature, o local e o nível dos registros.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das falhas inesperadas simuladas, a pessoa de manutenção encontra nos registros o tipo da falha e a requisição envolvida, sem precisar reproduzir o problema.
- **SC-002**: Em 100% dos registros gerados nos testes, nenhum valor de senha, chave secreta, cookie ou autorização aparece, inclusive quando presente na mensagem original da falha.
- **SC-003**: Nenhuma resposta ao visitante muda em relação à feature 007: 100% das falhas simuladas continuam devolvendo apenas a mensagem genérica.
- **SC-004**: Com o arquivo de registro em tamanho máximo, o espaço total ocupado pelos registros nunca ultrapassa o limite configurado.
- **SC-005**: Uma pessoa desenvolvedora instala e inicia o sistema em máquina limpa usando apenas o README em até 30 minutos, e encontra a documentação de 100% das variáveis.
- **SC-006**: A verificação do repositório não encontra nenhum segredo versionado.
- **SC-007**: A suíte completa passa, sem acesso a banco, com cobertura total de no mínimo 90%.

## Assumptions

- "Feature 008" refere-se ao épico EP-08 do backlog (US-031 a US-034), a oitava feature na sequência, após 001 a 007. As histórias US-032 e US-033 seguem fora do escopo por decisão de 2026-10-11, e EP-09 (US-035 e US-036) é somente frontend.
- US-031 já foi em grande parte entregue na feature 001 (variáveis de ambiente, exemplo sem segredos, falha clara ao faltar variável, testes sem banco). Esta feature apenas completa o que faltou: a variação explícita das proteções de segurança entre desenvolvimento e ambiente restritivo e a documentação das novas variáveis.
- Como o sistema roda apenas localmente, "hospedagem" no backlog é tratada como o modo restritivo (depuração desligada), sem que isso implique implantar em lugar algum.
- O registro de erros é básico e local: arquivo com rotação, sem serviço de monitoramento, alertas, painel ou envio para terceiros. A escolha da solução de monitoramento fica para quando houver hospedagem.
- O registro de erros não substitui a auditoria de conteúdo da feature 007 e não grava dados de visitantes.
- O arquivo de registro fica em um diretório ignorado pelo controle de versão.
- Os testes são unitários, com mocks, sem banco, conforme a constituição.
