# Contrato: envio de imagem pelo Django Admin

Interface: formulário de **Atividade** no Django Admin (sem rota ou tela nova). Quem pode: usuários com a
permissão de alterar atividades (a mesma que já vale para editar a atividade). Trocar, remover ou enviar
sem essa permissão é negado pelo Admin.

## Campos no formulário

| Campo | Rótulo | Observações |
|-------|--------|-------------|
| `image` | Imagem | Opcional. Mostra a imagem atual e a caixa "Limpar" para removê-la. Há pré-visualização da imagem atual. |
| `image_alt` | Texto alternativo da imagem | Até 200 caracteres. |
| `image_decorative` | Imagem decorativa | Caixa de seleção. |

## Regras e mensagens (todas em português)

| Situação | Resultado | Mensagem |
|----------|-----------|----------|
| Arquivo que não é JPEG, PNG nem WebP (inclui extensão trocada) | rejeita, erro em `image` | "Envie uma imagem JPEG, PNG ou WebP." |
| Arquivo corrompido ou ilegível | rejeita, erro em `image` | "Não foi possível ler a imagem. Envie outro arquivo." |
| Mais de 5 MB | rejeita, erro em `image` | "A imagem deve ter no máximo 5 MB." |
| Menos de 400×300 px | rejeita, erro em `image` | "A imagem deve ter pelo menos 400×300 pixels." |
| Mais de 6000×6000 px | rejeita, erro em `image` | "A imagem deve ter no máximo 6000×6000 pixels." |
| Imagem sem texto alternativo e sem marca de decorativa | rejeita, erro em `image_alt` | "Informe o texto alternativo da imagem ou marque-a como decorativa." |
| Texto alternativo preenchido **e** marcada como decorativa | rejeita, erro em `image_decorative` | "Informe o texto alternativo ou marque a imagem como decorativa, não os dois." |
| Texto alternativo com mais de 200 caracteres | rejeita, erro em `image_alt` | mensagem padrão do Django para o limite do campo |
| Armazenamento indisponível no envio | a atividade não é salva com referência a arquivo inexistente | "Não foi possível guardar a imagem agora. Tente novamente." (sem detalhes internos) |
| Atividade sem imagem | aceita; alt e marca ficam vazios | (nenhuma) |

Os limites de tamanho e de dimensões valem com os valores exatos (5 MB, 400×300, 6000×6000 aceitos; um
byte ou pixel além, rejeitado).

## Tratamento aplicado ao arquivo aceito

1. O formato é identificado pelo conteúdo do arquivo.
2. A orientação indicada nos metadados é aplicada à imagem.
3. O lado maior é reduzido a 1600 px, mantendo a proporção; imagens menores não são ampliadas.
4. A imagem é regravada no mesmo formato **sem nenhum metadado** (EXIF, localização, miniaturas embutidas).
5. O arquivo guardado recebe um nome aleatório (`activities/<uuid>.<ext>`); o nome enviado é ignorado.

## Efeitos ao salvar

| Ação da pessoa administradora | Efeito |
|-------------------------------|--------|
| Enviar imagem em atividade nova ou existente | guarda o arquivo tratado; o identificador da atividade não muda |
| Trocar a imagem | guarda o novo arquivo; o antigo é apagado após o salvamento |
| Marcar "Limpar" | remove a referência, zera alt e marca; o arquivo é apagado após o salvamento |
| Alterar só o texto alternativo ou a marca | atualiza o campo; o arquivo não é reprocessado nem trocado |
| Excluir a atividade (somente rascunho) | o arquivo é apagado após a exclusão |

Trocar, remover ou enviar a imagem atualiza `updated_by` e `updated_at` da atividade. Se a remoção do
arquivo antigo falhar, a operação conclui normalmente e o erro vai para o log local (`logs/agenda-livre.log`)
sem credenciais.

## Publicação

A imagem é opcional: uma atividade sem imagem pode ser salva e publicada. A publicação não exige imagem.
