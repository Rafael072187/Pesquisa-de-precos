# Pesquisa De Precos

🛒 Web Scraper de Ofertas com Selenium + Bing + Buscapé

Automação para comparar preços de produtos em dois grandes sites (Buscapé e Bing Shopping), filtrar pelas suas regras e te enviar as melhores ofertas por e-mail.

----------------------------------------------------------------------------------------------------------------

🚀 O que esse projeto faz

Lê uma planilha com produtos e regras de busca.

Acessa Buscapé e Bing Compras com Selenium + Brave.

Busca ofertas válidas (sem termos banidos, com termos obrigatórios e dentro do preço).

Gera uma planilha .xlsx com as ofertas encontradas.

Envia um e-mail com a planilha e a tabela HTML embutida.

----------------------------------------------------------------------------------------------------------------

📁 Estrutura esperada da planilha buscas.xlsx

| Nome          | Termos banidos       | Preço mínimo | Preço máximo |
| ------------- | -------------------- | ------------ | ------------ |
| notebook dell | usado recondicionado | 2500         | 4000         |
| iphone 12     | falso réplica        | 3000         | 5000         |

----------------------------------------------------------------------------------------------------------------

🧰 Requisitos

Python 3.x

selenium, pandas, webdriver_manager, openpyxl, pywin32

Navegador Brave instalado

pip install selenium pandas webdriver-manager openpyxl pywin32

----------------------------------------------------------------------------------------------------------------

🧠 Como funciona

Lê os dados da planilha buscas.xlsx

Para cada produto:

Abre o Bing e o Buscapé

Coleta ofertas (nome, preço, link)

Filtra:

Preço entre o mínimo e o máximo

Nome sem palavras banidas

Nome com todos os termos obrigatórios

Junta tudo em um DataFrame

Salva em tabela_ofertas.xlsx

Envia um e-mail com:

Planilha anexa

Tabela HTML das ofertas no corpo

----------------------------------------------------------------------------------------------------------------

💡 Exemplos de filtros aplicados

Produto: "notebook dell"

Termos banidos: "usado recondicionado"

Será ignorado qualquer resultado que:

Fale "usado"

Não mencione "notebook" e "dell"

----------------------------------------------------------------------------------------------------------------

📬 Envio de e-mail (Outlook)

Usa o Outlook instalado (COM):

outlook = win32.Dispatch('outlook.application')

mail = outlook.CreateItem(0)

mail.To = 'seu@email.com'

mail.Subject = 'Tabela de Ofertas'

mail.HTMLBody = tabela_ofertas.to_html(index=False)

----------------------------------------------------------------------------------------------------------------

⚠️ O Outlook precisa estar instalado e configurado.

⚠️ Observações

Sites de busca podem mudar a estrutura. Se o script quebrar, provavelmente trocaram uma class name.

Brave é usado como navegador, mas você pode trocar para Chrome se quiser.

O código fecha automaticamente abas antigas e cuida dos cookies do Bing.

Evite abusar: scraping em excesso pode gerar bloqueios.


