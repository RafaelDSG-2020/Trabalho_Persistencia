# Proposta de Trabalho Prático de Desenv. de Software para Persistência - 2024.2
## Tema do Projeto
Sistema de Gerenciamento de Eventos Acadêmicos

## Descrição do Sistema
O sistema será uma API REST que permite o gerenciamento de eventos acadêmicos, como conferências, workshops e simpósios. A API facilitará a administração desses eventos, permitindo o cadastro de eventos, a inscrição de participantes e o gerenciamento de palestrantes.

## Principais Requisitos de Persistência
A API deve fornecer suporte para as seguintes operações de persistência:

__CRUD para cada entidade principal:__ criação, leitura, atualização e exclusão de registros para cada uma das entidades descritas.

__Relações entre entidades:__ como a inscrição de participantes em eventos e a associação de palestrantes a um evento.

__Consultas e filtros específicos:__ como listagem de eventos futuros, filtragem de eventos por categoria e verificação de disponibilidade de inscrição.

## Entidades Principais
__Evento:__ Representa um evento acadêmico específico, como uma conferência ou workshop. Cada evento possui detalhes como título, data, local e capacidade máxima de participantes.

__Participante:__ representa as pessoas interessadas em se inscrever nos eventos. Cada participante possui dados como nome, e-mail e status de inscrição para os eventos.

__Palestrante:__ representa os especialistas convidados para os eventos. Cada palestrante possui informações como nome, biografia e especialidade, além dos eventos nos quais irá participar.


## Motivações
O tema foi escolhido por ser um caso de uso frequente em ambientes acadêmicos e por sua relevância prática, visto que permite aplicar conceitos de persistência de dados em um contexto realista. Além disso, a estrutura dos dados e a relação entre as entidades possibilitam explorar diferentes técnicas de consulta e manipulação de dados.