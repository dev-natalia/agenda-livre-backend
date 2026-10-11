# Feature Specification: Fundação do Backend

**Feature Branch**: `001-backend-foundation`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "Fundação do backend Agenda Livre: projeto organizado em módulos por domínio, com configurações separadas da lógica de domínio; conexão com o banco PostgreSQL no AWS RDS por variáveis de ambiente, sem segredos no repositório; estrutura de testes unitários com mocks, sem acesso a banco, e cobertura mínima de 90%; dependências com versões fixadas; verificação de estilo de código; README com instalação local, variáveis de ambiente e como rodar os testes; acesso permitido a um frontend em repositório separado. O sistema roda apenas localmente."

## User Scenarios & Testing *(mandatory)*

Nesta feature, a "pessoa desenvolvedora" é quem prepara e evolui o backend: integrantes da equipe do projeto. Não há usuário final, pois a feature entrega a base sobre a qual as demais funcionalidades serão construídas.

### User Story 1 - Rodar o projeto em uma máquina nova (Priority: P1)

Uma pessoa da equipe clona o repositório em uma máquina limpa, segue o README, instala as dependências, informa suas configurações locais e inicia o backend com sucesso.

**Why this priority**: sem um projeto que inicia de forma repetível, nenhuma outra feature pode ser desenvolvida ou demonstrada. É o requisito mínimo para a entrega local e para o vídeo de demonstração.

**Independent Test**: em uma máquina sem configuração prévia, seguir apenas o README e chegar a um backend em execução que responde a uma verificação básica de funcionamento.

**Acceptance Scenarios**:

1. **Dado** um repositório recém-clonado e o README, **Quando** a pessoa segue os passos de instalação, **Então** as dependências são instaladas nas versões fixadas e o backend inicia sem erros.
2. **Dado** que as variáveis de ambiente obrigatórias não foram informadas, **Quando** o backend é iniciado, **Então** ele falha com uma mensagem que indica quais variáveis estão faltando, sem expor valores sensíveis.
3. **Dado** o arquivo de exemplo de variáveis de ambiente, **Quando** a pessoa o copia e preenche os valores, **Então** o backend inicia usando essas configurações.
4. **Dado** a estrutura inicial do projeto, **Quando** a pessoa a examina, **Então** encontra módulos separados por domínio (unidades, categorias, atividades, programações, públicos-alvo) e as configurações isoladas da lógica de negócio.

---

### User Story 2 - Conectar ao banco de dados e aplicar a estrutura (Priority: P1)

A pessoa informa, por configuração externa, os dados de conexão do banco PostgreSQL no AWS RDS, confirma que a conexão funciona e aplica o histórico de alterações de estrutura do banco.

**Why this priority**: todas as features de dados dependem de uma conexão funcional com o banco compartilhado do projeto.

**Independent Test**: com credenciais válidas, executar a verificação de conexão e a aplicação de alterações de estrutura, e observar sucesso; com credenciais inválidas, observar uma falha clara.

**Acceptance Scenarios**:

1. **Dado** credenciais válidas do RDS nas variáveis de ambiente, **Quando** a pessoa executa a verificação de conexão, **Então** o resultado indica que o banco está acessível.
2. **Dado** credenciais inválidas ou um banco inacessível, **Quando** a verificação é executada, **Então** a mensagem de erro identifica o tipo de falha sem revelar a senha nem outros segredos.
3. **Dado** uma conexão funcional, **Quando** a pessoa aplica as alterações de estrutura, **Então** elas são aplicadas de forma controlada e a execução informa o banco de destino antes de modificá-lo.
4. **Dado** o repositório, **Quando** a pessoa o inspeciona, **Então** não encontra senhas, endereços privados do banco ou chaves reais, apenas o arquivo de exemplo com nomes de variáveis.

---

### User Story 3 - Executar testes unitários e medir a cobertura (Priority: P1)

A pessoa executa a suíte de testes por um único comando documentado, vê o resultado e a porcentagem de cobertura, e a execução falha automaticamente se a cobertura ficar abaixo de 90%.

**Why this priority**: a constituição exige cobertura mínima de 90% como pré-requisito para integrar alterações. A estrutura de testes precisa existir desde o início para que cada feature seguinte a use.

**Independent Test**: executar o comando de testes em uma máquina sem acesso ao banco e verificar que a suíte roda, informa a cobertura e sinaliza claramente falhas.

