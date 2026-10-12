# Contrato: público-alvo no Django Admin

Interface: cadastro de **Público-alvo** e lista de **Atividades** no Django Admin (sem rota ou tela nova).
Quem pode: os mesmos usuários e permissões que já valem para esses cadastros.

## 1. Cadastro de Público-alvo

| Campo | Rótulo | Observações |
|-------|--------|-------------|
| `includes_everyone` | Abrange todos os públicos | Caixa de seleção, desmarcada por padrão. |

Texto de ajuda: “Marque se esta opção vale para todos os públicos (por exemplo, ‘Todas as idades’). Quem
filtra por qualquer outro público também vê as atividades desta opção.”

- A lista de públicos mostra uma coluna com a marca e oferece o filtro lateral “Abrange todos os públicos”,
  ao lado do filtro de “Ativo” já existente.
- Alterar a marca vale imediatamente para o filtro da consulta pública; nenhum vínculo é alterado.
- Pode haver mais de um público marcado; nada impede, e todos são tratados da mesma forma.
- Desativar um público marcado não retira a marca: os vínculos existentes continuam valendo para a regra
  inclusiva (o público só deixa de poder ser escolhido no filtro).

## 2. Carga inicial (`seed_catalog`)

| Situação | Efeito |
|----------|--------|
| Públicos ainda não existem | “Todas as idades” é criada já marcada |
| “Todas as idades” já existe sem a marca | a marca é aplicada; nome e descrição não mudam |
| Outro público já foi marcado pelo administrador | a marca é mantida; nada é desmarcado |
| Comando executado de novo | nenhum registro novo, nenhuma mudança |

## 3. Filtro “Público-alvo” na lista de Atividades

Novo filtro no painel lateral da lista de atividades, ao lado de “Situação”, “Unidade” e “Categoria”.

- **Opções:** os públicos-alvo ativos **e** os inativos que ainda tenham atividades vinculadas, ordenados por
  nome; mais “Todos”.
- **Resultado:** as atividades vinculadas ao público escolhido, cada uma uma única vez (a atividade só se
  liga uma vez a cada público).
- Funciona em conjunto com os outros filtros e com a busca da lista, e não altera permissões nem as ações em
  lote existentes (publicar, cancelar e encerrar selecionadas).
- No Admin, o filtro mostra a situação real das atividades (rascunho, cancelada, encerrada também), pois quem
  usa a área administrativa vê tudo; a regra de “abrange todos” **não** se aplica ali, já que o filtro serve
  para localizar as atividades vinculadas ao público.
