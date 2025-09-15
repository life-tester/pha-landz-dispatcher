# Projeto PHA Landz Dispatcher

Este projeto automatiza os **dispatches do LandZ no Pixel Heroes Adventure (PHA)** selecionando automaticamente a melhor combinação de heroz para maximizar buffs e priorizar missões de grau mais alto.

---

## 📋 Visão Geral
- **Linguagem:** Python 3.9+
- **Objetivo:** Automatizar o envio de heroz para as contruções da LandZ no PHA.
- **Funcionalidades:**
  - Seleciona automaticamente os heroz para maximizar buffs e pontos totais.
  - Respeita o requisito de heroz-chave (grau ≥ grau do prédio).
  - Exibe um plano detalhado em modo simulação.
  - Pode executar os dispatches automaticamente com tentativas de repetição.
  - Pode reivindicar recompensas antes de planejar.

---

## ⚠️ Aviso Importante
Este script foi desenvolvido para **meus próprios ativos** e adaptado às minhas necessidades:

- Eu **não possuo Heroz Genesis**, então o suporte a Genesis ainda não foi implementado.
- A contratação de mercenários **ainda não foi implementada**.
- A lógica de dispatch para heroz míticos foi implementada, mas **ainda não foi testada**.
- Eu **nunca irei pedir o seu Bearer Token** ou entrar em contato primeiro.
- **Nada aqui é recomendação de compra ou venda de ativos** — é apenas uma automação para facilitar o dispatch de Heroz.
- Eu **não faço parte da equipe de desenvolvimento da PHA**, sou apenas uma jogadora.
- Este código deve ser executado **localmente** — nunca compartilhe seu Bearer Token com ninguém.
- Não me responsabilizo por qualquer perda de dados ou ativos. **Use por sua conta e risco.**
- Eu utilizo apenas Linux, então as instruções para Windows e macOS **não foram testadas**. Se algo não funcionar, me avise.

**Contato:**
- Discord: `life_tester`
- Email: `lifetester.dev@gmail.com`

**Agradecimentos e Doações:**
- Carteira Ronin: `0xD4Ec419216ABd8286005a4797fd1C183Bd9E6649`
- Carteira Ethereum: `0xB6CF6aF6C4D200835ffa7088a7Eef40110C7c953`

Aceito palavras de agradecimento, NFTs, $RON, $ETH, cafezinho ou qualquer outra forma de apoio ❤️

---

## 🛠️ Planos Futuros
Se o PHA continuar oferecendo a funcionalidade de dispatch no LandZ, pretendo:

- Melhorar a lógica de seleção de heroz para completar buffs.
- Implementar contratação de mercenários (Primal e Genesis).
- Adicionar suporte completo para heroz Genesis.

---

## 📸 Passo a Passo: Como Obter o Bearer Token
1. Abra o [Pixel Heroes Adventure DApp](https://dapp.pixelheroes.io/) no Chrome ou Firefox.
2. Faça login.
3. Abra as **Ferramentas de Desenvolvedor** (F12 ou clique com o botão direito → Inspecionar).
4. Vá até a aba **Rede**.
5. Recarregue a página.
6. Clique em qualquer requisição.
7. Vá para a aba **Headers**.
8. Localize o cabeçalho **Authorization** e copie o valor após `Bearer`.

### Exemplo de Bearer Token:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtZWdhdXNlciIsImlhdCI6MTY4ODc0MDAwMCwiZXhwIjoxNjg4NzQ2MDAwfQ.signatureexample
```

**Exemplo de Captura de Tela:**
![Exemplo de Bearer Token](docs/images/bearer-token-example.png)

---

## Rodando no Colab

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/life-tester/pha-landz-dispatcher-/blob/main/PHA-Landz-Dispatcher-pt-BR.ipynb)

---

## 📥 Instalação e Configuração

### Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/pha-landz-dispatch.git
cd pha-landz-dispatch
```

### Instalar Dependências
#### Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Windows (PowerShell)
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Verifique se o Python está instalado:
```bash
python --version
```
Se não estiver instalado, baixe em [python.org](https://www.python.org/downloads/).

---

## 🖥️ Comandos para Rodar
Linux/macOS:
```bash
python3 main.py --token <TOKEN>
```
Windows (PowerShell):
```powershell
py main.py --token <TOKEN>
```
Certifique-se de que o Python está no PATH.

---

## 📜 Argumentos de Linha de Comando
| Argumento | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `--token` | ✅ | — | Bearer token obtido na aba Rede do navegador |
| `--region` | ❌ | 1 | 1 = Meta Toy City, 2 = Ludo City |
| `--confirm` | ❌ | False | Executa os dispatches de fato |
| `--all` | ❌ | False | Faz dispatch de todas as missões em vez de apenas uma |
| `--max-dispatches` | ❌ | 999999 | Limite de segurança para número de dispatches |
| `--claim-first` | ❌ | False | Faz claim das recompensas antes de planejar |

---

## ▶️ Exemplo Completo
```bash
python main.py --token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... --region 2 --claim-first --confirm --all
```

Este comando:
- Usa a região **2** (Ludo City) para buscar as missões
- Faz claim das recompensas antes do planejamento
- Confirma e executa os dispatches
- Envia **todas as missões disponíveis**

⚠️ **Recomendação:** rode primeiro sem `--confirm` para apenas simular e ver o plano.  
Depois, use `--confirm` para executar de fato.

---

## 🔍 Exemplo de Saída
```
=== Dispatch Plan ===
01. - #3540 | Tavern | Grade=Épico | Base=250 | Buffs=1 x 30% [Epic+ Base Primal HeroZ x2 [...]] |
     Est.Total=325.0 | Chosen=[...] | Reserved=[—] | Dispatch garantido com heroz-chave (≥ Épico);
     completado 1 buff(s).
    Requisitos:
      - Epic+ Base Primal HeroZ x2: createType=2 grade=2(1) race=-1 star=-1 need=2
```

---

## 🧑‍💻 Contribuição
Sinta-se à vontade para abrir issues, enviar pull requests ou sugerir melhorias.  
Contato via Discord (`life_tester`) ou email (`lifetester.dev@gmail.com`).

---

## 📄 Licença
Licença MIT — livre para usar, modificar e compartilhar.
