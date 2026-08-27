# Pendência Externa — Acesso às Contas de Transferências Especiais na API BB

**Data do diagnóstico:** 27/08/2026  
**Projeto:** transferegov_pmmg  
**Módulo:** Integração Banco do Brasil — Investimentos

## 1. Contexto

Durante o desenvolvimento da V5 do projeto, foi implementada a integração com a API de investimentos do Banco do Brasil para consulta dos saldos aplicados das contas bancárias vinculadas às Transferências Especiais da PMMG.

A comunicação técnica com a API foi validada com sucesso.

## 2. Validação da integração

Foram validados:

- autenticação OAuth2;
- comunicação com mTLS;
- certificado e chave privada;
- credenciais da aplicação;
- endpoint de consulta de fundos;
- envio de agência e conta;
- processamento da resposta JSON;
- leitura de `listaFundosInvestimento`;
- leitura dos saldos bruto e líquido.

Como teste de controle, a conta:

`Agência 1615 / Conta 23416`

foi consultada com sucesso pela nova implementação.

A API retornou normalmente informações do fundo de investimento e seus respectivos saldos.

Portanto, não há evidência de falha na implementação técnica da integração.

## 3. Contas identificadas pelo Transferegov

A extração automática do Transferegov identificou:

**54 contas bancárias únicas**

associadas às Transferências Especiais da PMMG existentes na base analisada.

As contas foram consolidadas pelo módulo de descoberta de contas BB.

## 4. Comparação com o cadastro histórico

O sistema anteriormente utilizado para consulta de investimentos BB possui um cadastro histórico contendo:

**65 contas bancárias**

Foi realizado o cruzamento entre:

- 54 contas descobertas automaticamente no Transferegov;
- 65 contas existentes no cadastro histórico BB.

Resultado:

| Situação | Quantidade |
|---|---:|
| Contas Transferegov | 54 |
| Contas cadastro BB antigo | 65 |
| Presentes nas duas bases | 0 |
| Somente Transferegov | 54 |
| Somente cadastro antigo | 65 |

Não foi encontrada nenhuma conta em comum entre os dois conjuntos.

## 5. Teste das contas do Transferegov na API BB

As 54 contas identificadas pelo Transferegov foram submetidas individualmente à API de investimentos BB.

Resultado:

| Resultado | Quantidade |
|---|---:|
| Contas testadas | 54 |
| Sucesso | 0 |
| Erro | 54 |
| Código BB | 107 |

Todas retornaram o código:

`107`

Mensagem apresentada pela API:

> Código do cliente não compatível com agência e conta.

## 6. Conclusão técnica

A integração com a API BB está funcional.

O teste com conta previamente autorizada confirmou o funcionamento da autenticação, mTLS, endpoint e processamento da resposta.

Entretanto, as 54 contas provenientes das Transferências Especiais não estão acessíveis com o código de cliente/aplicação atualmente utilizado.

A evidência disponível indica uma dependência externa relacionada ao vínculo/autorização dessas contas perante a aplicação utilizada na API BB.

## 7. Pendência externa

Deverá ser verificado junto à gestão responsável pelas contas do Banco do Brasil se as contas das Transferências Especiais estão cadastradas/vinculadas à aplicação utilizada para acesso à API.

Essa verificação não depende de alteração no código do projeto neste momento.

## 8. Evidências locais

Foram produzidos os seguintes arquivos de diagnóstico:

- `dados/bb/contas.json`
- `dados/bb/cruzamento_contas_bb.json`
- `dados/bb/teste_contas_bb.json`

Esses arquivos permanecem fora do versionamento por pertencerem à camada de dados operacionais do projeto.

## 9. Próxima ação

Após a verificação e eventual regularização do acesso às contas junto ao Banco do Brasil:

1. repetir o teste automatizado das 54 contas;
2. confirmar retorno HTTP válido;
3. validar `listaFundosInvestimento`;
4. integrar os saldos de investimento à camada financeira da V5;
5. implementar armazenamento histórico dos saldos;
6. posteriormente calcular variações entre snapshots, observando que variação de saldo não representa necessariamente rendimento quando houver aportes ou resgates.

## 10. Status

**PENDENTE — DEPENDÊNCIA EXTERNA**

A evolução das demais funcionalidades da V5 pode continuar independentemente desta pendência.