**Acceptance Scenarios**:

1. **Dado** o projeto instalado, **Quando** a pessoa executa o comando de testes, **Então** os testes rodam sem abrir nenhuma conexão com banco de dados.
2. **Dado** um teste que tente acessar o banco de dados, **Quando** a suíte é executada, **Então** ele falha com uma mensagem explícita de que o acesso ao banco é proibido nos testes.
3. **Dado** que a cobertura total está abaixo de 90%, **Quando** a verificação de cobertura é executada, **Então** ela termina com falha e informa a porcentagem atual.
4. **Dado** que a cobertura está em 90% ou mais e todos os testes passam, **Quando** a verificação é executada, **Então** ela termina com sucesso.
5. **Dado** uma falha em um teste, **Quando** a suíte termina, **Então** a falha é claramente identificada e a execução não é considerada bem-sucedida.

---

### User Story 4 - Padronizar o estilo do código (Priority: P2)

A pessoa executa uma verificação de estilo documentada e recebe a lista de trechos fora do padrão PEP 8.

**Why this priority**: a constituição exige conformidade com PEP 8, mas o projeto roda sem isso. É importante para manter a qualidade, mas não bloqueia o funcionamento.

**Independent Test**: executar a verificação de estilo em um código intencionalmente fora do padrão e observar a falha; em código conforme, observar sucesso.

**Acceptance Scenarios**:

1. **Dado** código que viola o padrão, **Quando** a verificação é executada, **Então** os problemas são listados com arquivo e linha.
2. **Dado** código conforme, **Quando** a verificação é executada, **Então** ela termina com sucesso.

---

### User Story 5 - Permitir o consumo por um frontend separado (Priority: P2)

O frontend, mantido em outro repositório e executado em outra origem local, consegue chamar o backend a partir do navegador.

**Why this priority**: o frontend é um repositório separado e o navegador bloqueia chamadas entre origens diferentes sem autorização explícita. Sem isso, nenhuma tela funcionaria na demonstração.

**Independent Test**: a partir de uma página servida em uma origem local configurada, fazer uma requisição ao backend pelo navegador e observar que ela é permitida; repetir de uma origem não configurada e observar o bloqueio.

**Acceptance Scenarios**:

1. **Dado** que a origem do frontend está configurada, **Quando** o navegador faz uma requisição ao backend a partir dela, **Então** a resposta é permitida.
2. **Dado** uma origem que não está na lista permitida, **Quando** o navegador faz uma requisição, **Então** ela não é autorizada.
3. **Dado** que a lista de origens permitidas é uma configuração, **Quando** a pessoa a altera, **Então** não é necessário modificar o código.

---

### Edge Cases

