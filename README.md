# 🍔 DevJuan Lanches

<p align="center">
  Sistema web completo para gerenciamento de uma lanchonete, desenvolvido com Python, Flask, SQLite, HTML, CSS e JavaScript.
</p>

<p align="center">
  <a href="#-sobre-o-projeto">Sobre</a> •
  <a href="#-funcionalidades">Funcionalidades</a> •
  <a href="#-tecnologias">Tecnologias</a> •
  <a href="#-estrutura-do-projeto">Estrutura</a> •
  <a href="#-instalação">Instalação</a> •
  <a href="#-aprendizados">Aprendizados</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

---

## 📌 Sobre o projeto

O **DevJuan Lanches** é uma aplicação web desenvolvida para simular o funcionamento de uma lanchonete digital.

O sistema permite que clientes criem uma conta, façam login, naveguem pelo cardápio, adicionem produtos ao carrinho, realizem pedidos e acompanhem seus pedidos.

Além da área do cliente, o projeto possui um **painel administrativo**, permitindo o gerenciamento do cardápio, estoque e pedidos.

O projeto foi desenvolvido com foco em aprendizado prático de desenvolvimento web, integração entre front-end e back-end, banco de dados e criação de funcionalidades de um sistema real.

---

## 🎯 Objetivos

O principal objetivo do projeto é colocar em prática conceitos de desenvolvimento de software através da construção de uma aplicação completa.

Durante o desenvolvimento foram trabalhados conceitos como:

- Desenvolvimento web com Python
- Criação de aplicações utilizando Flask
- Integração com banco de dados SQLite
- Operações CRUD
- Autenticação de usuários
- Controle de sessões
- Manipulação de formulários
- Manipulação de arquivos e imagens
- Controle de estoque
- Sistema de pedidos
- Integração entre front-end e back-end
- Organização de projetos
- Versionamento utilizando Git e GitHub

---

# 🚀 Funcionalidades

## 👤 Área do cliente

### Cadastro

O cliente pode criar uma conta informando seus dados e definir uma senha para acessar o sistema.

### 🔐 Login

Sistema de autenticação para clientes e administradores.

O sistema identifica automaticamente o tipo de usuário e direciona cada um para sua respectiva área.

### 🍔 Cardápio

Exibição dos produtos disponíveis, incluindo:

- Nome
- Preço
- Imagem
- Descrição
- Disponibilidade em estoque

### 🛒 Carrinho

O cliente pode:

- Adicionar produtos
- Aumentar quantidade
- Diminuir quantidade
- Remover produtos
- Visualizar subtotal
- Visualizar valor total

### 💳 Pagamento

O sistema permite selecionar uma forma de pagamento para o pedido.

> O pagamento é simulado, pois o projeto não utiliza um gateway financeiro real.

### 🚚 Entrega

O sistema permite trabalhar com informações relacionadas à entrega e endereço do cliente.

### 📦 Pedidos

Após finalizar um pedido, o cliente pode visualizar seus pedidos e acompanhar o status.

### 📋 Histórico

Área destinada à visualização dos pedidos realizados pelo cliente.

---

# 🔑 Área administrativa

O sistema possui um painel exclusivo para administração da lanchonete.

## 📊 Dashboard

O administrador pode visualizar informações como:

- Total de clientes
- Total de pedidos
- Faturamento
- Estoque total
- Produtos disponíveis
- Produtos esgotados
- Pedidos entregues
- Pedidos cancelados

---

## 🍔 Gerenciamento de produtos

O administrador pode:

- Adicionar produtos
- Editar produtos
- Excluir produtos
- Alterar preços
- Alterar descrições
- Adicionar imagens
- Controlar estoque

---

## 📦 Controle de estoque

O estoque dos produtos pode ser atualizado diretamente pelo painel administrativo.

O sistema também verifica a disponibilidade dos produtos antes da realização do pedido.

---

## 📝 Gerenciamento de pedidos

O administrador pode visualizar os pedidos realizados pelos clientes e atualizar seus respectivos status.

### Status disponíveis

```text
Em processamento
        ↓
      Pago
        ↓
 Em preparação
        ↓
     Pronto
        ↓
   Entregue
