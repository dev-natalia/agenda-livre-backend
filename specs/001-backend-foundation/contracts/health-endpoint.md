# Contrato: verificação de funcionamento

## `GET /api/v1/health/`

Confirma que a aplicação está em execução. **Não** consulta o banco de dados.

- **Autenticação**: não exigida.
- **Parâmetros**: nenhum.

### Resposta de sucesso

`200 OK`, `Content-Type: application/json`

```json
{
  "status": "ok"
}
```

### Outros métodos

Qualquer método diferente de `GET` retorna `405 Method Not Allowed`.

### CORS

A resposta inclui os cabeçalhos de CORS apenas para requisições vindas de origens listadas em
`CORS_ALLOWED_ORIGINS`. Para outras origens, o navegador bloqueia o acesso à resposta.
