# Acessibilidade: o que o backend entrega e o que cabe ao frontend

Meta proposta (DOC-06, RNF-ACC-05): **WCAG 2.2 nível AA** na interface pública, verificada com
ferramentas automáticas e revisão manual. A meta e o método serão confirmados antes da validação
final do produto.

## O backend entrega (verificado por teste)

| Necessidade (US-028) | Garantia da API |
|---|---|
| Texto legível, sem depender de cor ou código | Unidade, categoria, públicos-alvo e dias da semana vêm com `name`/`weekday_names` em português. |
| Datas e horários inequívocos | Datas em `AAAA-MM-DD`; horários em `HH:MM`; fuso `America/Sao_Paulo`. |
| Campos opcionais sem ruído | Campos vazios opcionais vêm como `null` (por exemplo, `address`, `description`, `external_registration_url`), não como texto vazio. |
| Estrutura previsível | Listas paginadas com o mesmo formato; campos sempre presentes. |
| Erros associáveis aos campos | `errors` mapeia nome do parâmetro → mensagens; o frontend liga cada mensagem ao campo (`aria-describedby`/`aria-invalid`). |
| Mensagens compreensíveis | Português, dizem o que corrigir, sem códigos internos (ver [error-format.md](error-format.md)). |
| Sem texto alternativo a fornecer | Imagens fora da primeira versão; se entrarem, a spec correspondente deve incluir descrição alternativa obrigatória. |

## Cabe ao frontend (repositório separado)

- Rótulos associados a todos os campos de formulário e filtros.
- Navegação e uso completos por teclado, foco visível, ordem coerente.
- Hierarquia de títulos e estrutura semântica (landmarks, listas, botões e links com nome).
- Contraste mínimo de texto e controles; informação nunca só por cor.
- Responsividade (celular e desktop) e alvos de toque.
- Anunciar erros de validação para leitores de tela.
- Executar a verificação automática e a revisão manual, registrando e priorizando os problemas.

## Como o backend ajuda a verificar

Os exemplos reais de resposta e de erro estão em [quickstart.md](../quickstart.md) e nos contratos da
feature 006 (`specs/006-public-consultation/contracts/public-api.md`).
