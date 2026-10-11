# Contrato: comandos de gerenciamento

## `seed_catalog` (estendido)

```bash
python manage.py seed_catalog
```

Carrega, de forma idempotente por `slug`, a unidade e as categorias da feature 003 e, agora, as
opções iniciais de público-alvo:

| slug | Nome |
|---|---|
| `criancas` | Crianças |
| `adolescentes` | Adolescentes |
| `adultos` | Adultos |
| `pessoas-idosas` | Pessoas idosas |
| `todas-as-idades` | Todas as idades |

- Registros que já existem não são alterados.
- Saída: uma linha por tipo, no formato `Públicos-alvo: N criada(s), M já existiam.`
- Segunda execução seguida: nenhum registro criado.
- A lista é provisória e pode ser mantida depois pelo Admin.
