# Contrato: comandos de gerenciamento

## `seed_catalog`

Carrega a unidade e as categorias iniciais.

- **Entrada**: nenhuma opção.
- **Ação**: para cada item abaixo, cria o registro se não existir um com o mesmo slug. Registros
  existentes não são alterados, nem reativados.
- **Saída**: resumo com quantos registros foram criados e quantos já existiam. Código 0.
- **Pré-requisito**: migrations aplicadas (`safe_migrate`).
- **Idempotência**: rodar de novo não duplica nem sobrescreve edições feitas pelo Admin.

### Unidade

| Nome | Slug | Bairro |
|---|---|---|
| CEU Navegantes | `ceu-navegantes` | Navegantes (a confirmar, ver research R7) |

### Categorias

| Nome | Slug |
|---|---|
| Cultura e Artes | `cultura-e-artes` |
| Cursos e Formação | `cursos-e-formacao` |
| Esporte e Atividade Física | `esporte-e-atividade-fisica` |
| Lazer e Recreação | `lazer-e-recreacao` |
| Saúde e Bem-estar | `saude-e-bem-estar` |
| Educação e Meio Ambiente | `educacao-e-meio-ambiente` |
| Eventos e Encontros | `eventos-e-encontros` |
| Participação Comunitária | `participacao-comunitaria` |

As descrições vêm do documento de visão (seção 9) e podem ser editadas pelo Admin depois da carga.
