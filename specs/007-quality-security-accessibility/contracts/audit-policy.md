# Política de auditoria de conteúdo

Aplica-se a **atividades** e **programações** (US-030, RNF-PRIV-02). Fecha as pendências "contas
removidas" e "operações automatizadas" de `docs/PENDENCIAS.md`.

## O que é registrado

Quem criou, quem atualizou por último, quando criou e quando atualizou. Não há histórico de versões:
guarda-se apenas o último atualizador.

## Quem é o autor

Sempre uma conta administradora autenticada, preenchida pelo sistema a partir da requisição. O campo
nunca é digitado nem editável na administração.

## Contas removidas

- Uma conta que é autora de qualquer atividade ou programação **não pode ser removida** (o banco
  recusa, `PROTECT`).
- Quando uma pessoa deixa a equipe, a conta é **desativada**; o histórico de autoria permanece.
- Contas sem autoria podem ser removidas normalmente.

## Operações automatizadas

- Hoje **não existe** rotina que crie ou altere atividades ou programações sem uma pessoa autenticada
  (inclusive a mudança de situação, que é ação manual na administração).
- Uma rotina futura só pode alterar esses registros se receber um usuário-ator explícito (por exemplo,
  uma conta de serviço dedicada) e se esta política for atualizada antes.

## Exposição

Os campos de autoria e de horários **nunca** aparecem em respostas públicas. Na administração
aparecem somente para leitura.

## Fora do escopo

Auditoria de unidades, categorias e públicos-alvo; histórico de alterações campo a campo.
