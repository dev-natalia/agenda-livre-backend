# Research: Páginas Informativas (Sobre e Contato)

Resultado da leitura do código existente (features 001 a 008) contra os FR da spec. Não restou nenhum
`NEEDS CLARIFICATION`.

## Estado atual por requisito

| FR | Estado hoje | Ação |
|---|---|---|
| FR-001 | `config/urls.py` publica `admin/`, `api/v1/` (core e consultation) e o coringa `^api/`. Nenhuma rota de contato ou Sobre. | Teste que varre as rotas |
| FR-002 | O coringa `api_not_found` devolve 404 JSON, mas só chega à view se o `CsrfViewMiddleware` deixar. Sondagem com `Client(enforce_csrf_checks=True).post("/api/contato/")` devolveu **403 `text/html`**. O `Client` padrão do Django não impõe CSRF, por isso os testes atuais não viam o problema. | Isentar `api_not_found` de CSRF + teste com CSRF ativo |
| FR-002 (logs) | O arquivo de log tem nível mínimo ERROR (feature 008); 404 e 403 não entram. A view não lê o corpo. | Teste com `caplog` |
| FR-003 | Nenhum modelo nem `ModelAdmin` ligado a contato/Sobre; `makemigrations --check` limpo. | Teste que varre modelos e `admin.site._registry` |
| FR-004 | Não há guarda contra a volta dessas rotas/modelos. | Os mesmos testes servem de guarda |
| FR-005 | DOC-05 lista só os endpoints de consulta; não diz que Sobre e Contato não existem na API. | Nova subseção |
| FR-006 | README já diz (linhas ~221-222) que Sobre e Contato existem só no frontend. | Conferir/ajustar texto |
| FR-007 | DOC-04 já descreve US-035/US-036 como somente frontend; falta o histórico de revisão da feature. | Entrada no histórico |
| FR-008 | `docs/PENDENCIAS.md` cita o EP-09 como só frontend, sem item aberto. | Conferir |
| FR-009 | Padrão de testes unitários já existe (`tests/unit/core`). | Seguir o padrão |

## Decisões

### D1. Isentar `api_not_found` de CSRF
- **Decision**: aplicar `csrf_exempt` à view coringa.
- **Rationale**: a view não lê corpo, cookies nem sessão e não altera estado; a proteção CSRF existe para
  evitar ações indevidas e aqui não há ação. Sem a isenção, `POST`/`PUT`/`DELETE` a rotas inexistentes
  sob `/api/` vão receber 403 HTML, quebrando o contrato de erros JSON (constituição IV).
- **Alternatives**: criar um endpoint explícito de contato que responda 410/404 (contradiz a decisão de
  "sem endpoint"); remover o `CsrfViewMiddleware` (enfraquece o admin); middleware próprio para `/api/`
  (mais código para o mesmo efeito).

### D2. Guarda por teste, não por código de produção
- **Decision**: a proteção de escopo é um módulo de testes que inspeciona rotas, modelos e admin por
  palavras-chave (`contact`, `contato`, `about`, `sobre`, `message`).
- **Rationale**: nenhuma lógica nova em produção; o teste falha se alguém reintroduzir o recurso sem nova spec.
- **Alternatives**: linter/CI customizado (sem CI de deploy no escopo); checagem só por documentação
  (não é verificável).

### D3. Sem app, modelo ou endpoint de "conteúdo estático"
- **Decision**: nenhuma estrutura nova para servir o texto de Sobre.
- **Rationale**: a decisão de 2026-10-11 é texto fixo no frontend; servir pela API exigiria nova spec.
- **Alternatives**: endpoint `/api/v1/about/` ou cadastro no admin (fora do escopo, YAGNI).

### D4. Cuidado com falsos positivos nas palavras-chave
- **Decision**: o teste compara nomes de rotas/modelos como palavras inteiras em minúsculas e usa uma lista
  explícita de exceções vazia por padrão.
- **Rationale**: modelos como `LogEntry` do admin ou rotas existentes não podem ser confundidos; qualquer
  exceção futura precisa ser justificada no próprio teste.
