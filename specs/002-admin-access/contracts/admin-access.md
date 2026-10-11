# Contrato: acesso administrativo

Rotas HTTP expostas por esta feature. Não há endpoints JSON novos.

| Rota | Quem acessa | Comportamento |
|---|---|---|
| `GET /admin/login/` | Qualquer pessoa | Formulário de entrada |
| `POST /admin/login/` | Qualquer pessoa | Credenciais válidas de conta ativa e `is_staff`: redireciona ao painel. Inválidas ou conta inativa: volta ao formulário com mensagem genérica |
| `GET /admin/` e qualquer `/admin/...` | Conta autenticada | Painel (só os cadastros permitidos) |
| `GET /admin/...` | Não autenticado | Redireciona (302) para `/admin/login/?next=...`, sem conteúdo administrativo |
| `POST /admin/logout/` | Autenticada | Encerra a sessão |
| `/admin/<app>/<modelo>/...` | Autenticada sem a permissão | 403, sem alterar nada |

## Regras

- Conta autenticada sem `is_staff` não entra no painel.
- Cada operação (ver, criar, alterar, excluir) verifica a permissão do modelo no servidor.
- Mensagens de login não revelam se o usuário existe nem se a senha está errada.
- O CSRF é obrigatório nos formulários do painel.
- Rotas públicas (`/api/v1/...`) não exigem login, e esta feature não as altera.
- Não há bloqueio por tentativas repetidas nem fluxo de "esqueci a senha".
