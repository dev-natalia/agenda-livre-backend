# Research: Gestão de Programações

Não havia itens "NEEDS CLARIFICATION" no Technical Context. As decisões abaixo resolvem as escolhas de
desenho que a spec deixou para o plano.

## 1. Dias da semana como campo do formulário

- **Decision**: `ScheduleWeekday` existe como tabela (conforme `docs/03-modelo-de-dados.md`), mas no
  Admin os dias são um campo de múltipla escolha com checkboxes (`ScheduleAdminForm.weekdays`). Em
  `ScheduleAdmin.save_related()` o conjunto escolhido é comparado com as linhas existentes: criam-se as
  que faltam e removem-se as que sobraram.
- **Rationale**: o Admin não aceita inline dentro de inline; um inline de dias na programação
  funcionaria, mas permitiria repetir dias e exigiria várias linhas. Os checkboxes tornam o
  duplicado impossível na interface e deixam a validação "recorrente exige ao menos um dia" simples.
- **Alternatives considered**: `TabularInline` de dias (duplicidade possível, mais cliques); campo
  `ArrayField` no PostgreSQL (foge do modelo do DOC-03 e da regra de unicidade por par).

## 2. Onde ficam as regras

- **Decision**: regras de uma linha ficam no modelo — `clean()` e `CheckConstraint` (`start_date <=
  end_date`, `start_time < end_time`, pontual com datas iguais). Regras que envolvem os dias
  (recorrente ≥ 1 dia; pontual sem dias) ficam em `ScheduleAdminForm.clean()`, como o DOC-03 prevê.
  Unicidade de (`schedule`, `weekday`) é `UniqueConstraint`.
- **Rationale**: o banco é a última barreira para os dados de uma linha; as regras entre tabelas só
  podem ser verificadas onde os dias são conhecidos.
- **Alternatives considered**: validar tudo só no formulário (dados incorretos entrariam por outro
  caminho, como um shell ou futura API).

## 3. Programação pontual com data final diferente

- **Decision**: recusar com mensagem no campo "data final". Não corrigir automaticamente.
- **Rationale**: a spec pede recusa (FR-005); corrigir em silêncio esconderia o erro de digitação.
- **Alternatives considered**: ocultar a data final para pontual e copiá-la da inicial. Exigiria
  JavaScript no Admin, o que foge da simplicidade (Princípio V).

## 4. Cálculo de ocorrências

- **Decision**: `iter_occurrences(schedule, weekdays, from_date)` gera, em ordem, uma ocorrência por
  data dentro do período e dos dias da semana, a partir de `from_date`. `upcoming_occurrences(activity,
  now=None, limit=10)` junta as programações da atividade, descarta as ocorrências já terminadas em
  `now` (data e `end_time` no fuso configurado), ordena por data e horário de início e corta em
  `limit`. `date.isoweekday()` já coincide com a convenção 1 a 7 do DOC-03.
- **Rationale**: nenhuma linha por ocorrência (FR-007); função pura sobre dados e relógio injetado
  permite teste sem banco e sem depender do relógio real; a iteração é limitada pelo fim do período.
- **Alternatives considered**: expandir recorrências com `dateutil.rrule` (dependência nova, sem
  ganho para dias da semana simples); pré-gerar tabela de ocorrências (contraria o DOC-03).

## 5. Fuso horário e "agora"

- **Decision**: `now` recebe `timezone.now()` por padrão e é convertido com `timezone.localtime()` para
  `America/Sao_Paulo` (já configurado, `USE_TZ=True`). Datas e horários da programação são
  armazenados como `DateField` e `TimeField` sem fuso e interpretados como horário local.
- **Rationale**: o produto atende uma unidade com fuso único; guardar o horário local evita deslocar o
  horário da atividade em mudanças de horário de verão.
- **Alternatives considered**: `DateTimeField` por ocorrência (exige expansão e fuso por registro).

## 6. Situação da atividade no cálculo

- **Decision**: `upcoming_occurrences` devolve lista vazia se `activity.status` não estiver em
  `PUBLIC_STATUSES` (somente `PUBLISHED`). A administração vê as programações de qualquer atividade;
  só o bloco "próximas ocorrências" respeita a situação, com texto explicando o motivo quando vazio.
- **Rationale**: FR-012 e Constituição IV; a regra fica no serviço, pronto para a API pública.
- **Alternatives considered**: calcular sempre e deixar a API filtrar (risco de esquecer o filtro).

## 7. Programações dentro da página da atividade

- **Decision**: `ActivityAdmin` ganha um inline tabular somente leitura (tipo, período, horário, dias)
  com `show_change_link`, sem adicionar/excluir, e um campo somente leitura "próximas ocorrências" com
  link "Adicionar programação" que abre o formulário da programação com a atividade preenchida (`?
  activity=<id>`). A edição acontece no formulário da programação.
- **Rationale**: atende FR-015 e FR-016 sem inline aninhado (ver item 1).
- **Alternatives considered**: inline editável com os dias como inline próprio (não suportado).

## 8. Exclusão

- **Decision**: `Schedule.activity` usa `PROTECT`; `ScheduleWeekday.schedule` usa `CASCADE`. Excluir
  programação (permitido ao Administrador) remove seus dias e mantém a atividade. Excluir atividade com
  programações é recusado pelo Admin (página de objetos protegidos), mantendo a regra da feature 004.
- **Rationale**: FR-013; nenhuma perda silenciosa de programações.
- **Alternatives considered**: `CASCADE` na atividade (apagaria o histórico ao excluir rascunho).

## 9. Autoria

- **Decision**: `ScheduleAdmin.save_model()` preenche `created_by` na criação e `updated_by` sempre, como em
  `ActivityAdmin`. O Admin chama `save_model` a cada envio do formulário, então alterar apenas os dias
  da semana também atualiza `updated_by` e `updated_at`.
- **Rationale**: FR-010 e SC-003; mudar dias é mudar a programação.
- **Alternatives considered**: não registrar mudança só nos dias (violaria SC-003).