- Variáveis de ambiente ausentes, vazias ou com formato inválido (por exemplo, porta que não é número).
- Banco indisponível ou com tempo de resposta excedido durante a inicialização ou a verificação de conexão.
- Rede que bloqueia o acesso ao RDS a partir da máquina da pessoa (regras de rede da AWS).
- A pessoa executar a aplicação de alterações de estrutura apontando, sem perceber, para o banco errado.
- Cobertura exatamente em 90% (deve ser aceita) e abaixo disso (deve falhar).
- Teste que ignora os mocks e tenta acessar o banco real.
- Versão incompatível do Python na máquina da pessoa.
- Arquivo local de variáveis de ambiente acidentalmente adicionado ao controle de versão.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O projeto MUST ser iniciável localmente seguindo apenas as instruções do README, em uma máquina sem configuração prévia.
- **FR-002**: O código MUST ser organizado em módulos por domínio (unidades, categorias, atividades, programações e públicos-alvo), com a configuração isolada da lógica de negócio.
- **FR-003**: A configuração do backend MUST ser lida de variáveis de ambiente e MUST NOT conter valores sensíveis no repositório.
- **FR-004**: O repositório MUST incluir um arquivo de exemplo com todos os nomes de variáveis de ambiente necessárias, sem valores reais, e o arquivo real de configuração local MUST ficar fora do controle de versão.
- **FR-005**: O backend MUST validar as variáveis obrigatórias na inicialização e falhar com mensagem clara, sem expor valores sensíveis, quando alguma estiver ausente ou inválida.
- **FR-006**: O backend MUST conectar-se ao banco PostgreSQL no AWS RDS usando exclusivamente as variáveis de ambiente, com suporte a conexão criptografada.
- **FR-007**: Deve existir uma forma documentada de verificar a conectividade com o banco que informe sucesso ou o tipo de falha, sem revelar credenciais.
- **FR-008**: As alterações de estrutura do banco MUST ser versionadas e aplicáveis de forma controlada, e o comando MUST deixar claro qual banco será modificado.
- **FR-009**: A suíte de testes MUST ser executável por um comando único e documentado.
- **FR-010**: Os testes MUST usar mocks e MUST NOT acessar nenhum banco de dados, e qualquer tentativa de acesso ao banco em um teste MUST causar falha explícita.
- **FR-011**: A medição de cobertura MUST estar integrada à execução dos testes, e a execução MUST falhar quando a cobertura total for inferior a 90%.
- **FR-012**: As dependências MUST estar registradas com versões fixadas, de modo que a instalação seja reproduzível.
- **FR-013**: Deve existir uma verificação de estilo PEP 8 executável por comando documentado.
- **FR-014**: O backend MUST permitir requisições de navegador vindas das origens configuradas para o frontend separado e MUST recusar as demais.
- **FR-015**: O README MUST documentar a versão de Python exigida, a instalação das dependências, as variáveis de ambiente, a verificação de conexão, a aplicação das alterações de estrutura, a execução do backend, dos testes e da verificação de estilo.
- **FR-016**: O backend MUST oferecer um ponto de verificação de funcionamento simples, que confirme que a aplicação está em execução.
- **FR-017**: Esta feature MUST NOT incluir hospedagem, deploy, backup, monitoramento ou integração contínua de implantação, pois o sistema roda apenas localmente.

### Key Entities *(include if feature involves data)*

Esta feature não introduz entidades de negócio. As entidades (unidade, categoria, atividade, programação e público-alvo) são definidas nas features seguintes; aqui apenas é preparada a estrutura onde elas residirão.

- **Configuração de ambiente**: conjunto de valores externos ao código (conexão com o banco, chave secreta, modo de depuração, hosts e origens permitidas) que define como o backend roda em cada máquina.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa nova na equipe consegue colocar o backend em execução, seguindo apenas o README, em até 30 minutos.
- **SC-002**: 100% das variáveis de ambiente necessárias estão listadas no arquivo de exemplo e no README, e nenhum valor sensível aparece no repositório.
- **SC-003**: A suíte de testes completa roda em menos de 1 minuto em uma máquina de desenvolvimento comum, sem qualquer conexão com banco de dados.
- **SC-004**: Qualquer alteração com cobertura total inferior a 90% é rejeitada pela verificação de cobertura em 100% dos casos.
- **SC-005**: Uma configuração incorreta ou ausente é identificada na inicialização em menos de 10 segundos, com mensagem que indica o que corrigir.
- **SC-006**: A conexão com o banco é confirmada ou recusada, com o motivo, em menos de 15 segundos.
- **SC-007**: A verificação de estilo termina sem erros no código entregue por esta feature.

## Assumptions

- A feature é de fundação: não há usuário final nem funcionalidade pública, e o público são as pessoas da equipe.
- Seguem a constituição v1.1.0: execução somente local, PostgreSQL no AWS RDS sem Docker, testes unitários com mocks e sem banco, cobertura mínima de 90% e frontend em repositório separado.
- A instância do AWS RDS e as credenciais já existem ou serão criadas pela equipe fora desta feature, e a máquina de cada pessoa tem acesso de rede autorizado a ela.
- Python 3.14 é a versão exigida. A compatibilidade das bibliotecas com ela será verificada ao fixar as versões, e isso pode levar a ajustes na fase de planejamento.
- Os módulos de domínio são criados vazios, sem modelos de negócio, que ficam para as features seguintes (cadastros de apoio, atividades e programações).
- Conforme a US-031 do backlog, o ambiente de testes não usa dados reais.
- Autenticação e Django Admin ficam para a feature 2; esta feature só prepara a base.
- Referências: `docs/01-visao-do-produto-e-requisitos.md`, `docs/02-arquitetura-do-sistema.md`, `docs/08-estrategia-infraestrutura-deploy.md` (seções 4 a 7) e `docs/04-backlog-do-produto.md` (US-001, 002, 003 e 031).
